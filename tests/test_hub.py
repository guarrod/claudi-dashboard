import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import collector as C  # noqa: E402
import hub as H  # noqa: E402
import push as P  # noqa: E402
from test_collector import line  # noqa: E402

TOKEN = "t" * 32


class HubTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.now = datetime.now().astimezone()   # the hub snapshots at real time
        self.hub = H.Hub(self.root / "hub")
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), H.make_handler(self.hub, TOKEN))
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.cfg = {"url": f"http://127.0.0.1:{self.srv.server_address[1]}", "token": TOKEN}

    def machine(self, name, *lines):
        d = self.root / name
        d.mkdir()
        (d / "a.jsonl").write_text("".join(lines), encoding="utf-8")
        return C.Collector(d, machine=name)

    def get(self, path, token=TOKEN):
        req = urllib.request.Request(self.cfg["url"] + path,
                                     headers={"Authorization": f"Bearer {token}"} if token else {})
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())

    def test_two_machines_merge_and_window_is_per_account(self):
        # Mac opens the window 40 min ago; Windows works now. One account window.
        mac = self.machine("MAC", line("m1", "r1", "claude-sonnet-5", 100, self.now - timedelta(minutes=40)))
        win = self.machine("WIN", line("m2", "r2", "claude-opus-4-8", 50, self.now - timedelta(minutes=1)))
        P.push(self.cfg, mac.payload())
        P.push(self.cfg, win.payload())
        s = self.get("/api/telemetry")
        self.assertEqual(s["source"], "hub")
        self.assertEqual({n["name"] for n in s["nodes"]}, {"MAC", "WIN"})
        self.assertEqual(s["today_total"], 110 + 60)
        self.assertTrue(s["window_active"])
        self.assertEqual(s["window_tokens"], 110 + 60)       # both machines inside the same 5h window
        self.assertEqual({m["family"] for m in s["mix"]}, {"sonnet", "opus"})

    def test_same_message_on_two_machines_counts_once(self):
        t = self.now - timedelta(minutes=5)
        a = self.machine("A", line("m1", "r1", "claude-sonnet-5", 40, t))
        b = self.machine("B", line("m1", "r1", "claude-sonnet-5", 40, t))
        P.push(self.cfg, a.payload())
        P.push(self.cfg, b.payload())
        self.assertEqual(self.get("/api/telemetry")["today_total"], 50)

    def test_silent_machine_goes_offline(self):
        a = self.machine("A", line("m1", "r1", "claude-sonnet-5", 5, self.now - timedelta(minutes=5)))
        P.push(self.cfg, a.payload())
        self.hub.machines["A"]["reported_at"] -= 3600
        n = self.get("/api/telemetry")["nodes"][0]
        self.assertFalse(n["online"])
        self.assertFalse(n["active"])

    def test_auth_required(self):
        for tok in (None, "wrong" * 8):
            with self.assertRaises(urllib.error.HTTPError) as cm:
                self.get("/api/telemetry", token=tok)
            self.assertEqual(cm.exception.code, 401)
        with self.assertRaises(urllib.error.HTTPError) as cm:
            P.push({**self.cfg, "token": "x" * 32}, {"machine": "A", "records": []})
        self.assertEqual(cm.exception.code, 401)
        self.assertEqual(self.get("/healthz", token=None), {"ok": True})   # no data, no auth

    def test_rejects_bad_payloads(self):
        good = ["k", 1.0, "claude-sonnet-5", 1, 1, 0, 0, 0, "/x"]
        bad = [
            {"machine": "../evil", "records": []},                  # path traversal in name
            {"machine": "A", "records": "nope"},
            {"machine": "A", "records": [good[:5]]},                # short row
            {"machine": "A", "records": [good[:3] + [-1] + good[4:]]},   # negative number
            {"machine": "A", "records": [good[:3] + ["1"] + good[4:]]},  # string number
        ]
        for payload in bad:
            with self.assertRaises(urllib.error.HTTPError, msg=str(payload)) as cm:
                P.push(self.cfg, payload)
            self.assertEqual(cm.exception.code, 400)
        self.assertEqual(self.hub.machines, {})
        P.push(self.cfg, {"machine": "A", "records": [good]})
        self.assertIn("A", self.hub.machines)

    def test_machine_limit(self):
        for i in range(H.MAX_MACHINES):
            P.push(self.cfg, {"machine": f"M{i}", "records": []})
        with self.assertRaises(urllib.error.HTTPError) as cm:
            P.push(self.cfg, {"machine": "ONE-TOO-MANY", "records": []})
        self.assertEqual(cm.exception.code, 400)

    def test_restart_keeps_reports(self):
        a = self.machine("A", line("m1", "r1", "claude-sonnet-5", 5, self.now - timedelta(minutes=5)))
        P.push(self.cfg, a.payload())
        reborn = H.Hub(self.root / "hub")
        self.assertEqual(len(reborn.machines["A"]["records"]), 1)


if __name__ == "__main__":
    unittest.main()
