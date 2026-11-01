"""Reports this machine's Claude Code usage to the hub.

    python push.py                 # one report, then exit (cron / Task Scheduler)
    python push.py --loop 120      # report every 120 s (launchd / background)

Needs config.json or CLAUDE_DASH_URL / CLAUDE_DASH_TOKEN (see config.py).
Standard library only; the body is gzipped JSON of the last 32 days of records.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
import urllib.error
import urllib.request

import config
from collector import Collector


def push(cfg: dict, payload: dict, timeout: float = 15.0) -> None:
    """POST one report; raises on any failure."""
    body = gzip.compress(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    req = urllib.request.Request(
        cfg["url"] + "/api/ingest", data=body, method="POST",
        headers={"Authorization": "Bearer " + cfg["token"],
                 "Content-Type": "application/json", "Content-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        r.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", type=float, default=0, help="seconds between reports (0 = once)")
    args = ap.parse_args()

    cfg = config.load()
    if not cfg.get("url") or not cfg.get("token"):
        print("push: set url and token in config.json (or CLAUDE_DASH_URL / CLAUDE_DASH_TOKEN)",
              file=sys.stderr)
        return 2
    col = Collector(machine=cfg.get("machine"))

    while True:
        try:
            payload = col.payload()
            push(cfg, payload)
            print(f"{time.strftime('%H:%M:%S')} pushed {len(payload['records'])} records as {col.machine}")
        except (urllib.error.URLError, OSError, ValueError) as e:
            print(f"{time.strftime('%H:%M:%S')} push failed: {e}", file=sys.stderr)
            if not args.loop:
                return 1
        if not args.loop:
            return 0
        time.sleep(args.loop)


if __name__ == "__main__":
    raise SystemExit(main())
