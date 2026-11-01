"""Hub connection settings, shared by server.py and push.py.

Read from config.json (gitignored) next to this file; environment variables
override it. The token is never printed or committed.

    {"url": "https://guarrod.com/claude-hub", "token": "…", "machine": "MAC-01"}
"""
from __future__ import annotations

import json
import os
from pathlib import Path

HERE = Path(__file__).parent


def load() -> dict:
    cfg: dict = {}
    try:
        cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    for key, env in (("url", "CLAUDE_DASH_URL"), ("token", "CLAUDE_DASH_TOKEN"),
                     ("machine", "CLAUDE_DASH_MACHINE")):
        if os.environ.get(env):
            cfg[key] = os.environ[env]
    if cfg.get("url"):
        cfg["url"] = str(cfg["url"]).rstrip("/")
        if not cfg["url"].startswith("https://") and "127.0.0.1" not in cfg["url"] \
                and "localhost" not in cfg["url"]:
            raise SystemExit("config: url must be https:// (the token travels in a header)")
    return cfg
