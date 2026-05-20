"""Claude token dashboard for Waveshare 2.9" Touch e-Paper HAT.

Reads Claude Code session data from ~/.claude/projects and does a full
display refresh every --refresh seconds (default 30).

Usage:
    python dashboard.py                   # run on Pi (needs waveshare_epd)
    python dashboard.py --png preview.png # render one frame locally and exit
    python dashboard.py --refresh 60      # slower refresh to extend display life
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path

from collector import Collector
from epd_driver import EPDDriver
from render import build_frame


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", type=float, default=30.0,
                    help="Seconds between display refreshes (default 30)")
    ap.add_argument("--png", type=Path, default=None,
                    help="Render one frame to PNG and exit (local preview)")
    args = ap.parse_args()

    collector = Collector()
    driver = EPDDriver(png_out=args.png)

    if args.png:
        snap = collector.snapshot()
        driver.display(build_frame(snap))
        return 0

    driver.init()
    running = True

    def stop(*_: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    try:
        while running:
            snap = collector.snapshot()
            driver.display(build_frame(snap))
            deadline = time.monotonic() + args.refresh
            while running and time.monotonic() < deadline:
                time.sleep(1.0)
    finally:
        driver.sleep()

    return 0


if __name__ == "__main__":
    sys.exit(main())
