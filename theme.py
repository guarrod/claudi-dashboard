"""Visual constants — Claude brand palette."""

from pathlib import Path

WIDTH, HEIGHT = 320, 480

# Claude brand palette — warm dark with coral accents
BG          = (24, 20, 17)       # warm coffee black
BG_CARD     = (38, 31, 26)       # card surface
BG_CARD_2   = (52, 42, 35)       # elevated surface / hover

CREAM       = (245, 240, 232)    # primary text — Claude's signature cream
CREAM_DIM   = (196, 181, 162)    # secondary text
WARM_GRAY   = (140, 124, 110)
MUTED       = (90, 78, 68)
SUBTLE      = (60, 50, 42)

# Coral / terracotta — Claude's signature accent
CORAL       = (217, 119, 87)     # #D97757
CORAL_HOT   = (240, 155, 120)    # lighter pop
CORAL_DEEP  = (165, 80, 55)
CORAL_GLOW  = (217, 119, 87)     # used as RGBA with alpha for glow

# Status accents derived from coral
GOOD        = (180, 200, 130)    # warm-tinted soft green for "in"
INFO        = (180, 165, 140)    # neutral warm for cache reads

# Clawd — the official Claude Code crab mascot. Body color sampled from
# the upstream PNG (homarr-labs/dashboard-icons/png/clawd.png).
CLAWD_BODY = (241, 91, 69)
CLAWD_EYE  = (10, 10, 10)

CLAWD_PNG = Path(__file__).parent / "clawd.png"

FONT_REG    = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO   = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

# Font sizes
F_TINY  = 10
F_SMALL = 12
F_BASE  = 14
F_MED   = 17
F_BIG   = 24
F_XL    = 30
F_HERO  = 42

FB_DEV = Path("/dev/fb1")
