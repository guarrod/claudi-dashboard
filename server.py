"""Tiny local server for the HTML telemetry dashboard.

Serves the HUD at /  (also /telemetry), static fonts at /fonts/*, and live
data at /data.json (real Claude Code usage from collector.Collector).
Standard library only.

    python server.py                 # http://127.0.0.1:8787
    python server.py --port 9000
    python server.py --dev           # /version enables auto-reload on HTML edits
"""
from __future__ import annotations

import argparse
import json
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import config
import push
from collector import Collector, HistoryStore

HERE = Path(__file__).parent
HTML = HERE / "claude-code-telemetry.html"
FONTS = HERE / "fonts"
CTYPES = {".ttf": "font/ttf", ".woff2": "font/woff2"}

_collector = Collector(history=HistoryStore(HERE / "history.db"))
_lock = threading.Lock()      # Collector is not thread-safe; handlers are threaded
DEV = False
HUB: dict = {}                # hub url/token when configured (empty = local only)
PUSH_EVERY_S = 120
UPSTREAM_TIMEOUT_S = 4


def _upstream_snapshot() -> dict:
    """Merged view from the hub; raises on any failure."""
    req = urllib.request.Request(HUB["url"] + "/api/telemetry",
                                 headers={"Authorization": "Bearer " + HUB["token"]})
    with urllib.request.urlopen(req, timeout=UPSTREAM_TIMEOUT_S) as r:
        snap = json.loads(r.read())
    if "error" in snap:
        raise ValueError(snap["error"])
    return snap


def _snapshot() -> dict:
    """Hub snapshot when configured; this machine's own logs if the hub is unreachable."""
    if HUB:
        try:
            return _upstream_snapshot()
        except (urllib.error.URLError, OSError, ValueError):
            with _lock:
                snap = _collector.snapshot()
            snap["source"] = "local-fallback"
            return snap
    with _lock:
        return _collector.snapshot()


def _push_loop() -> None:
    """Report this machine to the hub; failures are silent (the hub may be down)."""
    while True:
        try:
            with _lock:
                payload = _collector.payload()
            push.push(HUB, payload)
        except (urllib.error.URLError, OSError, ValueError):
            pass
        time.sleep(PUSH_EVERY_S)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args) -> None:  # quiet
        pass

    def _send(self, body: bytes, ctype: str, code: int = 200, cache: str = "no-store") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html", "/telemetry", "/claude-code-telemetry.html"):
            try:
                self._send(HTML.read_bytes(), "text/html; charset=utf-8")
            except OSError:
                self._send(b"claude-code-telemetry.html not found", "text/plain", 404)
        elif path.startswith("/fonts/"):
            f = FONTS / Path(path).name          # basename only: no path traversal
            if f.suffix in CTYPES and f.is_file():
                self._send(f.read_bytes(), CTYPES[f.suffix], cache="public, max-age=604800")
            else:
                self._send(b"not found", "text/plain", 404)
        elif path == "/version" and DEV:
            try:
                body = json.dumps({"mtime": HTML.stat().st_mtime}).encode("utf-8")
                self._send(body, "application/json")
            except OSError:
                self._send(b"{}", "application/json", 404)
        elif path == "/data.json":
            try:
                self._send(json.dumps(_snapshot()).encode("utf-8"), "application/json")
            except Exception as e:  # never kill the dashboard over one bad read
                self._send(json.dumps({"error": str(e)}).encode(), "application/json", 500)
        else:
            self._send(b"not found", "text/plain", 404)

    do_HEAD = do_GET


def main() -> int:
    global DEV
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--dev", action="store_true", help="enable /version (HTML auto-reload)")
    ap.add_argument("--no-hub", action="store_true", help="ignore config.json; local logs only")
    args = ap.parse_args()
    DEV = args.dev

    cfg = {} if args.no_hub else config.load()
    if cfg.get("url") and cfg.get("token"):
        HUB.update(url=cfg["url"], token=cfg["token"])
        if cfg.get("machine"):
            _collector.machine = cfg["machine"]
        threading.Thread(target=_push_loop, daemon=True).start()
        print(f"hub: {cfg['url']} (reporting as {_collector.machine})")

    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"serving dashboard on http://{args.host}:{args.port}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
