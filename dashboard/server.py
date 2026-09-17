"""Static production dashboard and bounded same-origin proxy; no data cache or LLM."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, unquote
import json
import mimetypes
import os
import uuid

ROOT = Path(os.getenv("DASHBOARD_DIST", "/app/dist")).resolve()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self): self.respond()
    def do_POST(self): self.respond()

    def respond(self):
        if self.path.startswith("/api/"):
            reviewer = urlsplit(self.path).path.endswith("/explanations")
            target = os.getenv("REVIEWER_URL", "") if reviewer else os.getenv("ANALYSIS_URL", "http://analysis:8001")
            if not target:
                return self.failure(503, "AGENT_UNAVAILABLE", "Optional reviewer is not enabled.")
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 0 or length > 65536:
                    return self.failure(413, "INVALID_REQUEST", "Request body exceeds the permitted size.")
                payload = self.rfile.read(length) if self.command == "POST" else None
                request = Request(target.rstrip("/") + self.path, data=payload, method=self.command,
                                  headers={"Content-Type": "application/json", "Accept": "application/json"})
                try:
                    response = urlopen(request, timeout=31 if reviewer else 20)
                except HTTPError as exc:
                    response = exc
                with response:
                    return self.send_body(response.status, response.read(), response.headers.get("Content-Type", "application/json"))
            except (TimeoutError, URLError, OSError, ValueError):
                return self.failure(503, "AGENT_UNAVAILABLE" if reviewer else "UPSTREAM_UNAVAILABLE",
                                    "Optional reviewer unavailable." if reviewer else "Analysis service unavailable.")
        if self.command != "GET":
            return self.failure(404, "ROUTE_NOT_AVAILABLE", "Route not found.")
        path = (ROOT / unquote(urlsplit(self.path).path).lstrip("/")).resolve()
        if not path.is_relative_to(ROOT):
            return self.failure(404, "ROUTE_NOT_AVAILABLE", "Route not found.")
        if path == ROOT: path = ROOT / "index.html"
        if not path.is_file():
            return self.failure(404, "ROUTE_NOT_AVAILABLE", "Route not found.")
        self.send_body(200, path.read_bytes(), mimetypes.guess_type(path.name)[0] or "application/octet-stream")

    def failure(self, status, code, message):
        self.send_body(status, json.dumps({"error": {"code": code, "message": message,
                        "retryable": status >= 500, "request_id": str(uuid.uuid4())}}).encode(), "application/json")

    def send_body(self, status, data, kind):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try: self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError): pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "3000"))), Handler).serve_forever()
