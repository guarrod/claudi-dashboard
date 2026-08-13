"""Visual constants — Hosyond 5" IPS LCD (1024×600, landscape, RGB color).

Drives a full-color dashboard rendered with Pillow and shown via pygame on a
secondary monitor. All sizes/coords are tuned for 1024×600 and can be tweaked
here without touching the renderer.
"""

from pathlib import Path
import sys as _sys

# ── Canvas ───────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1024, 600

# ── Palette (RGB) — warm dark "Claude" theme ─────────────────────────
BG        = (24, 22, 21)      # page background (warm near-black)
PANEL     = (36, 33, 31)      # stat-card background
PANEL_EDGE = (58, 53, 49)     # card border
FG        = (240, 238, 232)   # primary text (cream)
GRAY      = (150, 143, 135)   # secondary / dim text
ACCENT    = (217, 119, 87)    # Clawd coral (#D97757)
ACCENT_DIM = (150, 80, 58)    # dim coral (sparkline base, borders)

# Back-compat aliases (older code referenced these names)
WHITE = FG
BLACK = BG
CREAM = FG
CREAM_DIM = GRAY

CLAWD_PNG = Path(__file__).parent / "clawd.png"

# ── Fonts ────────────────────────────────────────────────────────────
if _sys.platform == "win32":
    _W = "C:/Windows/Fonts/"
    FONT_REG    = _W + "arial.ttf"
    FONT_BOLD   = _W + "arialbd.ttf"
    FONT_MONO   = _W + "consola.ttf"
    FONT_MONO_B = _W + "consolab.ttf"
else:
    FONT_REG    = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    FONT_BOLD   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    FONT_MONO   = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    FONT_MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

# Font sizes (scaled for 1024×600)
F_TITLE = 40   # "CLAUDE CODE"
F_CLOCK = 38   # header clock
F_BADGE = 22   # model badge
F_LABEL = 22   # card section labels (SESSION / TODAY)
F_BIG   = 56   # big token number
F_COST  = 40   # cost number
F_IO    = 22   # IN / OUT line
F_FOOT  = 18   # footer text
F_SPARK = 16   # sparkline label

# ── Layout regions (x0, y0, x1, y1) ──────────────────────────────────
MARGIN = 24

# Header
HEADER_H   = 84
TITLE_POS  = (MARGIN, 22)
CLOCK_POS  = (WIDTH - MARGIN, 20)   # anchored top-right ("ra")
BADGE_POS  = (MARGIN + 360, 34)

# Stat cards (two side-by-side, left/center region)
CARD_Y0, CARD_Y1 = 100, 400
CARD_SESSION = (MARGIN, CARD_Y0, 350, CARD_Y1)
CARD_TODAY   = (366, CARD_Y0, 692, CARD_Y1)

# Clawd lives in the right region
CLAWD_BOX = (708, CARD_Y0, WIDTH - MARGIN, CARD_Y1)   # x0,y0,x1,y1
CLAWD_SIZE = 220                                       # sprite max edge (px)

# Footer line
FOOTER_Y = 420

# Sparkline panel
SPARK_LABEL_Y = 452
SPARK_RECT = (MARGIN, 478, WIDTH - MARGIN, 580)        # x0,y0,x1,y1

# Legacy (no longer used; kept so stray imports don't break)
F_TINY, F_SMALL, F_BASE, F_MED = 16, 18, 20, 22
FB_DEV = Path("/dev/fb0")
