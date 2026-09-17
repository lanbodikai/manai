"""Official HTTP failure semantics using original synthetic responses."""
import unittest
import httpx
from service.analysis_routes import ServiceError, fetch_source_context


class Upstream(unittest.IsolatedAsyncioTestCase):
    async def test_C05_unavailable_and_malformed(self):
        for status, body, expected in ((503, {}, 503), (200, {"wrong": "shape"}, 502)):
            async with httpx.AsyncClient(base_url="http://synthetic", transport=httpx.MockTransport(
                lambda request: httpx.Response(status, json=body))) as client:
                with self.assertRaises(ServiceError) as caught:
                    await fetch_source_context(client)
                self.assertEqual(caught.exception.status, expected)


if __name__ == "__main__": unittest.main()
