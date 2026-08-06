"""Stdlib-only local admin health endpoint for P01-02."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from urllib.request import urlopen

from apps.api.local_runtime import health_payload


class AdminHealthHandler(BaseHTTPRequestHandler):
    server_version = "FenjiuLocalAdminHealth/1"

    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_error(404)
            return
        body = json.dumps(health_payload("admin"), sort_keys=True).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def serve(host: str, port: int) -> None:
    ThreadingHTTPServer((host, port), AdminHealthHandler).serve_forever()


def healthcheck(url: str) -> int:
    try:
        with urlopen(url, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        return 1
    return 0 if payload == health_payload("admin") else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="P01-02 local-only admin health endpoint.")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--healthcheck", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--url", default="http://127.0.0.1:8001/health")
    args = parser.parse_args()

    if args.healthcheck:
        return healthcheck(args.url)
    if args.serve:
        serve(args.host, args.port)
        return 0
    print(json.dumps(health_payload("admin"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
