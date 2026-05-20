"""Visual constants — Waveshare 2.9" e-paper (296×128, B&W)."""

from pathlib import Path
import sys as _sys

WIDTH, HEIGHT = 296, 128

# Grayscale palette (render in "L" mode; convert to "1" before sending to HW)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY  = (110, 110, 110)   # secondary text / dim elements

# Aliases so any leftover references keep working
BG       = WHITE
FG       = BLACK
CREAM    = BLACK
CREAM_DIM = GRAY

CLAWD_PNG = Path(__file__).parent / "clawd.png"

if _sys.platform == "win32":
    _W = "C:/Windows/Fonts/"
    FONT_REG    = _W + "arial.ttf"
    FONT_BOLD   = _W + "arialbd.ttf"
    FONT_MONO   = _W + "cour.ttf"
    FONT_MONO_B = _W + "courbd.ttf"
else:
    FONT_REG    = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    FONT_BOLD   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    FONT_MONO   = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    FONT_MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

F_TINY  = 10
F_SMALL = 12
F_BASE  = 13
F_MED   = 14

FB_DEV = Path("/dev/fb1")
