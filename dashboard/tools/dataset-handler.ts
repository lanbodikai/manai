import type { DatabaseSync } from "node:sqlite";
import { createRequire } from "node:module";
import { existsSync } from "node:fs";
import { collectionInfo } from "../src/dataset-fields.ts";
import type { Catalog, Collection, DatasetRecord } from "../src/api/dataset.ts";
import { buildDecisionTable, type FindingMeasure, type JobMeasure } from "./decision-summary.ts";
import { fixIds } from "../src/optimization-options.ts";

import type { IncomingMessage, ServerResponse } from "node:http";

type Row = {
  id: string;
  title: string;
  summary: string;
  synthetic: number;
  values_json: string;
  related_json: string;
};
export function datasetHandler(file: string) {
  let db: DatabaseSync | undefined;
  let catalog: Catalog;
  let decisionSource: { jobs: JobMeasure[]; findings: FindingMeasure[] } | undefined;
  const decode = (r: Row): DatasetRecord => ({
    id: r.id,
    title: r.title,
    summary: r.summary,
    synthetic: !!r.synthetic,
    values: JSON.parse(r.values_json),
    related: JSON.parse(r.related_json),
  });
  const { DatabaseSync } = createRequire(import.meta.url)("node:sqlite") as typeof import("node:sqlite");
  const handle = (req: IncomingMessage, res: ServerResponse) => {
    const send = (status: number, body: unknown) => {
      res.statusCode = status;
      res.setHeader("Content-Type", "application/json");
      res.setHeader("Cache-Control", "no-store");
      res.end(JSON.stringify(body));
    };
    const fail = (status: number, message: string) =>
      send(status, { error: { code: "LOCAL_DATASET_ERROR", message } });
    try {
      if (req.method !== "GET") return fail(405, "Read-only preview.");
      if (!db) {
        if (!existsSync(file))
          return fail(
            503,
            "The verified dataset snapshot is not prepared. Run dataset-prep and restart the dashboard.",
          );
        db = new DatabaseSync(file, { readOnly: true });
        const row = db
          .prepare("SELECT value FROM metadata WHERE key = ?")
          .get("catalog") as { value: string };
        catalog = JSON.parse(row.value);
      }
      const url = new URL(req.url ?? "/", "http://localhost");
      if (url.pathname === "/catalog") return send(200, catalog);
      if (url.searchParams.get("version") !== catalog.version)
        return fail(409, "Dataset version mismatch. Reload the explorer.");
      if (url.pathname === "/decisions") {
        if (!catalog.collections.find(c => c.key === "findings")?.available)
          return fail(503, "Generate and verify the official findings before opening cost optimization.");
        const selection = (url.searchParams.get("selection") ?? "").split(",").filter(Boolean);
        if (selection.some(id => !fixIds.includes(id)) || new Set(selection).size !== selection.length)
          return fail(422, "Unknown or repeated optimization selection.");
        if (!decisionSource) {
          decisionSource = {
            jobs: db.prepare(`SELECT id, outcome, json_extract(values_json,'$.gpu_hours') AS gpu_hours,
              json_extract(values_json,'$.sm_util_avg') AS sm_avg, json_extract(values_json,'$.sm_util_max') AS sm_max
              FROM records WHERE collection='jobs'`).all() as JobMeasure[],
            findings: db.prepare(`SELECT id, synthetic, json_extract(values_json,'$.rule') AS rule,
              json_extract(values_json,'$.id_job') AS job_id, json_extract(values_json,'$.impact_scope') AS scope
              FROM records WHERE collection='findings'`).all() as FindingMeasure[],
          };
        }
        return send(200, buildDecisionTable(decisionSource.jobs, decisionSource.findings, catalog.version, selection));
      }
      const [collectionRaw, idRaw, ...extra] = url.pathname
        .split("/")
        .filter(Boolean);
      if (!Object.hasOwn(collectionInfo, collectionRaw) || extra.length)
        return fail(404, "Dataset collection not found.");
      const collection = collectionRaw as Collection;
      if (
        catalog.collections.find((c) => c.key === collection)?.available ===
        false
      )
        return fail(
          503,
          "Official findings are not generated in this local preview. Jobs, GPUs and machines remain available.",
        );
      if (idRaw) {
        const id = decodeURIComponent(idRaw);
        const row = db
          .prepare("SELECT * FROM records WHERE collection = ? AND id = ?")
          .get(collection, id) as Row | undefined;
        if (!row) return fail(404, "Record not found.");
        const record = decode(row);
        const vals = record.values;
        const condition =
          collection === "jobs"
            ? "id_job = ?"
            : collection === "gpus"
              ? "node = ? AND gpu_id = ?"
              : "node = ?";
        const params =
          collection === "jobs"
            ? [id]
            : collection === "gpus"
              ? [String(vals.Node), Number(vals.gpu_id)]
              : [String(vals.Node)];
        if (collection !== "findings") {
          const activity = db
            .prepare(
              `SELECT values_json FROM activity WHERE ${condition} ORDER BY id_job LIMIT 100`,
            )
            .all(...params) as { values_json: string }[];
          record.activity = activity.map((r) => JSON.parse(r.values_json));
        }
        return send(200, {
          collection,
          version: catalog.version,
          record,
          caveats: catalog.caveats,
        });
      }
      const q = url.searchParams;
      const offset = Number(q.get("offset") ?? 0),
        limit = Number(q.get("limit") ?? 20),
        sort = q.get("sort") ?? collectionInfo[collection].fields[0].key;
      const direction = q.get("direction") ?? "asc";
      if (
        !Number.isSafeInteger(offset) ||
        offset < 0 ||
        !Number.isSafeInteger(limit) ||
        limit < 1 ||
        limit > 100 ||
        !["asc", "desc"].includes(direction) ||
        !collectionInfo[collection].fields.some((f) => f.key === sort)
      )
        return fail(422, "Invalid page or sort.");
      const query = q.get("query") ?? "";
      if (query.length > 200) return fail(422, "Search is too long.");
      const gpu = q.get("gpu");
      if (
        gpu &&
        (!q.get("node") ||
          !["0", "1"].includes(gpu) ||
          collection !== "jobs")
      )
        return fail(
          422,
          "Select a machine and GPU 0 or 1 in the Jobs view.",
        );
      const where = ["collection = ?"];
      const args: (string | number)[] = [collection];
      if (query) {
        where.push("search_text LIKE ? ESCAPE '\\'");
        args.push(`%${query.toLowerCase().replace(/[\\%_]/g, "\\$&")}%`);
      }
      if (q.get("outcome")) {
        where.push("outcome = ?");
        args.push(q.get("outcome")!);
      }
      if (q.get("node")) {
        where.push(
          collection === "jobs"
            ? `EXISTS (SELECT 1 FROM activity a WHERE a.id_job = records.id AND a.node = ?${gpu ? " AND a.gpu_id = ?" : ""})`
            : "node = ?",
        );
        args.push(q.get("node")!);
        if (gpu) args.push(Number(gpu));
      }
      const clause = where.join(" AND ");
      const { total } = db
        .prepare(`SELECT count(*) AS total FROM records WHERE ${clause}`)
        .get(...args) as { total: number };
      const jsonPath = `$.${sort}`;
      const rows = db
        .prepare(
          `SELECT * FROM records WHERE ${clause} ORDER BY json_extract(values_json, ?) IS NULL, json_extract(values_json, ?) ${direction.toUpperCase()}, id LIMIT ? OFFSET ?`,
        )
        .all(...args, jsonPath, jsonPath, limit, offset) as Row[];
      return send(200, {
        collection,
        version: catalog.version,
        synthetic: false,
        total,
        offset,
        limit,
        items: rows.map(decode),
        caveats: catalog.caveats,
      });
    } catch (error) {
      console.error(
        "Local dataset preview:",
        error instanceof Error ? error.message : "invalid request",
      );
      return fail(
        500,
        "The local dataset could not be read. Check preparation and restart the preview.",
      );
    }
  };
  return { handle, close: () => db?.close() };
}
