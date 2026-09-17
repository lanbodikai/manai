"""Adapter tests use original fixtures; one test launches the real official MCP."""
from contextlib import asynccontextmanager
import asyncio
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import httpx

from reviewer.clients import AnalysisClient, OfficialMCP, ReviewError


ROOT = Path(__file__).resolve().parents[2]


def fixture(name):
    base = ROOT / "contracts/examples"
    return json.loads((base / name).read_text())


class AnalysisTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.audit = fixture("audit-without-pilot.json")
        self.id = self.audit["audit_id"]
        self.refs = self.audit["evidence_preview"]
        self.page = {"audit_id": self.id, "items": self.refs, "next_cursor": None, "total": 2}
        self.details = {}
        for ref in self.refs:
            detail = fixture("evidence-response.json")
            detail["audit_id"] = self.id
            detail["evidence"] = copy.deepcopy(ref)
            detail["join_keys"] = {"id_job": ref["source_id"]}
            self.details[ref["id"]] = detail
        self.requests = []

    def handler(self, request):
        self.requests.append(request)
        self.assertEqual(request.method, "GET")
        path = request.url.path
        if path == "/api/audits/" + self.id:
            return httpx.Response(200, json=self.audit)
        if path.endswith("/evidence"):
            return httpx.Response(200, json=self.page)
        key = path.rsplit("/", 1)[-1]
        return httpx.Response(200, json=self.details[key])

    def client(self, handler=None, **kwargs):
        return AnalysisClient("http://analysis:8001", transport=httpx.MockTransport(handler or self.handler), **kwargs)

    async def assert_error(self, client, status, code):
        with self.assertRaises(ReviewError) as raised:
            await client.load(self.id)
        self.assertEqual((raised.exception.status, raised.exception.code), (status, code))
        return raised.exception

    async def test_complete_fixture_and_get_only(self):
        audit, details, coverage = await self.client().load(self.id)
        self.assertEqual(audit, self.audit)
        self.assertEqual(len(details), 2)
        self.assertEqual(coverage, {"listed_count": 2, "fetched_count": 2, "total": 2,
                                    "complete": True, "truncated": False, "reasons": [], "pages_fetched": 1,
                                    "targeted_count": 0, "targeted_evidence_ids": []})
        self.assertEqual(len(self.requests), 4)

    async def test_pagination_cursor_and_stable_total(self):
        def handler(request):
            if request.url.path.endswith("/evidence"):
                cursor = request.url.params.get("cursor")
                return httpx.Response(200, json={"audit_id": self.id, "items": [self.refs[0 if cursor is None else 1]],
                                                "next_cursor": "next+opaque" if cursor is None else None, "total": 2})
            return self.handler(request)
        _, _, coverage = await self.client(handler).load(self.id)
        self.assertTrue(coverage["complete"])
        self.assertEqual(coverage["pages_fetched"], 2)

    async def test_page_budget_is_incomplete_not_pass(self):
        self.page.update(items=self.refs[:1], next_cursor="remaining")
        _, details, coverage = await self.client(max_pages=1).load(self.id)
        self.assertEqual(len(details), 1)
        self.assertFalse(coverage["complete"])
        self.assertTrue(coverage["truncated"])
        self.assertEqual(coverage["reasons"], ["max_pages"])

    async def test_evidence_budget_is_incomplete(self):
        self.page.update(items=self.refs[:1], next_cursor="remaining")
        _, _, coverage = await self.client(max_evidence=1).load(self.id)
        self.assertEqual(coverage["reasons"], ["max_evidence"])
        self.assertEqual(coverage["total"], 2)

    async def test_early_end_is_not_complete(self):
        self.page["items"] = self.refs[:1]
        _, _, coverage = await self.client().load(self.id)
        self.assertFalse(coverage["complete"])
        self.assertEqual(coverage["reasons"], ["source_ended_before_total"])

    async def test_empty_cohort_is_complete(self):
        self.audit.update(evidence_preview=[], evidence_count=0)
        self.page.update(items=[], total=0)
        _, details, coverage = await self.client().load(self.id)
        self.assertEqual(details, [])
        self.assertTrue(coverage["complete"])

    async def test_wrong_audit_and_wrong_page_are_conflicts(self):
        self.audit["audit_id"] = "another-audit"
        await self.assert_error(self.client(), 409, "DATA_VERSION_MISMATCH")
        self.audit["audit_id"] = self.id
        self.page["audit_id"] = "another-audit"
        await self.assert_error(self.client(), 409, "DATA_VERSION_MISMATCH")

    async def test_wrong_detail_reference_and_source_are_conflicts(self):
        key = self.refs[0]["id"]
        self.details[key]["provenance"]["data_fingerprint"] = "other-snapshot"
        await self.assert_error(self.client(), 409, "DATA_VERSION_MISMATCH")
        self.details[key]["provenance"] = copy.deepcopy(self.audit["provenance"])
        self.details[key]["evidence"]["source_id"] = "another-job"
        await self.assert_error(self.client(), 409, "DATA_VERSION_MISMATCH")

    async def test_unknown_lineage_and_synthetic_as_real_rejected(self):
        self.audit["provenance"]["data_fingerprint"] = ""
        await self.assert_error(self.client(), 409, "DATA_VERSION_MISMATCH")
        self.audit["provenance"]["data_fingerprint"] = "synthetic-fixture-v1"
        self.refs[0]["synthetic"] = False
        await self.assert_error(self.client(), 409, "DATA_VERSION_MISMATCH")

    async def test_real_snapshot_may_contain_labeled_synthetic_finding(self):
        self.audit["provenance"]["synthetic"] = False
        for ref in self.refs:
            ref["kind"] = "finding"
            self.details[ref["id"]]["evidence"] = copy.deepcopy(ref)
        _, evidence, coverage = await self.client().load(self.id)
        self.assertTrue(coverage["complete"])
        self.assertTrue(all(item["evidence"]["synthetic"] for item in evidence))

    async def test_missing_required_and_extra_fields_rejected(self):
        del self.audit["scenario"]
        await self.assert_error(self.client(), 502, "UPSTREAM_RESPONSE_INVALID")
        self.audit = fixture("audit-without-pilot.json")
        self.audit["unreviewed_extension"] = 1
        await self.assert_error(self.client(), 502, "UPSTREAM_RESPONSE_INVALID")

    async def test_malformed_nonfinite_and_duplicate_json_rejected(self):
        for content in (b"not-json", b'{"contract_version":"0.3","value":NaN}',
                        b'{"contract_version":"0.3","contract_version":"0.4"}'):
            with self.subTest(content=content):
                await self.assert_error(self.client(lambda req: httpx.Response(200, content=content)),
                                        502, "UPSTREAM_RESPONSE_INVALID")

    async def test_duplicate_references_and_inconsistent_total_rejected(self):
        self.page["items"] = [self.refs[0], self.refs[0]]
        await self.assert_error(self.client(), 502, "UPSTREAM_RESPONSE_INVALID")
        self.page["items"] = self.refs
        self.page["total"] = 3
        await self.assert_error(self.client(), 502, "UPSTREAM_RESPONSE_INVALID")

    async def test_byte_limit_and_redirect_are_rejected(self):
        await self.assert_error(self.client(max_bytes=20), 502, "UPSTREAM_RESPONSE_INVALID")
        calls = []
        def redirect(request):
            calls.append(request)
            return httpx.Response(302, headers={"location": "http://elsewhere/secrets"})
        await self.assert_error(self.client(redirect), 502, "UPSTREAM_RESPONSE_INVALID")
        self.assertEqual(len(calls), 1)

    async def test_malformed_404_and_409_are_normalized_without_echo(self):
        for status, code in ((404, "AUDIT_NOT_FOUND"), (409, "DATA_VERSION_MISMATCH")):
            with self.subTest(status=status):
                error = await self.assert_error(self.client(lambda req: httpx.Response(status, content=b"secret backend body")), status, code)
                self.assertNotIn("secret", error.message)

    async def test_network_and_total_timeout_normalized(self):
        def broken(request):
            raise httpx.ConnectError("private-network-address", request=request)
        await self.assert_error(self.client(broken), 503, "UPSTREAM_UNAVAILABLE")
        async def delayed(request):
            await asyncio.sleep(0.1)
            return httpx.Response(200, json=self.audit)
        await self.assert_error(self.client(delayed, timeout=0.01), 504, "EXPLANATION_TIMEOUT")

    async def test_active_v04_is_default_and_legacy_versions_are_rejected(self):
        audit, _, coverage = await self.client().load(self.id)
        self.assertEqual(audit["contract_version"], "0.4")
        self.assertTrue(coverage["complete"])
        for version in ("0.3", "0.5", "unknown"):
            self.audit["contract_version"] = version
            await self.assert_error(self.client(), 502, "UPSTREAM_RESPONSE_INVALID")

    def test_configuration_bounds(self):
        for kwargs in ({"max_pages": 0}, {"max_evidence": True}, {"max_bytes": -1}, {"timeout": float("inf")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.client(**kwargs)
        with self.assertRaises(ValueError):
            AnalysisClient("http://user:password@analysis")

    async def test_dot_segment_audit_ids_rejected(self):
        for bad in (".", "..", " "):
            with self.subTest(bad=bad), self.assertRaises(ReviewError) as raised:
                await self.client().load(bad)
            self.assertEqual(raised.exception.status, 422)


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def mock_rules(self, *, roots=False, total=1, max_calls=6, responses=None, tools=None, max_bytes=1000000):
        """Exercise real adapter decisions with original fabricated tool payloads."""
        payloads = {
            "price_book": {"version": "test", "usd_per_gpu_hour": 2.5, "usd_per_kwh": 0.15,
                           "usd_per_engineer_hour": 95, "epoch_offset": 0},
            "list_rules": {"success": True, "rules": [{"rule_id": "rules::gpu-not-needed", "name": "Synthetic rule", "summary": "Synthetic only"}]},
            "list_findings": {"success": True, "total": total, "findings": [{"id": "invented-finding-1",
                              "detectorId": "rules::gpu-not-needed", "rootCauses": ["invented-root"] if roots else [],
                              "metadata": {"synthetic": True}}]},
            "causal": {"success": True, "message": "No available chain in this invented case", "findings": []},
        }
        payloads.update(responses or {})
        names = tools if tools is not None else list(payloads)
        calls = []
        self.mock_calls = calls
        class Reply:
            def __init__(self, **kwargs): self.__dict__.update(kwargs)
            def model_dump_json(self):
                return json.dumps(self.__dict__, default=lambda obj: obj.__dict__)
        class Session:
            def __init__(self, *args, **kwargs): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            async def initialize(self): return Reply()
            async def list_tools(self): return Reply(tools=[Reply(name=name) for name in names])
            async def call_tool(self, name, arguments):
                calls.append((name, arguments))
                return Reply(is_error=False, structured_content=payloads[name])
        @asynccontextmanager
        async def stdio(*args, **kwargs): yield None, None
        with patch("reviewer.clients.stdio_client", stdio), patch("reviewer.clients.ClientSession", Session):
            client = OfficialMCP(ROOT, context_mode="rules", max_calls=max_calls)
            client.max_bytes = max_bytes
            return await client.inspect()

    async def test_real_official_stdio_price_book(self):
        result = await OfficialMCP(ROOT, timeout=15).inspect()
        self.assertEqual(result["tool_calls"], 2)
        self.assertEqual(len(result["tool_trace_ids"]), 2)
        self.assertIn("price_book", result["tool_names"])
        self.assertEqual(result["price_book"]["usd_per_gpu_hour"], 2.5)
        self.assertTrue(result["limitations"])
        self.assertNotIn("data_fingerprint", result)

    def test_invalid_call_budget(self):
        for budget in (0, 1, 7, True):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                OfficialMCP(ROOT, max_calls=budget)
        with self.assertRaises(ValueError):
            OfficialMCP(ROOT, context_mode="choose-tools-freely")

    async def test_rules_mode_has_fixed_arguments_and_honest_coverage(self):
        result = await self.mock_rules(total=100)
        self.assertEqual(self.mock_calls, [("price_book", {}), ("list_rules", {}),
                                          ("list_findings", {"detector_id": "rules::gpu-not-needed", "limit": 20, "offset": 0})])
        self.assertEqual(result["tool_calls"], 4)
        self.assertIsNone(result["causal_context"])
        self.assertEqual(result["finding_context"]["coverage"], {"fetched_count": 1, "total": 100, "complete": False, "truncated": True})
        for context in (result["rule_context"], result["finding_context"]):
            self.assertFalse(context["audit_membership_verified"])
            self.assertFalse(context["data_identity_verified"])
            self.assertNotIn("data_fingerprint", context)
            self.assertIn(context["tool_trace_id"], result["tool_trace_ids"])

    async def test_rules_mode_causal_is_conditional_and_bounded(self):
        result = await self.mock_rules(roots=True)
        self.assertEqual(self.mock_calls[-1], ("causal", {"finding_id": "invented-finding-1", "hop_count": 2}))
        self.assertEqual(result["tool_calls"], 5)
        self.assertEqual(result["causal_context"]["data"]["findings"], [])
        self.assertTrue(any("not proof" in note for note in result["limitations"]))
        limited = await self.mock_rules(roots=True, max_calls=4)
        self.assertEqual(limited["tool_calls"], 4)
        self.assertIsNone(limited["causal_context"])
        self.assertTrue(any("budget" in note for note in limited["limitations"]))

    async def test_rules_mode_cannot_start_with_insufficient_budget(self):
        with self.assertRaises(ReviewError) as raised:
            await self.mock_rules(max_calls=3)
        self.assertEqual(raised.exception.status, 429)
        self.assertEqual(self.mock_calls, [])

    async def test_rules_mode_missing_tools_or_invalid_data_is_failure(self):
        cases = [
            {"tools": ["price_book"]},
            {"responses": {"list_rules": {"success": False, "rules": []}}},
            {"responses": {"list_findings": {"success": True, "total": 1, "findings": [{"id": "missing-fields"}]}}},
            {"roots": True, "responses": {"causal": {"success": True, "findings": "not-a-list"}}},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ReviewError) as raised:
                await self.mock_rules(**kwargs)
            self.assertEqual(raised.exception.status, 503)

    async def test_rules_mode_tool_result_byte_limit(self):
        with self.assertRaises(ReviewError) as raised:
            await self.mock_rules(max_bytes=10)
        self.assertEqual(raised.exception.status, 503)

    async def test_missing_official_module_is_failure(self):
        result = OfficialMCP(Path("/private/tmp"), timeout=3)
        with self.assertRaises(ReviewError) as raised:
            await result.inspect()
        self.assertEqual(raised.exception.status, 503)

    async def test_failed_tool_and_secret_env_filter(self):
        class Reply:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
            def model_dump_json(self):
                return "{}"
        class Session:
            def __init__(self, *args, **kwargs): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            async def initialize(self): return Reply()
            async def list_tools(self): return Reply(tools=[Reply(name="price_book")])
            async def call_tool(self, *args, **kwargs):
                return Reply(is_error=True, structured_content={"misleading": "success"})
        captured = []
        @asynccontextmanager
        async def stdio(params, **kwargs):
            captured.append(params.env)
            yield None, None
        with patch("reviewer.clients.stdio_client", stdio), patch("reviewer.clients.ClientSession", Session), \
                patch.dict("os.environ", {"FEATHERLESS_API_KEY": "never-inherit", "OPENAI_API_KEY": "never-inherit"}):
            with self.assertRaises(ReviewError) as raised:
                await OfficialMCP(ROOT).inspect()
        self.assertEqual(raised.exception.status, 503)
        self.assertNotIn("FEATHERLESS_API_KEY", captured[0])
        self.assertNotIn("OPENAI_API_KEY", captured[0])

    async def test_timeout_cleans_up_session_and_transport(self):
        exited = []
        class Session:
            def __init__(self, *args, **kwargs): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *args): exited.append("session")
            async def initialize(self): await asyncio.sleep(1)
        @asynccontextmanager
        async def stdio(*args, **kwargs):
            try:
                yield None, None
            finally:
                exited.append("transport")
        with patch("reviewer.clients.stdio_client", stdio), patch("reviewer.clients.ClientSession", Session):
            with self.assertRaises(ReviewError) as raised:
                await OfficialMCP(ROOT, timeout=0.01).inspect()
        self.assertEqual(raised.exception.status, 504)
        self.assertEqual(exited, ["session", "transport"])


if __name__ == "__main__":
    unittest.main()
