"""Deliberately faulty optional service, only for R02-R05 acceptance."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import time


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        mode = body["question"]
        if mode == "hang": time.sleep(40)
        if mode == "malformed":
            status, data = 200, b"{broken"
        elif mode == "wrong-audit":
            status = 200
            data = json.dumps({"audit_id":"wrong-audit", "client_request_id":body["client_request_id"],
                "status":"ok", "answer":"Fault-injection response, never display as evidence.",
                "supporting_evidence_ids":[],"tool_trace_ids":[],"limitations":[],
                "usage":{"tool_calls":0,"input_tokens":None,"output_tokens":None,"estimated_usd":None,
                         "latency_ms":0,"model":None,"provider":None}}).encode()
        else:
            status, data = 503, json.dumps({"error":{"code":"AGENT_UNAVAILABLE","message":"Injected reviewer outage", "retryable":True,"request_id":"resilience-test"}}).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try: self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError): pass


ThreadingHTTPServer(("0.0.0.0", 8002), Handler).serve_forever()
