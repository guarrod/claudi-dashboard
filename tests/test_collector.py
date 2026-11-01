import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import collector as C  # noqa: E402


def line(mid, rid, model, out, ts, inp=10, cr=0, cwd="C:\\x\\proj", cw=0):
    return json.dumps({
        "type": "assistant", "timestamp": ts.astimezone().isoformat(), "cwd": cwd,
        "requestId": rid,
        "message": {"id": mid, "model": model, "usage": {
            "input_tokens": inp, "output_tokens": out,
            "cache_read_input_tokens": cr, "cache_creation_input_tokens": cw}},
    }) + "\n"


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.now = datetime.now().astimezone().replace(hour=12, minute=0, second=0, microsecond=0)
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, *lines, mode="w"):
        with open(self.dir / name, mode, encoding="utf-8") as f:
            f.writelines(lines)

    def snap(self):
        return C.Collector(self.dir).snapshot(now=self.now)

    def test_dedup_same_message_within_and_across_files(self):
        t = self.now - timedelta(minutes=30)
        # streaming chunks (same id, growing output) + the resumed copy in another file
        self.write("a.jsonl",
                   line("m1", "r1", "claude-sonnet-5", 5, t),
                   line("m1", "r1", "claude-sonnet-5", 50, t))
        self.write("b.jsonl", line("m1", "r1", "claude-sonnet-5", 50, t))
        s = self.snap()
        self.assertEqual(s["out"], 50)          # last wins, counted once
        self.assertEqual(s["today_total"], 60)  # 10 in + 50 out

    def test_incremental_read_and_partial_line(self):
        t = self.now - timedelta(minutes=10)
        col = C.Collector(self.dir)
        full = line("m1", "r1", "claude-sonnet-5", 7, t)
        self.write("a.jsonl", full, line("m2", "r2", "claude-sonnet-5", 3, t)[:-15])  # half line
        self.assertEqual(col.snapshot(now=self.now)["out"], 7)
        self.write("a.jsonl", line("m2", "r2", "claude-sonnet-5", 3, t), mode="a")
        # the half line plus the new full line are now garbage-joined; the
        # collector must not crash and must still count the good ones
        self.assertGreaterEqual(col.snapshot(now=self.now)["out"], 7)

    def test_cache_not_in_primary_total(self):
        t = self.now - timedelta(minutes=5)
        self.write("a.jsonl", line("m1", "r1", "claude-sonnet-5", 20, t, inp=5, cr=100000))
        s = self.snap()
        self.assertEqual(s["today_total"], 25)
        self.assertEqual(s["cache_read"], 100000)

    def test_models_labels_and_unknown_family(self):
        self.assertEqual(C.model_label("claude-opus-4-8"), "Opus 4.8")
        self.assertEqual(C.model_label("claude-sonnet-5"), "Sonnet 5")
        self.assertEqual(C.model_label("claude-haiku-4-5-20251001"), "Haiku 4.5")
        self.assertEqual(C.model_label("claude-fable-5"), "Fable 5")
        self.assertEqual(C.model_label("claude-opus-4-20250514"), "Opus 4")
        self.assertIsNone(C.price_for("claude-fable-5"))     # never assume opus
        self.assertEqual(C.price_for("claude-opus-4-1")["in"], 15.0)
        self.assertEqual(C.price_for("claude-opus-4-8")["in"], 5.0)

    def test_unpriced_model_flags_partial_cost(self):
        t = self.now - timedelta(minutes=5)
        self.write("a.jsonl", line("m1", "r1", "claude-fable-5", 40, t))
        s = self.snap()
        self.assertTrue(s["cost_partial"])
        self.assertEqual(s["cost_day"], 0)
        self.assertEqual(s["mix"][0]["family"], "fable")

    def test_window_and_projects(self):
        self.write("a.jsonl",
                   line("m1", "r1", "claude-sonnet-5", 10, self.now - timedelta(hours=1), cwd="/a/alpha"),
                   line("m2", "r2", "claude-sonnet-5", 30, self.now - timedelta(minutes=2), cwd="/a/beta"))
        s = self.snap()
        self.assertTrue(s["window_active"])
        self.assertEqual(s["window_tokens"], 10 + 10 + 30 + 10)
        self.assertEqual(s["by_project"][0]["name"], "beta")

    def test_history_survives_purged_logs(self):
        db = C.HistoryStore(self.dir / "h.db")
        yday = self.now - timedelta(days=1)
        self.write("a.jsonl", line("m1", "r1", "claude-sonnet-5", 90, yday))
        C.Collector(self.dir, history=db).snapshot(now=self.now)
        (self.dir / "a.jsonl").unlink()                       # log purged
        s = C.Collector(self.dir, history=db).snapshot(now=self.now)
        self.assertEqual(s["daily"][-2]["io"], 100)


if __name__ == "__main__":
    unittest.main()
