"""Stdlib-only local worker probes for P01-02."""

from __future__ import annotations

import argparse
import json
import time

from apps.api.local_runtime import health_payload, readiness_payload


def print_payload(component: str, action: str, *, readiness: bool = False) -> None:
    payload = readiness_payload(component) if readiness else health_payload(component)
    payload["action"] = action
    payload["writes_data"] = False
    payload["loads_fixtures"] = False
    print(json.dumps(payload, sort_keys=True))


def idle() -> None:
    print_payload("worker", "idle")
    while True:
        time.sleep(60)


def main() -> int:
    parser = argparse.ArgumentParser(description="P01-02 local-only worker probe.")
    parser.add_argument("--idle", action="store_true")
    parser.add_argument("--healthcheck", action="store_true")
    parser.add_argument("--readinesscheck", action="store_true")
    parser.add_argument("--migrate-noop", action="store_true")
    parser.add_argument("--load-fixtures-noop", action="store_true")
    args = parser.parse_args()

    if args.healthcheck:
        print_payload("worker", "healthcheck")
        return 0
    if args.readinesscheck:
        print_payload("worker", "readinesscheck", readiness=True)
        return 1
    if args.migrate_noop:
        print_payload("worker", "migrate_noop")
        return 0
    if args.load_fixtures_noop:
        print_payload("worker", "load_fixtures_noop")
        return 0
    if args.idle:
        idle()
        return 0
    print_payload("worker", "probe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
