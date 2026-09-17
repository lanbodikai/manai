"""Bounded, read-only HTTP and official MCP adapters for the optional reviewer."""
from __future__ import annotations

import asyncio
import json
import math
import os
from pathlib import Path
import sys
from typing import Any
from urllib.parse import quote
from uuid import uuid4

import anyio
import httpx
from jsonschema import Draft202012Validator
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class ReviewError(Exception):
    """Public-safe failure; upstream bodies and credentials are never exposed."""

    def __init__(self, status: int, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.retryable = retryable


def _invalid(message: str) -> ReviewError:
    return ReviewError(502, "UPSTREAM_RESPONSE_INVALID", message)


def _mismatch(message: str) -> ReviewError:
    return ReviewError(409, "DATA_VERSION_MISMATCH", message)


def _finite(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(_finite(v) for v in value.values())
    if isinstance(value, list):
        return all(_finite(v) for v in value)
    return True


def _decode(raw: bytes) -> dict:
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=no_duplicates)
        if not isinstance(value, dict) or not _finite(value):
            raise ValueError("Expected finite JSON object")
        return value
    except (ValueError, UnicodeDecodeError, RecursionError) as exc:
        raise _invalid("Analysis returned malformed JSON.") from exc


class AnalysisClient:
    """Read a frozen audit and only its explicitly paginated evidence.

    ``timeout`` bounds the entire load as well as individual HTTP operations.
    ``max_bytes`` bounds each decoded response; page/evidence limits also bound
    total response count. Truncated coverage is returned, never certified full.
    """

    def __init__(self, base_url, timeout=5.0, max_pages=4, max_evidence=100,
                 max_bytes=1000000, transport=None):
        url = httpx.URL(base_url)
        if url.scheme not in ("http", "https") or not url.host or url.userinfo or url.query or url.fragment:
            raise ValueError("Analysis URL must be an HTTP(S) service URL without credentials, query or fragment")
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        for name, value in (("max_pages", max_pages), ("max_evidence", max_evidence), ("max_bytes", max_bytes)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(name + " must be a positive integer")
        if max_pages > 4 or max_evidence > 100:
            raise ValueError("Evidence limits must not exceed 100 records / 4 pages")
        self.base_url = str(url).rstrip("/")
        self.timeout = timeout
        self.max_pages = max_pages
        self.max_evidence = max_evidence
        self.max_bytes = max_bytes
        self.transport = transport
        root = Path(__file__).resolve().parents[1]
        spec = json.loads((root / "contracts/openapi.json").read_text())
        if spec["components"]["schemas"]["Audit"]["properties"]["contract_version"].get("const") != "0.4":
            raise ValueError("Reviewer requires the active Contract 0.4 schema")
        self._specs = {"0.4": spec}

    def _validate(self, value: dict, name: str, version: str) -> None:
        spec = self._specs.get(version)
        if spec is None:
            raise _invalid("Unsupported analysis contract version.")
        validator = Draft202012Validator({"$ref": "#/components/schemas/" + name,
                                           "components": spec["components"]})
        if not _finite(value) or next(validator.iter_errors(value), None) is not None:
            raise _invalid("Analysis response does not match the agreed " + name + " schema.")

    async def _get(self, client, path, params=None):
        async with client.stream("GET", self.base_url + path, params=params) as response:
            if response.status_code != 200:
                status = response.status_code
                if status == 404:
                    code = "EVIDENCE_NOT_FOUND" if "/evidence" in path else "AUDIT_NOT_FOUND"
                    raise ReviewError(404, code, "Analysis audit or evidence is missing or expired.")
                if status == 409:
                    raise _mismatch("Analysis rejected the audit's source version.")
                if status == 429:
                    raise ReviewError(429, "REQUEST_BUDGET_EXCEEDED", "Analysis request budget is exhausted.", True)
                if status == 503:
                    raise ReviewError(503, "UPSTREAM_UNAVAILABLE", "Analysis data is not ready.", True)
                if status == 504:
                    raise ReviewError(504, "EXPLANATION_TIMEOUT", "Analysis request timed out.", True)
                raise _invalid("Analysis returned an unexpected HTTP status; redirects are not followed.")
            if response.headers.get("content-encoding", "identity").lower() != "identity":
                raise _invalid("Analysis returned encoded content despite the bounded identity request.")
            raw = bytearray()
            async for chunk in response.aiter_bytes():
                if len(raw) + len(chunk) > self.max_bytes:
                    raise _invalid("Analysis response exceeded the byte limit.")
                raw.extend(chunk)
            return _decode(bytes(raw))

    async def load(self, audit_id):
        if not isinstance(audit_id, str) or not audit_id.strip() or audit_id in {".", ".."} or len(audit_id) > 512:
            raise ReviewError(422, "INVALID_AUDIT_ID", "A bounded nonempty audit ID is required.")
        try:
            async with asyncio.timeout(self.timeout):
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False,
                                             transport=self.transport, trust_env=False,
                                             headers={"Accept-Encoding": "identity"}) as client:
                    return await self._load(client, audit_id)
        except ReviewError:
            raise
        except (TimeoutError, httpx.TimeoutException) as exc:
            raise ReviewError(504, "EXPLANATION_TIMEOUT", "Analysis evidence retrieval timed out.", True) from exc
        except httpx.HTTPError as exc:
            raise ReviewError(503, "UPSTREAM_UNAVAILABLE", "Analysis service is unavailable.", True) from exc

    async def _load(self, client, audit_id):
        path = "/api/audits/" + quote(audit_id, safe="")
        audit = await self._get(client, path)
        version = audit.get("contract_version")
        if not isinstance(version, str):
            raise _invalid("Analysis response has no contract version.")
        self._validate(audit, "Audit", version)
        if audit["audit_id"] != audit_id:
            raise _mismatch("Analysis returned a different audit.")
        if any(not audit["provenance"][key].strip() for key in ("data_fingerprint", "source_version")):
            raise _mismatch("Audit source identity is unknown.")
        total = audit["evidence_count"]
        refs, details, reasons = {}, {}, []

        async def detail_for(eid, ref=None, *, baseline=False):
            if eid in {".", ".."}:
                raise _invalid("Analysis returned an invalid evidence identity.")
            if eid not in details:
                detail = await self._get(client, path + "/evidence/" + quote(eid, safe=""))
                self._validate(detail, "EvidenceDetail", version)
                actual_ref = detail["evidence"]
                if detail["audit_id"] != audit_id or actual_ref["id"] != eid:
                    raise _mismatch("Evidence detail does not match its audit-scoped identity.")
                for key in ("data_fingerprint", "source_version", "sample_label", "window_label"):
                    if detail["provenance"][key] != audit["provenance"][key]:
                        raise _mismatch("Evidence provenance differs from the immutable audit.")
                if detail["provenance"]["synthetic"] != actual_ref["synthetic"]:
                    raise _mismatch("Evidence reference and detail disagree on the synthetic label.")
                details[eid] = detail
            detail = details[eid]
            if ref is not None and detail["evidence"] != ref:
                raise _mismatch("Evidence detail does not match its paginated reference.")
            if baseline and detail["evidence"]["kind"] != "job":
                raise _mismatch("The selected CPU baseline must resolve to job evidence.")
            if len(details) > total:
                raise _invalid("Fetched evidence exceeds the immutable audit total.")

        # Reserve one slot for the selected job. Finding/aggregate pages can precede
        # that job, and a bounded sample must still review this individual pilot.
        pilot = audit["scenario"].get("cpu_pilot")
        baseline_id = pilot["baseline_evidence_id"] if pilot is not None else None
        if baseline_id is not None:
            await detail_for(baseline_id, baseline=True)

        cursor, cursors, pages, ended = None, set(), 0, False
        while pages < self.max_pages and len(details) < self.max_evidence:
            limit = min(100, self.max_evidence - len(details))
            params = {"limit": limit}
            if cursor is not None:
                params["cursor"] = cursor
            page = await self._get(client, path + "/evidence", params=params)
            self._validate(page, "EvidencePage", version)
            if page["audit_id"] != audit_id:
                raise _mismatch("Evidence page belongs to another audit.")
            if page["total"] != total or len(page["items"]) > limit:
                raise _invalid("Evidence pagination disagrees with the immutable audit or requested limit.")
            pages += 1
            for ref in page["items"]:
                if ref["id"] in refs:
                    raise _invalid("Evidence pagination contains duplicate references.")
                refs[ref["id"]] = ref
                await detail_for(ref["id"], ref)
            if len(set(refs) | set(details)) > total:
                raise _invalid("Evidence count exceeds the immutable audit total.")
            cursor = page["next_cursor"]
            if cursor is None:
                ended = True
                break
            if not page["items"] or cursor in cursors:
                raise _invalid("Evidence pagination does not make progress.")
            cursors.add(cursor)
        if not ended:
            if len(details) >= self.max_evidence:
                reasons.append("max_evidence")
            if pages >= self.max_pages:
                reasons.append("max_pages")
        elif len(refs) != total:
            reasons.append("source_ended_before_total")
        for ref in audit["evidence_preview"]:
            known = refs.get(ref["id"]) or (details[ref["id"]]["evidence"] if ref["id"] in details else None)
            if known is not None and known != ref:
                raise _mismatch("Evidence preview differs from the fetched reference.")
            if ended and len(refs) == total and ref["id"] not in refs:
                raise _invalid("Evidence preview cannot be resolved in the complete page listing.")
        targeted = sorted(set(details) - set(refs))
        complete = ended and not reasons and not targeted and len(refs) == len(details) == total
        return audit, list(details.values()), {
            "listed_count": len(refs), "fetched_count": len(details), "total": total,
            "targeted_count": len(targeted), "targeted_evidence_ids": targeted,
            "complete": complete, "truncated": not complete, "reasons": reasons,
            "pages_fetched": pages}


def _nested_review_error(exc):
    if isinstance(exc, ReviewError):
        return exc
    for child in getattr(exc, "exceptions", ()):
        match = _nested_review_error(child)
        if match is not None:
            return match
    return None


class OfficialMCP:
    """Real official stdio connection; price-book access is not dataset proof."""

    def __init__(self, repo_root: Path, timeout=15, max_calls=6, context_mode="price_only"):
        self.repo_root = Path(repo_root).resolve()
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        if not isinstance(max_calls, int) or isinstance(max_calls, bool) or not 2 <= max_calls <= 6:
            raise ValueError("max_calls must allow list_tools and price_book, with at most six calls")
        if context_mode not in {"price_only", "rules"}:
            raise ValueError("context_mode must be price_only or rules")
        self.context_mode = context_mode
        self.timeout, self.max_calls = timeout, max_calls
        self.max_bytes = 1000000

    def _bounded(self, response):
        raw = response.model_dump_json().encode("utf-8")
        if len(raw) > self.max_bytes:
            raise ReviewError(503, "AGENT_UNAVAILABLE", "MCP response exceeded the byte limit.")

    async def inspect(self):
        if self.context_mode == "rules" and self.max_calls < 4:
            raise ReviewError(429, "REQUEST_BUDGET_EXCEEDED", "Rules context requires at least four MCP operations.")
        # The SDK additionally inherits only its documented OS allowlist
        # (HOME/LOGNAME/PATH/SHELL/TERM/USER); no provider credentials are passed.
        env = {key: value for key, value in os.environ.items()
               if key in {"PATH", "HOME", "USER", "LOGNAME", "SHELL", "TERM", "SYSTEMROOT", "WINDIR"}
               and not value.startswith("()")}
        env.update({"PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1"})
        params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_layer.server"],
                                       cwd=self.repo_root, env=env)
        traces = []
        try:
            with anyio.fail_after(self.timeout):
                with open(os.devnull, "w") as errlog:
                    async with stdio_client(params, errlog=errlog) as (read, write):
                        async with ClientSession(read, write, read_timeout_seconds=self.timeout) as session:
                            initialized = await session.initialize()
                            self._bounded(initialized)
                            listing = await session.list_tools()
                            self._bounded(listing)
                            traces.append("mcp:list_tools:" + uuid4().hex)
                            names = [tool.name for tool in listing.tools]
                            required = {"price_book"}
                            if self.context_mode == "rules":
                                required.update({"list_rules", "list_findings", "causal"})
                            if not required.issubset(names):
                                raise ReviewError(503, "AGENT_UNAVAILABLE", "Required official MCP tools are unavailable.")

                            async def call(name, arguments):
                                if len(traces) >= self.max_calls:
                                    raise ReviewError(429, "REQUEST_BUDGET_EXCEEDED", "MCP operation budget is exhausted.")
                                result = await session.call_tool(name, arguments=arguments)
                                self._bounded(result)
                                traces.append("mcp:" + name + ":" + uuid4().hex)
                                if getattr(result, "is_error", True):
                                    raise ReviewError(503, "AGENT_UNAVAILABLE", "Official MCP tool returned an error.")
                                data = getattr(result, "structured_content", None)
                                if data is None:
                                    text = [block.text for block in result.content if block.type == "text"]
                                    if len(text) != 1:
                                        raise ReviewError(503, "AGENT_UNAVAILABLE", "Official MCP tool did not return one JSON object.")
                                    data = _decode(text[0].encode("utf-8"))
                                if not isinstance(data, dict) or not _finite(data) or data.get("success") is False:
                                    raise ReviewError(503, "AGENT_UNAVAILABLE", "Official MCP returned invalid or failed tool data.")
                                return {"tool": name, "arguments": arguments, "tool_trace_id": traces[-1],
                                        "source": "official_mcp", "data": data,
                                        "audit_membership_verified": False, "data_identity_verified": False}

                            price_book = (await call("price_book", {}))["data"]
                            price_schema = {"type": "object", "required": ["version", "usd_per_gpu_hour", "usd_per_kwh", "usd_per_engineer_hour", "epoch_offset"],
                                            "properties": {"version": {"type": "string", "minLength": 1},
                                                           "usd_per_gpu_hour": {"type": "number", "minimum": 0},
                                                           "usd_per_kwh": {"type": "number", "minimum": 0},
                                                           "usd_per_engineer_hour": {"type": "number", "minimum": 0},
                                                           "epoch_offset": {"type": "integer"}}}
                            if next(Draft202012Validator(price_schema).iter_errors(price_book), None) is not None:
                                raise ReviewError(503, "AGENT_UNAVAILABLE", "Official MCP price book has an invalid shape.")
                            output = {"price_book": price_book, "tool_names": names,
                                      "rule_context": None, "finding_context": None, "causal_context": None,
                                      "limitations": ["Price-book retrieval proves MCP connectivity only; it does not verify audit membership or dataset lineage.",
                                                      "No audit-specific official finding was corroborated."]}
                            if self.context_mode == "rules":
                                rules = await call("list_rules", {})
                                rules_schema = {"type": "object", "required": ["success", "rules"],
                                                "properties": {"success": {"const": True}, "rules": {"type": "array", "items": {
                                                    "type": "object", "required": ["rule_id", "name", "summary"],
                                                    "properties": {key: {"type": "string"} for key in ("rule_id", "name", "summary")}}}}}
                                if next(Draft202012Validator(rules_schema).iter_errors(rules["data"]), None) is not None:
                                    raise ReviewError(503, "AGENT_UNAVAILABLE", "Official MCP rule catalogue has an invalid shape.")
                                detector = "rules::gpu-not-needed"
                                findings = await call("list_findings", {"detector_id": detector, "limit": 20, "offset": 0})
                                findings_schema = {"type": "object", "required": ["success", "total", "findings"],
                                                   "properties": {"success": {"const": True}, "total": {"type": "integer", "minimum": 0},
                                                                  "findings": {"type": "array", "maxItems": 20, "items": {
                                                                      "type": "object", "required": ["id", "detectorId", "rootCauses", "metadata"],
                                                                      "properties": {"id": {"type": "string", "minLength": 1, "maxLength": 512},
                                                                                     "detectorId": {"const": detector},
                                                                                     "rootCauses": {"type": "array", "items": {"type": "string"}},
                                                                                     "metadata": {"type": "object"}}}}}}
                                if next(Draft202012Validator(findings_schema).iter_errors(findings["data"]), None) is not None:
                                    raise ReviewError(503, "AGENT_UNAVAILABLE", "Official MCP finding page has an invalid shape.")
                                items, total = findings["data"]["findings"], findings["data"]["total"]
                                if len(items) > total or len({item["id"] for item in items}) != len(items):
                                    raise ReviewError(503, "AGENT_UNAVAILABLE", "Official MCP finding count or identities are inconsistent.")
                                findings["coverage"] = {"fetched_count": len(items), "total": total,
                                                        "complete": len(items) == total, "truncated": len(items) < total}
                                output["rule_context"], output["finding_context"] = rules, findings
                                output["limitations"].append("Official rule/finding context has no verified fingerprint or membership link to the selected A audit.")
                                if len(items) < total:
                                    output["limitations"].append("Only the first bounded finding page was retrieved; no complete-cohort corroboration is claimed.")
                                if items and items[0]["rootCauses"]:
                                    if len(traces) >= self.max_calls:
                                        output["limitations"].append("Causal lookup was skipped because the MCP call budget was exhausted.")
                                    else:
                                        causal = await call("causal", {"finding_id": items[0]["id"], "hop_count": 2})
                                        causal_schema = {"type": "object", "required": ["success", "message", "findings"],
                                                         "properties": {"success": {"const": True}, "message": {"type": "string"},
                                                                        "findings": {"type": ["array", "null"], "items": {"type": "object"}}}}
                                        if next(Draft202012Validator(causal_schema).iter_errors(causal["data"]), None) is not None:
                                            raise ReviewError(503, "AGENT_UNAVAILABLE", "Official MCP causal context has an invalid shape.")
                                        output["causal_context"] = causal
                                        if not causal["data"]["findings"]:
                                            output["limitations"].append("Causal output was empty; absence of a chain is not proof of innocence or workload compatibility.")
                                else:
                                    output["limitations"].append("The first retrieved finding had no available causal root, or the finding page was empty; no causal lookup was run.")
                            output.update(tool_trace_ids=traces, tool_calls=len(traces))
                            return output
        except Exception as exc:
            known = _nested_review_error(exc)
            if known is not None:
                # A malformed MCP JSON result is a failed tool, not an HTTP-A error.
                if known.status == 502:
                    raise ReviewError(503, "AGENT_UNAVAILABLE", "Official MCP returned malformed content.") from exc
                raise known
            if isinstance(exc, TimeoutError):
                raise ReviewError(504, "EXPLANATION_TIMEOUT", "Official MCP inspection timed out.", True) from exc
            raise ReviewError(503, "AGENT_UNAVAILABLE", "Official MCP inspection is unavailable.", True) from exc
