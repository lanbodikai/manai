"""Temporary integration probe, deliberately outside B's dashboard ownership."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
import os
import uuid

class Handler(BaseHTTPRequestHandler):
    def do_GET(self): self.respond()
    def do_POST(self): self.respond()
    def respond(self):
        if self.path.startswith("/api/"):
            try:
                length=int(self.headers.get("Content-Length","0"))
                if length>65536: return self.send_body(413,b"Request too large","text/plain")
                payload=self.rfile.read(length) if self.command=="POST" else None
                request=Request(os.getenv("ANALYSIS_URL","http://analysis:8001")+self.path,
                    data=payload, method=self.command, headers={"Content-Type":"application/json"})
                try:
                    response=urlopen(request, timeout=20)
                except HTTPError as exc:
                    response=exc
                with response:
                    return self.send_body(response.status,response.read(),response.headers.get("Content-Type","application/json"))
            except (URLError, TimeoutError, OSError):
                data={"error":{"code":"UPSTREAM_UNAVAILABLE","message":"Analysis service unavailable.",
                    "retryable":True,"request_id":str(uuid.uuid4())}}
                return self.send_body(503,json.dumps(data).encode(),"application/json")
        allowed={"/":(Path(__file__).parent/"index.html","text/html; charset=utf-8"),
                 "/bootstrap/fixture.json":(Path('/app/fixtures/audit-response.json'),"application/json")}
        if self.command=="GET" and self.path in allowed:
            path,kind=allowed[self.path]
            return self.send_body(200,path.read_bytes(),kind)
        self.send_body(404,b"Not found","text/plain")
    def send_body(self,status,data,kind):
        self.send_response(status)
        self.send_header("Content-Type",kind)
        self.send_header("Content-Length",str(len(data)))
        self.send_header("Cache-Control","no-store")
        self.end_headers()
        self.wfile.write(data)

ThreadingHTTPServer(("0.0.0.0",3000),Handler).serve_forever()
