"""Stdlib-only local health endpoint for P01-02."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from urllib.request import urlopen

from core.contracts import default_execution_policy, synthetic_scope

API_HEALTH_URL = "http://127.0.0.1:8000/health"


def health_payload(component: str) -> dict[str, object]:
    policy = default_execution_policy()
    scope = synthetic_scope()
    return {
        "component": component,
        "status": "ok",
        "capability_status": "local_only",
        "scope": {
            "tenant_id": scope.tenant_id,
            "project_id": scope.project_id,
            "business_line_id": scope.business_line_id,
            "correlation_id": scope.correlation_id,
        },
        "external_send": policy.external_send,
        "public_publish": policy.public_publish,
        "real_quote": policy.real_quote,
        "payment": policy.payment,
        "order_create": policy.order_create,
        "refund": policy.refund,
        "external_execution_allowed": policy.external_execution_allowed,
        "business_external_ready": policy.business_external_ready,
    }


class HealthHandler(BaseHTTPRequestHandler):
    server_version = "FenjiuLocalHealth/1"

    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_error(404)
            return
        body = json.dumps(health_payload("api"), sort_keys=True).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def serve(host: str, port: int) -> None:
    ThreadingHTTPServer((host, port), HealthHandler).serve_forever()


def healthcheck() -> int:
    try:
        with urlopen(API_HEALTH_URL, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        return 1
    return 0 if payload == health_payload("api") else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="P01-02 local-only API health endpoint.")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--healthcheck", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.healthcheck:
        return healthcheck()
    if args.serve:
        serve(args.host, args.port)
        return 0
    print(json.dumps(health_payload("api"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
