import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "../src/App";
import { createMockApi, initialAudit, type Fault } from "../src/mock/api";
import type { Runtime } from "../src/api/types";
import cpuAuditFixture from "../../contracts/examples/audit-response.json";
import { parse } from "../src/api/validation";

function runtime(fault: Fault = "none"): Runtime {
  window.history.replaceState(null, "", "/");
  return {
    api: createMockApi({ delay: 0, fault }),
    mode: "mock",
    initialScenario: initialAudit.scenario,
  };
}

async function navigate(hash: string) {
  await act(async () => {
    window.history.replaceState(null, "", hash);
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  });
}

describe("CFO journey", () => {
  it("preserves the source overview while unfinished recommendations are unavailable", async () => {
    const rt = runtime();
    rt.initialScenario = undefined;
    rt.api.listRecommendations = async () => {
      throw new Error("Bootstrap recommendations are not implemented.");
    };
    render(<App runtime={rt} />);
    expect(await screen.findByText("Where the money goes")).toBeVisible();
    expect(
      await screen.findByText(/Pilot recommendations are not available yet/),
    ).toBeVisible();
    expect(
      screen.queryByRole("heading", { name: "Source data unavailable" }),
    ).not.toBeInTheDocument();
  });
  it("shows mandatory labeling and opens the dollar-to-source path", async () => {
    render(<App runtime={runtime()} />);
    expect(
      screen.getByText("Synthetic demo — no live data or MCP"),
    ).toBeVisible();
    expect(screen.getByText("Loading the spending overview…")).toBeVisible();
    const recovery = await screen.findByRole("button", {
      name: "Inspect recovery value and evidence",
    });
    expect(recovery).toHaveTextContent("$15–$45");
    fireEvent.click(recovery);
    fireEvent.click(
      await screen.findByRole("button", { name: /Synthetic completed job J1/ }),
    );
    expect(await screen.findByText("Source and joins")).toBeVisible();
    expect(screen.getByText("Not source-data-derived.")).toBeVisible();
  });
  it("renders a v0.4 CPU pilot result separately from cohort recovery", async () => {
    const rt = runtime();
    rt.initialScenario = {
      ...initialAudit.scenario,
      cpu_pilot: {
        mode: "replacement_success",
        baseline_evidence_id: "job:J2",
        cpu_vcpus: 4,
        cpu_hours: 12,
        cpu_vcpu_hour_usd: 0.1,
        extra_queue_hours: 0,
        trial_cap_hours: null,
        baseline_host_costs_included: true,
        assumption_note: "Synthetic test scenario only.",
      },
    };
    // A declared fixture response exercises rendering; the demo adapter does
    // not pretend to calculate arbitrary CPU pilot inputs.
    rt.api.createAudit = async request => ({
      ...structuredClone(parse("Audit", cpuAuditFixture)),
      client_request_id: request.client_request_id,
      scenario: request.scenario,
    });
    render(<App runtime={rt} />);
    expect(await screen.findByRole("heading", { name: "CPU pilot scenario" })).toBeVisible();
    expect(screen.getByText("Scenario estimate · not verified")).toBeVisible();
    expect(screen.getByRole("button", { name: "Inspect selected job" })).toBeEnabled();
  });
  it("prepares the canonical audit without the removed scenario panel or sidebar tabs", async () => {
    const rt = runtime();
    rt.initialScenario = undefined;
    render(<App runtime={rt} />);
    const recovery = await screen.findByRole("button", {
      name: "Inspect recovery value and evidence",
    });
    expect(recovery).toHaveTextContent("$0–$75");
    expect(screen.queryByLabelText("Low recovery (%)")).not.toBeInTheDocument();
    expect(screen.queryByRole("link", {name:"Scenario"})).not.toBeInTheDocument();
    expect(screen.queryByRole("link", {name:"Evidence"})).not.toBeInTheDocument();
    await navigate("#ask");
    expect(screen.getByRole("heading", {name:"Ask about this pilot"})).toBeVisible();
    expect(screen.queryByRole("heading", {name:"GPU spending overview"})).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", {name:"Why this pilot?"}));
    expect(await screen.findByText(/Synthetic example: 30 eligible/)).toBeVisible();
  });
  it("allows a failed assistant audit to be retried without fake answers", async () => {
    const rt = runtime();
    const create = rt.api.createAudit;
    let attempts = 0;
    rt.api.createAudit = request => ++attempts === 1 ? Promise.reject(new Error("Audit unavailable")) : create(request);
    window.history.replaceState(null, "", "#ask");
    render(<App runtime={rt} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Audit unavailable");
    expect(screen.queryByRole("button", {name:"Why this pilot?"})).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", {name:"Retry connection"}));
    expect(await screen.findByRole("button", {name:"Why this pilot?"})).toBeEnabled();
  });
  it.each([
    "reviewer-unavailable",
    "reviewer-timeout",
    "reviewer-malformed",
  ] as const)(
    "keeps base chat and export available after %s",
    async (fault) => {
      render(<App runtime={runtime(fault)} />);
      await screen.findByRole("button", {
        name: "Inspect recovery value and evidence",
      });
      await navigate("#ask");
      fireEvent.click(screen.getByText("Open optional advanced reviewer"));
      fireEvent.change(screen.getByLabelText("Advanced review question"), {
        target: { value: "Why this pilot?" },
      });
      fireEvent.click(
        screen.getByRole("button", { name: "Ask advanced reviewer" }),
      );
      expect(await screen.findByRole("alert")).toBeVisible();
      fireEvent.click(
        screen.getByRole("button", { name: "What could go wrong?" }),
      );
      expect(
        await screen.findByText(/Synthetic example: 30 eligible/),
      ).toBeVisible();
      await navigate("#overview");
      expect(
        screen.getByRole("button", { name: "Download synthetic claims" }),
      ).toBeEnabled();
    },
  );
  it.each(["source-unavailable", "not-found"] as const)(
    "shows evidence failure %s without removing the audit",
    async (fault) => {
      render(<App runtime={runtime(fault)} />);
      fireEvent.click(
        await screen.findByRole("button", {
          name: "Inspect recovery value and evidence",
        }),
      );
      fireEvent.click(
        await screen.findByRole("button", {
          name: /Synthetic completed job J1/,
        }),
      );
      expect(await screen.findByRole("alert")).toHaveTextContent(
        fault === "not-found" ? "404" : "503",
      );
      fireEvent.click(screen.getByRole("button", { name: "Close evidence" }));
      expect(
        screen.getByRole("button", { name: "Download synthetic claims" }),
      ).toBeEnabled();
    },
  );
  it.each(["conflict", "invalid"] as const)(
    "shows %s creation errors without fabricating a result",
    async (fault) => {
      render(<App runtime={runtime(fault)} />);
      expect(await screen.findByRole("alert")).toHaveTextContent(
        fault === "conflict" ? "409" : "422",
      );
      expect(
        screen.queryByRole("button", { name: "Download synthetic claims" }),
      ).not.toBeInTheDocument();
      expect(screen.getByText("Not modeled")).toBeVisible();
    },
  );
  it("shows empty cohort as zero and downside as unknown", async () => {
    render(<App runtime={runtime("empty")} />);
    expect(
      await screen.findByText("No eligible jobs in this calculation."),
    ).toBeVisible();
    expect(screen.getByText("Not measured")).toBeVisible();
    expect(
      screen.getByRole("button", {
        name: "Inspect recovery value and evidence",
      }),
    ).toHaveTextContent("$0–$0");
  });
});
