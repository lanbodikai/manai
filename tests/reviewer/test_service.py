import asyncio
from dataclasses import replace
import json
import unittest
import httpx

from eval.agent.cases import CASES, fixture, fixture_transport, FixtureMCP, grade
from reviewer.clients import AnalysisClient, ReviewError
from reviewer.main import create_app
from reviewer.settings import Settings
from reviewer.model import ModelReviewer


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    def app(self, case="included_cohort", **kwargs):
        audit, evidence = fixture(case)
        analysis = AnalysisClient("http://fixture-a", transport=fixture_transport(audit, evidence))
        return create_app(kwargs.pop("settings", Settings()), analysis=analysis, mcp=kwargs.pop("mcp", FixtureMCP(case == "tool_failure")), **kwargs)

    async def post(self, app, body=None):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://reviewer") as client:
            return await client.post("/api/audits/synthetic-audit-001/explanations", json=body if body is not None else {"client_request_id": "test", "question": "Review risk and evidence"})

    async def test_eight_cases_three_repetitions(self):
        for repeat in range(3):
            for case, question in CASES:
                with self.subTest(repeat=repeat, case=case):
                    audit, evidence = fixture(case)
                    before = json.dumps([audit, evidence], sort_keys=True)
                    analysis = AnalysisClient("http://fixture-a", transport=fixture_transport(audit, evidence))
                    app = create_app(Settings(), analysis=analysis, mcp=FixtureMCP(case == "tool_failure"))
                    response = await self.post(app, {"client_request_id": "test", "question": question})
                    gates = grade(case, response.status_code, response.json(), audit, evidence, before)
                    self.assertNotIn(False, gates.values(), (gates, response.json()))

    async def test_invalid_inputs(self):
        for body in ({}, {"client_request_id": "x", "question": " "}, {"client_request_id": "x", "question": "x" * 2001}, {"client_request_id": "x", "question": "risk", "mode": "hack"}):
            self.assertEqual((await self.post(self.app(), body)).status_code, 422)

    async def test_g01_rejects_corrupted_rendered_source_and_independent_values(self):
        for case, old, new in [("included_cohort", "30 GPU-hours", "999 GPU-hours"),
                               ("headline_hours", "C independently expected: 30.0", "C independently expected: 999.0")]:
            audit, evidence = fixture(case)
            before = json.dumps([audit, evidence], sort_keys=True)
            result = (await self.post(self.app(case))).json()
            self.assertIn(old, result["answer"])
            result["answer"] = result["answer"].replace(old, new)
            self.assertFalse(grade(case, 200, result, audit, evidence, before)["G01"])

    async def test_model_adapter_connected_to_service_same_eight_cases(self):
        def provider(request):
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
                "selected_fact_ids": ["eligible_hours"], "selected_check_ids": [],
                "concern_codes": ["gpu_dependency", "correctness", "recovery"]})}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 30}})
        reviewer = ModelReviewer("http://localhost/v1", "synthetic-test-key", "synthetic-test-model", transport=httpx.MockTransport(provider))
        for repeat in range(3):
            for case, question in CASES:
                audit, evidence = fixture(case)
                before = json.dumps([audit, evidence], sort_keys=True)
                app = create_app(Settings(mode="model"), analysis=AnalysisClient("http://fixture-a", transport=fixture_transport(audit, evidence)), mcp=FixtureMCP(case == "tool_failure"), model=reviewer)
                response = await self.post(app, {"client_request_id": f"mock-{repeat}", "question": question})
                self.assertNotIn(False, grade(case, response.status_code, response.json(), audit, evidence, before).values(), response.json())
                if response.status_code == 200:
                    self.assertIn("model-selected review", response.json()["answer"])
                    self.assertIsNone(response.json()["usage"]["estimated_usd"])

    async def test_missing_provider_is_not_success(self):
        response = await self.post(self.app(settings=Settings(mode="model")))
        self.assertEqual(response.status_code, 503)
        self.assertIn("error", response.json())

    async def test_total_timeout_and_slot_cleanup(self):
        class SlowMCP:
            async def inspect(self):
                await asyncio.sleep(1)
        app = self.app(settings=Settings(timeout_seconds=.03), mcp=SlowMCP())
        response = await self.post(app)
        self.assertEqual(response.status_code, 504)
        self.assertEqual(app.state.active, 0)

    async def test_concurrency_budget(self):
        app = self.app()
        app.state.active = 2
        response = await self.post(app)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(app.state.active, 2)

    async def test_health_does_not_claim_readiness(self):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app(settings=Settings(mode="model"))), base_url="http://reviewer") as client:
            result = (await client.get("/health")).json()
        self.assertEqual(result["provider"], "unconfigured")
        self.assertEqual(result["tools"], "not_checked")

    async def test_unexpected_failure_is_redacted(self):
        class Broken:
            async def load(self, _):
                raise RuntimeError("a-secret-token")
        app = create_app(Settings(), analysis=Broken(), mcp=FixtureMCP())
        response = await self.post(app)
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("a-secret-token", response.text)


if __name__ == "__main__":
    unittest.main()
