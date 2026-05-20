"""Waveshare 2.9" e-Paper driver with PNG fallback for local development.

On Raspberry Pi: wraps waveshare_epd.epd2in9_V2.
On other platforms: saves frames as PNG previews.

Install on Pi:
    pip install RPi.GPIO spidev
    # then place waveshare_epd/ from https://github.com/waveshare/e-Paper
    # under RaspberryPi_JetsonNano/python/lib/ in your project or site-packages
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


class EPDDriver:
    def __init__(self, png_out: Path | None = None) -> None:
        self._png = png_out
        self._epd = None
        if sys.platform != "win32":
            self._epd = self._load_epd()

    def _load_epd(self):
        try:
            from waveshare_epd import epd2in9_V2
            return epd2in9_V2.EPD()
        except ImportError:
            print("waveshare_epd not found — running in PNG-preview mode")
            return None

    def init(self) -> None:
        if self._epd:
            self._epd.init()
            self._epd.Clear(0xFF)

    def display(self, img: Image.Image) -> None:
        if self._png:
            img.save(self._png)
            print(f"wrote {self._png}")
        if self._epd:
            self._epd.display(self._epd.getbuffer(img.convert("1")))

    def sleep(self) -> None:
        if self._epd:
            self._epd.sleep()

    def wake(self) -> None:
        if self._epd:
            self._epd.init()
