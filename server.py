"""Tiny local server for the HTML telemetry dashboard.

Serves dashboard.html at /  and live data at /data.json (real Claude Code
usage from collector.Collector). No external dependencies — stdlib only.

    python server.py                 # http://127.0.0.1:8787
    python server.py --port 9000
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from collector import Collector

HERE = Path(__file__).parent
HTML = HERE / "dashboard.html"
TELEMETRY = HERE / "claude-code-telemetry.html"   # sci-fi HUD variant

_collector = Collector()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args) -> None:  # quiet
        pass

    def _send(self, body: bytes, ctype: str, code: int = 200) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html", "/dashboard.html"):
            try:
                self._send(HTML.read_bytes(), "text/html; charset=utf-8")
            except OSError:
                self._send(b"dashboard.html not found", "text/plain", 404)
        elif path in ("/telemetry", "/claude-code-telemetry.html"):
            try:
                self._send(TELEMETRY.read_bytes(), "text/html; charset=utf-8")
            except OSError:
                self._send(b"claude-code-telemetry.html not found", "text/plain", 404)
        elif path == "/version":
            # mtime del HTML para auto-reload al editar el UI. ?f=telemetry
            # apunta al HUD sci-fi; por defecto, dashboard.html.
            target = TELEMETRY if "f=telemetry" in self.path else HTML
            try:
                body = json.dumps({"mtime": target.stat().st_mtime}).encode("utf-8")
                self._send(body, "application/json")
            except OSError:
                self._send(b"{}", "application/json", 404)
        elif path == "/data.json":
            try:
                body = json.dumps(_collector.web_snapshot()).encode("utf-8")
                self._send(body, "application/json")
            except Exception as e:  # never kill the dashboard over one bad read
                self._send(json.dumps({"error": str(e)}).encode(), "application/json", 500)
        else:
            self._send(b"not found", "text/plain", 404)

    do_HEAD = do_GET


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    args = ap.parse_args()

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
