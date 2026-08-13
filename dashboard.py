"""Claude token dashboard for the Hosyond 5" 1024×600 color LCD.

Pillow composes each frame; pygame shows it full-screen on the external
monitor. The collector is re-sampled every --refresh seconds while animations
(Clawd bob/blink/jump, particles, halo) run at --fps.

Usage:
    python dashboard.py                      # full-screen on monitor 2 (display 1)
    python dashboard.py --display 0          # full-screen on the primary monitor
    python dashboard.py --windowed           # 1024×600 window on the primary (dev)
    python dashboard.py --png preview.png    # render one frame to PNG and exit
"""
from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path

from collector import Collector
from display import Display
from render import Renderer


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=15,
                    help="Target frames per second (default 15)")
    ap.add_argument("--refresh", type=float, default=1.0,
                    help="Seconds between collector snapshots (default 1.0)")
    ap.add_argument("--display", default="auto",
                    help="Monitor for full-screen: 'auto' (smallest screen) "
                         "or an index like 0/1/2 (default auto)")
    ap.add_argument("--windowed", action="store_true",
                    help="Run in a window on the primary monitor (dev)")
    ap.add_argument("--png", type=Path, default=None,
                    help="Render one frame to PNG and exit (local preview)")
    args = ap.parse_args()

    collector = Collector()
    renderer = Renderer()

    # ── one-shot PNG preview (no window / no pygame needed) ──────────
    if args.png:
        renderer.update_data(collector.snapshot())
        renderer.step(0.0)
        Display(png_out=args.png).show(renderer.frame())
        return 0

    disp = Display(display=args.display, windowed=args.windowed)

    running = True

    def stop(*_: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    frame_dt = 1.0 / max(1, args.fps)
    next_refresh = 0.0
    last = time.monotonic()

    try:
        while running:
            now = time.monotonic()
            dt = now - last
            last = now

            if now >= next_refresh:
                renderer.update_data(collector.snapshot())
                next_refresh = now + args.refresh

            renderer.step(dt)
            disp.show(renderer.frame())

            if not disp.pump():
                break

            # frame pacing
            sleep = frame_dt - (time.monotonic() - now)
            if sleep > 0:
                time.sleep(sleep)
    finally:
        disp.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
