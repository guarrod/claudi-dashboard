"""Renderer for Waveshare 2.9" e-paper (296×128, B&W).

Layout (landscape):

  ┌──────────────────────────────────────────────────────────────┐
  │ CLAUDE   sonnet            │                         14:32   │ 0–20
  ├──────────────────────────────────────────────────────────────┤
  │ SESSION             │ TODAY                                   │ 22–34
  │ 1.23M tok  $0.083   │ 4.56M tok  $0.310                      │ 35–51
  │ IN 890K  OUT 45K    │ IN 3.2M  OUT 120K                      │ 52–65
  ├──────────────────────────────────────────────────────────────┤
  │ last: 2m ago                                  session-id...  │ 67–80
  │ ▁▁▂▃▅▆▇█▇▆▅▄▃▂▁  (30-min sparkline)                         │ 82–126
  └──────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

import theme as T
from collector import Snapshot


@lru_cache(maxsize=12)
def font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    path = (T.FONT_MONO_B if bold else T.FONT_MONO) if mono else \
           (T.FONT_BOLD   if bold else T.FONT_REG)
    return ImageFont.truetype(path, size)


def fmt_int(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 10_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:,}"


def fmt_money(c: float) -> str:
    return f"${c:.3f}"


def _short_model(model_id: str) -> str:
    if not model_id:
        return "—"
    m = model_id.lower()
    if "opus"   in m: return "opus"
    if "sonnet" in m: return "sonnet"
    if "haiku"  in m: return "haiku"
    return model_id[:10]


def _fmt_age(seconds: float) -> str:
    if seconds <= 0:
        return "—"
    m = int(seconds // 60)
    if m < 1:  return "<1m ago"
    if m < 60: return f"{m}m ago"
    return f"{m // 60}h {m % 60}m ago"


def _draw_sparkline(d: ImageDraw.Draw, spark: list[int],
                    x: int, y: int, w: int, h: int) -> None:
    n = len(spark)
    if n == 0:
        return
    peak = max(spark) or 1
    bar_w = max(1, w // n)
    for i, val in enumerate(spark):
        bar_h = int(val / peak * h)
        if val > 0 and bar_h < 2:
            bar_h = 2
        bx = x + i * bar_w
        if bar_h > 0:
            d.rectangle([bx, y + h - bar_h, bx + bar_w - 1, y + h], fill=0)
    d.line([(x, y + h), (x + w, y + h)], fill=0, width=1)


def build_frame(snap: Snapshot) -> Image.Image:
    img = Image.new("L", (T.WIDTH, T.HEIGHT), 255)
    d = ImageDraw.Draw(img)
    mid = T.WIDTH // 2  # 148 — vertical divider x

    # ── HEADER (y 2–19) ──────────────────────────────────────────
    d.text((4, 2), "CLAUDE", fill=0, font=font(T.F_MED, bold=True))
    d.text((72, 4), _short_model(snap.session.get("model") or ""),
           fill=T.GRAY[0], font=font(T.F_SMALL))
    d.text((T.WIDTH - 4, 2), snap.now.strftime("%H:%M"),
           fill=0, font=font(T.F_MED, bold=True), anchor="ra")
    d.line([(0, 20), (T.WIDTH, 20)], fill=0, width=1)

    # ── COLUMN HEADERS (y 22–33) ─────────────────────────────────
    d.text((4, 22), "SESSION", fill=0, font=font(T.F_TINY, bold=True))
    d.text((mid + 4, 22), "TODAY",   fill=0, font=font(T.F_TINY, bold=True))
    d.line([(mid, 20), (mid, 66)], fill=0, width=1)

    sess  = snap.session
    today = snap.today

    # ── ROW 1: total tokens + cost (y 35–50) ─────────────────────
    s_line = f"{fmt_int(sess['total'])} tok  {fmt_money(sess['cost'])}"
    t_line = f"{fmt_int(today['total'])} tok  {fmt_money(today['cost'])}"
    d.text((4,       35), s_line, fill=0, font=font(T.F_SMALL, bold=True))
    d.text((mid + 4, 35), t_line, fill=0, font=font(T.F_SMALL, bold=True))

    # ── ROW 2: IN / OUT (y 52–64) ────────────────────────────────
    s_io = f"IN {fmt_int(sess['input'])}  OUT {fmt_int(sess['output'])}"
    t_io = f"IN {fmt_int(today['input'])}  OUT {fmt_int(today['output'])}"
    d.text((4,       52), s_io, fill=0, font=font(T.F_TINY))
    d.text((mid + 4, 52), t_io, fill=0, font=font(T.F_TINY))

    # ── FOOTER (y 67–80) ─────────────────────────────────────────
    d.line([(0, 66), (T.WIDTH, 66)], fill=0, width=1)
    d.text((4, 68), f"last: {_fmt_age(snap.last_prompt_age)}",
           fill=T.GRAY[0], font=font(T.F_TINY))

    sid_short = (snap.session.get("id") or "")[:12]
    if sid_short:
        d.text((T.WIDTH - 4, 68), sid_short,
               fill=T.GRAY[0], font=font(T.F_TINY), anchor="ra")

    # ── SPARKLINE (y 82–126) ─────────────────────────────────────
    _draw_sparkline(d, snap.sparkline, x=4, y=82, w=T.WIDTH - 8, h=44)

    return img
