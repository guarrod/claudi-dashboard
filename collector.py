"""Reads ~/.claude/projects/**/*.jsonl and aggregates Claude Code usage.

Design notes
  * Claude Code writes the same API message several times (streaming chunks,
    resumed sessions copy history into new files). Records are de-duplicated
    on (message.id, requestId); the LAST line seen wins, since it carries the
    final usage numbers.
  * JSONL files are append-only, so each file is read incrementally from the
    byte offset where the previous read stopped.
  * "Work" tokens = input + output. Cache tokens are reported separately
    (they are ~95 % of the raw total and say little about actual work).
  * All day / hour bucketing uses LOCAL time so it matches the on-screen clock.
  * Dollar figures are API-rate equivalents (computed), never a bill. Models
    with no known price are left out of the sum and flagged (`cost_partial`).
  * Several machines can be merged: each reports its Records to a hub, and
    `build_snapshot` aggregates over the union (see hub.py / push.py).
"""

from __future__ import annotations

import glob
import json
import os
import platform
import re
import socket
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

HERE = Path(__file__).parent


def _claude_config_dir() -> Path:
    """Respect CLAUDE_CONFIG_DIR if set, else fall back to ~/.claude."""
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(env).expanduser() if env else Path.home() / ".claude"


CLAUDE_HOME = _claude_config_dir()
CLAUDE_DIR = CLAUDE_HOME / "projects"
HISTORY_FILE = CLAUDE_HOME / "history.jsonl"

# ── models ───────────────────────────────────────────────────────────
# USD per 1M tokens. Cache write tiers = 5-minute and 1-hour ephemeral cache.
_P_OPUS_LEGACY = {"in": 15.0, "out": 75.0, "cache_read": 1.50, "cache_w_5m": 18.75, "cache_w_1h": 30.0}
_P_OPUS        = {"in":  5.0, "out": 25.0, "cache_read": 0.50, "cache_w_5m":  6.25, "cache_w_1h": 10.0}
_P_SONNET      = {"in":  3.0, "out": 15.0, "cache_read": 0.30, "cache_w_5m":  3.75, "cache_w_1h":  6.0}
_P_HAIKU       = {"in":  1.0, "out":  5.0, "cache_read": 0.10, "cache_w_5m":  1.25, "cache_w_1h":  2.0}

_FAMILY_RE = re.compile(r"(opus|sonnet|haiku|fable)", re.I)
_VERSION_RE = re.compile(r"(?:opus|sonnet|haiku|fable)-(\d+)(?:-(\d{1,2})(?!\d))?", re.I)
_LEGACY_OPUS_RE = re.compile(r"opus-4(?:-[01])?(?:-\d{8})?$|3-opus", re.I)


def model_family(model_id: Optional[str]) -> Optional[str]:
    """'opus' | 'sonnet' | 'haiku' | 'fable' | other family name | None."""
    if not model_id:
        return None
    m = _FAMILY_RE.search(model_id)
    return m.group(1).lower() if m else None


def model_label(model_id: Optional[str]) -> str:
    """Human label derived from the real id: 'claude-opus-4-8' -> 'Opus 4.8'."""
    fam = model_family(model_id)
    if not fam:
        return (model_id or "—")[:14]
    v = _VERSION_RE.search(model_id)
    if not v:
        return fam.title()
    minor = v.group(2)
    return f"{fam.title()} {v.group(1)}" + (f".{minor}" if minor else "")


def price_for(model_id: Optional[str]) -> Optional[dict]:
    """Price table for a model, or None when the price is unknown."""
    fam = model_family(model_id)
    if fam == "opus":
        return _P_OPUS_LEGACY if _LEGACY_OPUS_RE.search(model_id) else _P_OPUS
    if fam == "sonnet":
        return _P_SONNET
    if fam == "haiku":
        return _P_HAIKU
    return None  # fable / unknown: no published price we trust


def cost_of(inp: int, out: int, cache_read: int, c5m: int, c1h: int,
            model: Optional[str]) -> Optional[float]:
    p = price_for(model)
    if p is None:
        return None
    return (
        inp * p["in"] / 1_000_000
        + out * p["out"] / 1_000_000
        + cache_read * p["cache_read"] / 1_000_000
        + c5m * p["cache_w_5m"] / 1_000_000
        + c1h * p["cache_w_1h"] / 1_000_000
    )


def cache_tiers(usage: dict) -> tuple[int, int]:
    """(5m, 1h) cache-write tokens; older logs only have the aggregate (-> 5m)."""
    cache = usage.get("cache_creation") or {}
    c5m = cache.get("ephemeral_5m_input_tokens", 0) or 0
    c1h = cache.get("ephemeral_1h_input_tokens", 0) or 0
    if not (c5m or c1h):
        c5m = usage.get("cache_creation_input_tokens", 0) or 0
    return c5m, c1h


def estimate_cost(usage: dict, model: Optional[str]) -> Optional[float]:
    c5m, c1h = cache_tiers(usage)
    return cost_of(usage.get("input_tokens", 0), usage.get("output_tokens", 0),
                   usage.get("cache_read_input_tokens", 0), c5m, c1h, model)


def project_name(cwd: Optional[str]) -> str:
    """Friendly project label = basename of the working directory."""
    if not cwd:
        return "—"
    norm = cwd.replace("\\", "/").rstrip("/")
    return norm.rsplit("/", 1)[-1] or norm


# ── records ──────────────────────────────────────────────────────────
@dataclass
class Record:
    key: str                # de-dup key: "<message.id>|<requestId>" (or file position)
    ts: float
    model: Optional[str]
    inp: int
    out: int
    cache_read: int
    c5m: int                # cache-write tokens, 5-minute tier
    c1h: int                # cache-write tokens, 1-hour tier
    cwd: Optional[str]
    machine: str = ""

    @property
    def io(self) -> int:
        return self.inp + self.out

    @property
    def cache_write(self) -> int:
        return self.c5m + self.c1h

    @property
    def cache(self) -> int:
        return self.cache_read + self.cache_write

    @property
    def cost(self) -> Optional[float]:
        """None = model without a known price. Priced at aggregation time, so a
        price-table update on the hub applies to every machine's history."""
        return cost_of(self.inp, self.out, self.cache_read, self.c5m, self.c1h, self.model)

    def to_wire(self) -> list:
        return [self.key, self.ts, self.model, self.inp, self.out,
                self.cache_read, self.c5m, self.c1h, self.cwd]

    @classmethod
    def from_wire(cls, row: list, machine: str) -> "Record":
        """Validating constructor for rows received over the network."""
        key, ts, model, inp, out, cr, c5m, c1h, cwd = row
        if not isinstance(key, str) or len(key) > 300:
            raise ValueError("bad key")
        nums = (ts, inp, out, cr, c5m, c1h)
        if not all(isinstance(n, (int, float)) and not isinstance(n, bool) and n >= 0 for n in nums):
            raise ValueError("bad number")
        if model is not None and not isinstance(model, str):
            raise ValueError("bad model")
        if cwd is not None and not isinstance(cwd, str):
            raise ValueError("bad cwd")
        return cls(key, float(ts), model and model[:80], int(inp), int(out), int(cr),
                   int(c5m), int(c1h), cwd and cwd[:300], machine)


def _tail_json_line(path: Path) -> Optional[dict]:
    """Last JSON line of a file, reading from the end."""
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            data = b""
            while size > 0 and data.count(b"\n") < 2:
                step = min(4096, size)
                size -= step
                f.seek(size)
                data = f.read(step) + data
        return json.loads(data.rstrip(b"\n").split(b"\n")[-1].decode("utf-8", errors="replace"))
    except (OSError, ValueError):
        return None


def last_prompt_ts() -> Optional[float]:
    """Epoch seconds of the user's most recent prompt (history.jsonl)."""
    entry = _tail_json_line(HISTORY_FILE) if HISTORY_FILE.exists() else None
    try:
        return float(entry["timestamp"]) / 1000.0 if entry else None
    except (KeyError, TypeError, ValueError):
        return None


# ── persisted daily history ──────────────────────────────────────────
class HistoryStore:
    """Daily aggregates in SQLite so history survives log purges."""

    def __init__(self, path: Path | str) -> None:
        self.path = str(path)
        with self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS daily (
                day TEXT PRIMARY KEY, io INTEGER, cache INTEGER,
                cost REAL, msgs INTEGER)""")

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=5)

    def save(self, days: dict[str, dict]) -> None:
        """Upsert; never lower a day (the oldest day may be partially purged)."""
        try:
            with self._conn() as c:
                for day, d in days.items():
                    c.execute(
                        """INSERT INTO daily(day, io, cache, cost, msgs) VALUES (?,?,?,?,?)
                           ON CONFLICT(day) DO UPDATE SET io=excluded.io, cache=excluded.cache,
                             cost=excluded.cost, msgs=excluded.msgs
                           WHERE excluded.io >= daily.io""",
                        (day, d["io"], d["cache"], d["cost"], d["msgs"]))
        except sqlite3.Error:
            pass  # history is a bonus; never break the dashboard over it

    def load(self, since: str) -> dict[str, dict]:
        try:
            with self._conn() as c:
                rows = c.execute(
                    "SELECT day, io, cache, cost, msgs FROM daily WHERE day >= ?", (since,)).fetchall()
        except sqlite3.Error:
            return {}
        return {r[0]: {"io": r[1], "cache": r[2], "cost": r[3], "msgs": r[4]} for r in rows}


# ── collector (reads this machine's logs) ────────────────────────────
class Collector:
    """Incremental, de-duplicating reader of Claude Code transcripts."""

    SAVE_EVERY_S = 60

    def __init__(self, claude_dir: Path | str | None = None,
                 history: HistoryStore | None = None, machine: str | None = None) -> None:
        self.dir = Path(claude_dir) if claude_dir else CLAUDE_DIR
        self.history = history
        self.machine = machine or socket.gethostname().split(".")[0].upper()
        self._offset: dict[str, int] = {}
        self._records: dict[str, Record] = {}
        self._last_save = 0.0

    # -- reading --
    def refresh(self) -> None:
        for path in glob.glob(str(self.dir / "**" / "*.jsonl"), recursive=True):
            try:
                size = os.stat(path).st_size
            except OSError:
                continue
            start = self._offset.get(path, 0)
            if size < start:      # truncated / rewritten: read again from zero
                start = 0
            if size == start:
                continue
            self._offset[path] = start + self._read_from(path, start)

    def _read_from(self, path: str, start: int) -> int:
        """Parse complete lines from `start`; return bytes consumed."""
        consumed = 0
        try:
            with open(path, "rb") as f:
                f.seek(start)
                for raw in f:
                    if not raw.endswith(b"\n"):
                        break     # half-written line: pick it up next time
                    pos = start + consumed
                    consumed += len(raw)
                    self._ingest(raw, path, pos)
        except OSError:
            pass
        return consumed

    def _ingest(self, raw: bytes, path: str, pos: int) -> None:
        try:
            d = json.loads(raw)
        except ValueError:
            return
        if d.get("type") != "assistant":
            return
        msg = d.get("message") or {}
        usage = msg.get("usage")
        model = msg.get("model")
        if not usage or model == "<synthetic>":
            return
        try:
            ts = datetime.fromisoformat((d.get("timestamp") or "").replace("Z", "+00:00")).timestamp()
        except ValueError:
            return
        mid, rid = msg.get("id"), d.get("requestId")
        key = f"{mid}|{rid}" if mid else f"{self.machine}|{path}|{pos}"
        prev = self._records.get(key)
        c5m, c1h = cache_tiers(usage)
        self._records[key] = Record(
            key=key,
            ts=prev.ts if prev else ts,    # keep the first timestamp
            model=model,
            inp=usage.get("input_tokens", 0) or 0,
            out=usage.get("output_tokens", 0) or 0,
            cache_read=usage.get("cache_read_input_tokens", 0) or 0,
            c5m=c5m, c1h=c1h,
            cwd=d.get("cwd"),
            machine=self.machine,
        )

    # -- outputs --
    def source(self) -> dict:
        """This machine as an aggregation source."""
        self.refresh()
        return {"name": self.machine, "os": platform.system(),
                "records": list(self._records.values()),
                "last_prompt": last_prompt_ts(), "reported_at": None}

    def snapshot(self, now: Optional[datetime] = None) -> dict:
        save = False
        t = time.time()
        if self.history is not None and t - self._last_save >= self.SAVE_EVERY_S:
            save, self._last_save = True, t
        return build_snapshot([self.source()], now, self.history, save)

    def payload(self, days: int = 32) -> dict:
        """What this machine reports to the hub: its recent records."""
        src = self.source()
        cutoff = time.time() - days * 86400
        return {"machine": self.machine, "os": src["os"], "sent_at": time.time(),
                "last_prompt": src["last_prompt"],
                "records": [r.to_wire() for r in src["records"] if r.ts >= cutoff]}


# ── aggregation (local logs and/or machines reported to a hub) ───────
WINDOW_S = 5 * 3600
BURN_WINDOW_S = 5 * 60
ACTIVE_S = 120          # a machine counts as "active" if it prompted within this long
OFFLINE_S = 600         # a remote machine silent for this long is offline


def build_snapshot(sources: list[dict], now: Optional[datetime] = None,
                   history: HistoryStore | None = None, save_history: bool = False) -> dict:
    """Merge one or more machines into everything the HTML dashboard needs.

    Each source: {name, os, records: [Record], last_prompt, reported_at}.
    The 5h window, day totals and mix are computed over the UNION of records
    (de-duplicated by key), so the window is per account, not per machine.
    """
    now = now or datetime.now().astimezone()
    tz = now.tzinfo
    now_epoch = now.timestamp()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start = midnight.timestamp()
    week_start = (midnight - timedelta(days=6)).timestamp()
    month_start = midnight.replace(day=1).timestamp()

    merged: dict[str, Record] = {}
    for s in sources:
        for r in s["records"]:
            merged.setdefault(r.key, r)
    recs = list(merged.values())

    # Rolling 5h window anchored on the first message of the active window
    # (resets from first activity, not on a clock-aligned bucket).
    anchor = None
    for ts in sorted(r.ts for r in recs):
        if anchor is None or ts >= anchor + WINDOW_S:
            anchor = ts
    window_active = anchor is not None and now_epoch < anchor + WINDOW_S
    window_start = anchor if window_active else float("inf")

    c = {k: 0.0 for k in ("cost_day", "week_cost", "month_cost", "window_cost")}
    in_t = out_t = cr_t = cw_t = window_io = window_cache = burn_io = 0
    unpriced_today = 0
    hourly = [0] * 24
    fam_io: dict[str, int] = {}
    fam_model: dict[str, tuple[float, str]] = {}    # family -> (ts, newest model id)
    proj: dict[str, int] = {}
    days: dict[str, dict] = {}
    node_io: dict[str, int] = {}
    node_latest: dict[str, float] = {}
    latest_ts, latest_model = 0.0, None

    for r in recs:
        cost_r = r.cost
        cost = cost_r or 0.0
        day = datetime.fromtimestamp(r.ts, tz).strftime("%Y-%m-%d")
        dd = days.setdefault(day, {"io": 0, "cache": 0, "cost": 0.0, "msgs": 0})
        dd["io"] += r.io; dd["cache"] += r.cache; dd["cost"] += cost; dd["msgs"] += 1
        node_latest[r.machine] = max(node_latest.get(r.machine, 0.0), r.ts)

        if r.ts >= month_start:
            c["month_cost"] += cost
        if r.ts >= week_start:
            c["week_cost"] += cost
            p = project_name(r.cwd)
            proj[p] = proj.get(p, 0) + r.io
        if r.ts >= window_start:
            c["window_cost"] += cost
            window_io += r.io
            window_cache += r.cache
        if r.ts >= today_start:
            in_t += r.inp; out_t += r.out; cr_t += r.cache_read; cw_t += r.cache_write
            c["cost_day"] += cost
            if cost_r is None:
                unpriced_today += r.io
            hourly[datetime.fromtimestamp(r.ts, tz).hour] += r.io
            node_io[r.machine] = node_io.get(r.machine, 0) + r.io
            fam = model_family(r.model) or "otro"
            fam_io[fam] = fam_io.get(fam, 0) + r.io
            if r.ts >= fam_model.get(fam, (0, ""))[0]:
                fam_model[fam] = (r.ts, r.model or "")
        if now_epoch - r.ts <= BURN_WINDOW_S:
            burn_io += r.io
        if r.ts > latest_ts:
            latest_ts, latest_model = r.ts, r.model

    # persisted history (survives log purges) merged with what logs show now
    if history is not None:
        if save_history:
            history.save(days)
        stored = history.load((midnight - timedelta(days=6)).strftime("%Y-%m-%d"))
        for day, d in stored.items():
            if day not in days or d["io"] > days[day]["io"]:
                days[day] = d
    series = []
    for k in range(6, -1, -1):
        dkey = (midnight - timedelta(days=k)).strftime("%Y-%m-%d")
        series.append({"date": dkey, "io": days.get(dkey, {}).get("io", 0)})

    today_io = in_t + out_t
    base = [d_["io"] for d_ in series[:-1]]
    base_avg = sum(base) / len(base) if base else 0
    vs_7d = round((today_io - base_avg) / base_avg * 100) if base_avg > 0 else None

    mix_total = sum(fam_io.values()) or 1
    mix = [{"family": f, "label": model_label(fam_model[f][1]) if f in fam_model else f.title(),
            "tokens": t, "frac": round(t / mix_total, 4)}
           for f, t in sorted(fam_io.items(), key=lambda kv: kv[1], reverse=True)]

    nodes = []
    for s in sources:
        name = s["name"]
        newest = node_latest.get(name, 0.0)
        reported = s.get("reported_at")
        online = reported is None or now_epoch - reported < OFFLINE_S
        recent = max(s.get("last_prompt") or 0.0, newest)
        nodes.append({
            "name": name, "os": s["os"],
            "tokens": int(node_io.get(name, 0)),
            "last_min": int((now_epoch - recent) / 60) if recent else None,
            "active": online and recent > 0 and now_epoch - recent < ACTIVE_S,
            "online": online,
            "report_min": None if reported is None else int((now_epoch - reported) / 60),
        })
    nodes.sort(key=lambda n: n["tokens"], reverse=True)

    return {
        "generated_at": now_epoch,
        "clock": now.strftime("%H:%M"),
        "model": model_label(latest_model),
        "active": any(n["active"] for n in nodes),
        "window_active": window_active,
        "reset_min": int((anchor + WINDOW_S - now_epoch) / 60) if window_active else 0,
        "window_id": int(anchor) if window_active else 0,
        "window_elapsed": round(min((now_epoch - anchor) / WINDOW_S, 1.0), 4) if window_active else 0.0,
        "window_start": datetime.fromtimestamp(anchor, tz).strftime("%H:%M") if window_active else None,
        "window_tokens": int(window_io),                 # R — input + output in the window
        "window_cache": int(window_cache),               # R
        "window_cost": round(c["window_cost"], 4),       # C — API-rate equivalent
        "cost_day": round(c["cost_day"], 4),             # C
        "week_cost": round(c["week_cost"], 4),           # C
        "month_cost": round(c["month_cost"], 4),         # C
        "cost_partial": unpriced_today > 0,              # some tokens had no known price
        "burn": round(burn_io / (BURN_WINDOW_S / 60.0)),   # R — work tok/min, last 5 min
        "in": int(in_t), "out": int(out_t),
        "cache": int(cr_t + cw_t), "cache_read": int(cr_t),
        "hourly": hourly,
        "cur_hour": now.hour,
        "mix": mix,                                      # R — by model family, today
        "today_total": int(today_io),                    # R — input + output today
        "vs_7d_avg_pct": vs_7d,                          # C
        "daily": series,                                 # R — 7 days, persisted
        "week_total": sum(d_["io"] for d_ in series),
        "by_project": sorted(({"name": n, "tokens": t} for n, t in proj.items()),
                             key=lambda p: p["tokens"], reverse=True)[:5],
        "nodes": nodes,                                  # R — one entry per machine
        "source": "local",                               # overwritten by hub / upstream
    }


if __name__ == "__main__":
    t0 = time.time()
    snap = Collector(history=HistoryStore(HERE / "history.db")).snapshot()
    print(json.dumps(snap, indent=2, default=str))
    print(f"-- {time.time() - t0:.2f}s")
