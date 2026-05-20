"""Reads ~/.claude/projects/**/*.jsonl and produces dashboard snapshots.

The "current session" is whichever JSONL file was most recently modified.
"Today" aggregates every assistant turn whose timestamp falls within the
current UTC day.
"""

from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _claude_config_dir() -> Path:
    """Respect CLAUDE_CONFIG_DIR if set, else fall back to ~/.claude."""
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(env).expanduser() if env else Path.home() / ".claude"


CLAUDE_HOME = _claude_config_dir()
CLAUDE_DIR = CLAUDE_HOME / "projects"
HISTORY_FILE = CLAUDE_HOME / "history.jsonl"

# Approximate Anthropic pricing in USD per 1M tokens for the Claude 4.x family.
# Cache-write tiers correspond to the 5-minute and 1-hour ephemeral cache.
PRICING = {
    "opus":   {"in": 15.0, "out": 75.0, "cache_read": 1.50, "cache_w_5m": 18.75, "cache_w_1h": 30.0},
    "sonnet": {"in":  3.0, "out": 15.0, "cache_read": 0.30, "cache_w_5m":  3.75, "cache_w_1h":  6.0},
    "haiku":  {"in":  1.0, "out":  5.0, "cache_read": 0.10, "cache_w_5m":  1.25, "cache_w_1h":  2.0},
}


def model_family(model_id: Optional[str]) -> str:
    if not model_id:
        return "opus"
    m = model_id.lower()
    if "opus" in m: return "opus"
    if "sonnet" in m: return "sonnet"
    if "haiku" in m: return "haiku"
    return "opus"


def estimate_cost(usage: dict, model: Optional[str]) -> float:
    p = PRICING[model_family(model)]
    cache = usage.get("cache_creation") or {}
    c5m = cache.get("ephemeral_5m_input_tokens", 0)
    c1h = cache.get("ephemeral_1h_input_tokens", 0)
    return (
        usage.get("input_tokens", 0)            * p["in"]         / 1_000_000
        + usage.get("output_tokens", 0)         * p["out"]        / 1_000_000
        + usage.get("cache_read_input_tokens", 0) * p["cache_read"] / 1_000_000
        + c5m * p["cache_w_5m"] / 1_000_000
        + c1h * p["cache_w_1h"] / 1_000_000
    )


@dataclass
class Record:
    ts: float
    session: Optional[str]
    model: Optional[str]
    usage: dict
    path: str


@dataclass
class Snapshot:
    session: dict
    today: dict
    sparkline: list[int] = field(default_factory=list)
    now: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_prompt_age: float = 0.0  # seconds since user's last prompt (None if unknown)


def _read_latest_history_entry() -> Optional[dict]:
    """Return the last line of history.jsonl, parsed.

    history.jsonl is the global, append-only log of every prompt the user
    sent to Claude Code, with `sessionId`, `project`, `timestamp` (ms).
    The last line is the source of truth for "which session is the user
    actually talking to right now".
    """
    if not HISTORY_FILE.exists():
        return None
    try:
        # Tail the file efficiently by seeking from the end
        with open(HISTORY_FILE, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = 4096
            data = b""
            while size > 0 and data.count(b"\n") < 2:
                step = min(block, size)
                size -= step
                f.seek(size)
                data = f.read(step) + data
            last = data.rstrip(b"\n").split(b"\n")[-1]
        return json.loads(last.decode("utf-8", errors="replace"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None


def _resolve_active_session() -> tuple[Optional[str], Optional[float], Optional[str]]:
    """Return (session_id, prompt_ts_seconds, project_path) of the active
    Claude Code session, or (None, None, None) if it can't be determined.
    """
    entry = _read_latest_history_entry()
    if not entry:
        return None, None, None
    sid = entry.get("sessionId")
    ts_ms = entry.get("timestamp")
    try:
        ts_s = float(ts_ms) / 1000.0 if ts_ms is not None else None
    except (TypeError, ValueError):
        ts_s = None
    return sid, ts_s, entry.get("project")


class Collector:
    """Re-parses any JSONL whose mtime changed; otherwise reuses cached records."""

    def __init__(self) -> None:
        self._mtime: dict[str, float] = {}
        self._records: dict[str, list[Record]] = {}

    def refresh(self) -> None:
        paths = glob.glob(str(CLAUDE_DIR / "**" / "*.jsonl"), recursive=True)
        # drop files that disappeared
        for stale in [p for p in self._mtime if p not in set(paths)]:
            self._mtime.pop(stale, None)
            self._records.pop(stale, None)

        for path in paths:
            try:
                mt = os.stat(path).st_mtime
            except FileNotFoundError:
                continue
            if self._mtime.get(path) == mt:
                continue
            self._mtime[path] = mt
            self._records[path] = self._parse(path)

    def _parse(self, path: str) -> list[Record]:
        out: list[Record] = []
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if d.get("type") != "assistant":
                        continue
                    msg = d.get("message") or {}
                    usage = msg.get("usage")
                    if not usage:
                        continue
                    ts_str = d.get("timestamp") or ""
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
                    except ValueError:
                        ts = 0.0
                    out.append(Record(
                        ts=ts,
                        session=d.get("sessionId"),
                        model=msg.get("model"),
                        usage=usage,
                        path=path,
                    ))
        except FileNotFoundError:
            pass
        return out

    def snapshot(self) -> Snapshot:
        self.refresh()
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc).timestamp()
        now_epoch = now.timestamp()

        # Authoritative active-session lookup via global history.jsonl
        active_sid, prompt_ts, _proj = _resolve_active_session()

        latest_path = None
        if active_sid:
            for p in self._mtime:
                if Path(p).stem == active_sid:
                    latest_path = p
                    break

        # Fall back to most-recently-modified JSONL if history wasn't useful
        if latest_path is None and self._mtime:
            latest_path = max(self._mtime, key=self._mtime.get)

        latest_mtime = self._mtime.get(latest_path, 0) if latest_path else 0
        last_prompt_age = (now_epoch - prompt_ts) if prompt_ts else 0.0

        sess = {"id": None, "model": None, "tier": None,
                "input": 0, "output": 0, "cache_read": 0, "cache_write": 0,
                "total": 0, "cost": 0.0, "path": latest_path, "last_mtime": latest_mtime}
        today = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0,
                 "total": 0, "cost": 0.0, "messages": 0}
        spark = [0] * 30
        spark_window = 30 * 60

        for path, recs in self._records.items():
            for r in recs:
                u = r.usage
                inp = u.get("input_tokens", 0)
                outp = u.get("output_tokens", 0)
                cr = u.get("cache_read_input_tokens", 0)
                cw = u.get("cache_creation_input_tokens", 0)
                total = inp + outp + cr + cw
                cost = estimate_cost(u, r.model)

                if path == latest_path:
                    sess["input"]       += inp
                    sess["output"]      += outp
                    sess["cache_read"]  += cr
                    sess["cache_write"] += cw
                    sess["total"]       += total
                    sess["cost"]        += cost
                    if r.model: sess["model"] = r.model
                    if u.get("service_tier"): sess["tier"] = u["service_tier"]
                    if r.session: sess["id"] = r.session

                if r.ts >= today_start:
                    today["input"]       += inp
                    today["output"]      += outp
                    today["cache_read"]  += cr
                    today["cache_write"] += cw
                    today["total"]       += total
                    today["cost"]        += cost
                    today["messages"]    += 1

                delta = now_epoch - r.ts
                if 0 <= delta < spark_window:
                    idx = 29 - int(delta // 60)
                    if 0 <= idx < 30:
                        spark[idx] += total

        # Ensure session id reflects the authoritative lookup even if the
        # JSONL hasn't been written to yet (e.g. brand-new session).
        if active_sid:
            sess["id"] = active_sid

        return Snapshot(session=sess, today=today, sparkline=spark, now=now,
                        last_prompt_age=last_prompt_age)


if __name__ == "__main__":
    c = Collector()
    s = c.snapshot()
    print("session:", s.session)
    print("today:  ", s.today)
    print("spark:  ", s.sparkline)
