"""Claude live dashboard for Waveshare 3.5" SPI LCD.

Reads Claude Code session data from ~/.claude/projects, animates the metrics
and writes RGB565 frames to /dev/fb1 at ~15 fps.
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path

from PIL import Image

import theme as T
from collector import Collector
from render import AnimState, build_frame, build_static_base, static_key, to_rgb565_le


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=float, default=15.0)
    ap.add_argument("--refresh", type=float, default=1.0,
                    help="Seconds between collector refreshes")
    ap.add_argument("--png", type=Path, default=None,
                    help="Render one frame to this PNG path and exit")
    ap.add_argument("--device", type=Path, default=T.FB_DEV,
                    help="Framebuffer device path (default: /dev/fb1)")
    args = ap.parse_args()

    collector = Collector()
    anim = AnimState.empty()

    # Prime — fill displayed with target so initial draw isn't a long count-up
    snap = collector.snapshot()
    t0 = time.monotonic()
    anim.update_targets(snap, t0)
    for k in anim.targets:
        anim.displayed[k] = float(anim.targets[k])
    anim.spark_prev = list(snap.sparkline)
    anim.spark_target = list(snap.sparkline)

    static_base = build_static_base(snap, snap.sparkline)
    last_static_key = static_key(snap)

    if args.png:
        img = build_frame(snap, anim, t0, static_base)
        img.save(args.png)
        print(f"wrote {args.png}")
        return 0

    fb = open(args.device, "wb", buffering=0)
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    frame_period = 1.0 / args.fps
    last_refresh = 0.0
    last_t = time.monotonic()

    try:
        while running:
            now_t = time.monotonic()
            dt = now_t - last_t
            last_t = now_t

            if now_t - last_refresh >= args.refresh:
                snap = collector.snapshot()
                anim.update_targets(snap, now_t)
                key = static_key(snap)
                if key != last_static_key:
                    static_base = build_static_base(snap, snap.sparkline)
                    last_static_key = key
                last_refresh = now_t

            anim.step(dt)
            img = build_frame(snap, anim, now_t, static_base)
            fb.seek(0)
            fb.write(to_rgb565_le(img))

            sleep_left = frame_period - (time.monotonic() - now_t)
            if sleep_left > 0:
                time.sleep(sleep_left)
    finally:
        fb.close()
        # blank screen on exit
        try:
            with open(args.device, "wb") as f:
                f.write(b"\x00" * (T.WIDTH * T.HEIGHT * 2))
        except OSError:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
