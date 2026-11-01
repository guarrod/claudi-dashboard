"""Hub: receives usage reports from several machines and serves the merged view.

Runs on the VPS behind Nginx (see deploy/). Standard library only.

    CLAUDE_HUB_TOKEN=<secret> python hub.py --port 8788

    POST /api/ingest      Bearer token; gzip/plain JSON from push.py
    GET  /api/telemetry   Bearer token; merged snapshot (same shape as /data.json)
    GET  /healthz         no auth, no data

Every machine's latest report is kept in data/<machine>.json so a restart
loses nothing. The token is mandatory: the hub refuses to start without one.
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
import re
import threading
import time
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from collector import HistoryStore, Record, build_snapshot

HERE = Path(__file__).parent
MACHINE_RE = re.compile(r"^[A-Za-z0-9_.-]{1,40}$")
MAX_BODY = 8 * 1024 * 1024          # compressed
MAX_RAW = 64 * 1024 * 1024          # after decompression
MAX_RECORDS = 200_000
MAX_MACHINES = 8
MAX_AGE_S = 40 * 86400              # drop records older than this on ingest


class Hub:
    def __init__(self, data_dir: Path, history: HistoryStore | None = None) -> None:
        self.dir = data_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.history = history
        self.lock = threading.Lock()
        self.machines: dict[str, dict] = {}
        self._last_save = 0.0
        for f in self.dir.glob("*.json"):
            try:
                self._store(json.loads(f.read_text(encoding="utf-8")), persist=False)
            except (OSError, ValueError, KeyError, TypeError):
                continue    # a corrupt file must not stop the hub

    def _store(self, payload: dict, persist: bool = True) -> int:
        """Validate and keep one machine's report. Raises ValueError on bad input."""
        name = payload.get("machine")
        if not isinstance(name, str) or not MACHINE_RE.match(name):
            raise ValueError("bad machine name")
        rows = payload.get("records")
        if not isinstance(rows, list) or len(rows) > MAX_RECORDS:
            raise ValueError("bad records")
        os_name = payload.get("os")
        os_name = os_name[:32] if isinstance(os_name, str) else "?"
        lp = payload.get("last_prompt")
        lp = float(lp) if isinstance(lp, (int, float)) and not isinstance(lp, bool) else None
        now = time.time()
        recs = []
        for row in rows:
            if not isinstance(row, list) or len(row) != 9:
                raise ValueError("bad row")
            r = Record.from_wire(row, name)
            if now - r.ts <= MAX_AGE_S:
                recs.append(r)
        with self.lock:
            if name not in self.machines and len(self.machines) >= MAX_MACHINES:
                raise ValueError("too many machines")
            self.machines[name] = {"name": name, "os": os_name, "records": recs,
                                   "last_prompt": lp, "reported_at": now}
        if persist:
            tmp = self.dir / f"{name}.json.tmp"
            tmp.write_text(json.dumps({"machine": name, "os": os_name, "last_prompt": lp,
                                       "records": [r.to_wire() for r in recs]}), encoding="utf-8")
            os.replace(tmp, self.dir / f"{name}.json")
        else:   # loaded from disk: report time = file mtime
            with self.lock:
                self.machines[name]["reported_at"] = (self.dir / f"{name}.json").stat().st_mtime
        return len(recs)

    def ingest(self, payload: dict) -> int:
        return self._store(payload)

    def snapshot(self) -> dict:
        with self.lock:
            sources = [dict(m) for m in self.machines.values()]
            save = self.history is not None and time.time() - self._last_save >= 60
            if save:
                self._last_save = time.time()
        snap = build_snapshot(sources, history=self.history, save_history=save)
        snap["source"] = "hub"
        return snap


def _decode(body: bytes, encoding: str) -> dict:
    if encoding == "gzip":
        d = zlib.decompressobj(16 + zlib.MAX_WBITS)
        body = d.decompress(body, MAX_RAW)
        if d.unconsumed_tail:
            raise ValueError("payload too large")
    return json.loads(body)


def make_handler(hub: Hub, token: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_a) -> None:
            pass

        def _send(self, code: int, obj: dict) -> None:
            body = json.dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _authed(self) -> bool:
            got = self.headers.get("Authorization", "")
            ok = hmac.compare_digest(got.encode(), ("Bearer " + token).encode())
            if not ok:
                self._send(401, {"error": "unauthorized"})
            return ok

        def do_GET(self) -> None:
            path = self.path.split("?", 1)[0]
            if path == "/healthz":
                self._send(200, {"ok": True})
            elif path == "/api/telemetry":
                if self._authed():
                    try:
                        self._send(200, hub.snapshot())
                    except Exception as e:      # never crash the hub on one bad read
                        self._send(500, {"error": str(e)})
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path.split("?", 1)[0] != "/api/ingest":
                return self._send(404, {"error": "not found"})
            if not self._authed():
                return
            try:
                n = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                n = -1
            if not 0 < n <= MAX_BODY:
                return self._send(413, {"error": "bad or oversized body"})
            try:
                payload = _decode(self.rfile.read(n), self.headers.get("Content-Encoding", ""))
                self._send(200, {"ok": True, "records": hub.ingest(payload)})
            except (ValueError, zlib.error, TypeError, KeyError) as e:
                self._send(400, {"error": str(e)[:100]})

    return Handler


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8788)
    ap.add_argument("--data", type=Path, default=HERE / "hub-data")
    args = ap.parse_args()

    token = os.environ.get("CLAUDE_HUB_TOKEN", "")
    if len(token) < 24:
        raise SystemExit("hub: set CLAUDE_HUB_TOKEN to a secret of at least 24 characters")

    args.data.mkdir(parents=True, exist_ok=True)     # HistoryStore opens its db right away
    hub = Hub(args.data, HistoryStore(args.data / "history.db"))
    srv = ThreadingHTTPServer((args.host, args.port), make_handler(hub, token))
    print(f"hub on http://{args.host}:{args.port} · {len(hub.machines)} machine(s) loaded")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
