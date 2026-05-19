"""Renderer for the Claude live dashboard — Claude-branded with animated mark.

The mark is the 8-ray asterisk/star that is Claude's brand glyph. Each ray
"breathes" with a phase offset, the whole mark rotates slowly, and a soft
coral halo pulses behind it.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import theme as T


@lru_cache(maxsize=24)
def font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    if mono:
        path = T.FONT_MONO_B if bold else T.FONT_MONO
    else:
        path = T.FONT_BOLD if bold else T.FONT_REG
    return ImageFont.truetype(path, size)


def fmt_int(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 10_000:
        return f"{n/1000:.1f}K"
    return f"{n:,}"


def fmt_money(c: float) -> str:
    if c >= 100:
        return f"${c:,.2f}"
    return f"${c:.2f}"


def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


# ---------- Clawd: the official Claude Code crab mascot ----------
#
# Loads the upstream PNG sprite (Homarr dashboard-icons), caches a
# pixel-perfect resized variant per requested display size, and animates
# bob / blink / halo on top. Resizing uses NEAREST to preserve the
# retro pixel-art crispness.

_CLAWD_CACHE: dict = {}

# Eye bounding boxes in the source 400x400 sprite — sampled from the PNG.
_EYE_BOXES_SRC = [(108, 120, 139, 151),   # left  (x0,y0,x1,y1)
                  (262, 120, 294, 151)]   # right


def _load_clawd_at(size: int) -> tuple[Image.Image, Image.Image]:
    """Return (open, closed) pixel-perfect Clawd sprites at the given size."""
    src = Image.open(T.CLAWD_PNG).convert("RGBA")
    w0, h0 = src.size
    img_open = src.resize((size, size), Image.NEAREST)

    img_closed = img_open.copy()
    d = ImageDraw.Draw(img_closed)
    sx, sy = size / w0, size / h0
    for x0, y0, x1, y1 in _EYE_BOXES_SRC:
        d.rectangle([x0 * sx, y0 * sy, x1 * sx, y1 * sy],
                    fill=(*T.CLAWD_BODY, 255))
    return img_open, img_closed


def draw_clawd(size: int, t: float, *,
               glow: bool = True, excitement: float = 0.0,
               mood: str = "idle") -> Image.Image:
    """Render Clawd at ``size`` px.

    Animations:
      * idle bob   — small Y oscillation (faster when excited)
      * side waddle — subtle X sway
      * blink — eyes briefly covered with body color every ~3.5s
      * halo  — soft coral pulse, brighter when excitement > 0
    """
    cached = _CLAWD_CACHE.get(size)
    if cached is None:
        cached = _load_clawd_at(size)
        _CLAWD_CACHE[size] = cached
    base_open, base_closed = cached

    # Blink: last 6% of a 3.5s cycle (~210ms closed)
    blink_phase = (t % 3.5) / 3.5
    blink_on = blink_phase > 0.94

    # Excitement speeds up & enlarges the bob, and brightens the halo
    bob_freq = 1.8 + 2.2 * excitement
    bob_amp  = size * (0.018 + 0.035 * excitement)
    bob_y = int(round(math.sin(t * bob_freq) * max(1, bob_amp)))
    sway_x = int(round(math.sin(t * 0.9) * max(1, size * 0.010)))

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    if glow:
        halo = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        hd = ImageDraw.Draw(halo)
        base_a = 50 + 40 * (0.5 + 0.5 * math.sin(t * 1.5))
        ga = int(min(220, base_a + 110 * excitement))
        rr = size * (0.48 + 0.06 * excitement)
        hd.ellipse([size/2 - rr, size/2 - rr * 0.85,
                    size/2 + rr, size/2 + rr * 0.85],
                   fill=(*T.CLAWD_BODY, ga))
        halo = halo.filter(ImageFilter.GaussianBlur(radius=size * 0.08))
        canvas.alpha_composite(halo)

    base = base_closed if blink_on else base_open
    canvas.alpha_composite(base, (sway_x, bob_y))
    return canvas


def draw_particles(img: Image.Image, anchor_xy: tuple[int, int],
                   particles: list) -> None:
    """Draw token particles emanating from `anchor_xy`. Pixel-art squares
    in coral that fade and shrink as they age."""
    if not particles:
        return
    d = ImageDraw.Draw(img, "RGBA")
    ax, ay = anchor_xy
    for p in particles:
        frac = max(0.0, p["life"] / p["max_life"])
        alpha = int(255 * (frac ** 0.6))
        sz = max(1, int(p["size"] * (0.5 + 0.5 * frac)))
        x = int(ax + p["x"])
        y = int(ay + p["y"])
        # warmer at start, cooler/cream as they age — keeps the coral theme
        if frac > 0.6:
            col = T.CLAWD_BODY
        elif frac > 0.3:
            col = T.CORAL_HOT
        else:
            col = T.CREAM_DIM
        d.rectangle([x, y, x + sz, y + sz], fill=(*col, alpha))


# Back-compat aliases so older callsites keep working
draw_jetsam = draw_clawd
draw_claude_mark = draw_clawd


# ---------- animation state ----------

@dataclass
class AnimState:
    displayed: dict
    targets: dict
    spark_prev: list
    spark_target: list
    spark_change_at: float

    # Event-driven reactive animation state
    last_token_event_t: float = -100.0   # monotonic time when tokens last grew
    last_prompt_event_t: float = -100.0  # monotonic time of last new prompt
    _last_seen_prompt_ts: float = 0.0    # epoch ts of most recent prompt we've reacted to
    particles: list = field(default_factory=list)

    @classmethod
    def empty(cls) -> "AnimState":
        keys = ("s_in", "s_out", "s_rd", "s_cost",
                "t_in", "t_out", "t_total", "t_cost", "t_msgs")
        return cls(
            displayed={k: 0.0 for k in keys},
            targets={k: 0.0 for k in keys},
            spark_prev=[0] * 30,
            spark_target=[0] * 30,
            spark_change_at=0.0,
        )

    def update_targets(self, snap, now_t: float) -> None:
        new = {
            "s_in":    snap.session["input"],
            "s_out":   snap.session["output"],
            "s_rd":    snap.session["cache_read"],
            "s_cost":  snap.session["cost"],
            "t_in":    snap.today["input"],
            "t_out":   snap.today["output"],
            "t_total": snap.today["total"],
            "t_cost":  snap.today["cost"],
            "t_msgs":  snap.today["messages"],
        }

        # Detect token growth — Clawd should react when tokens flow in.
        # Compare against previous targets (not initial zeros) so the
        # priming snapshot doesn't fire an event.
        grew = any(new[k] > self.targets[k] for k in ("s_in", "s_out", "t_total"))
        was_primed = any(self.targets[k] > 0 for k in ("s_in", "s_out", "t_total"))
        if grew and was_primed and now_t - self.last_token_event_t > 0.3:
            self.last_token_event_t = now_t
            self._emit_particles(count=3, ttl=1.4, vy_range=(-55, -25), x_jitter=18)

        self.targets.update(new)

        # Detect a fresh user prompt via history.jsonl timestamp.
        prompt_epoch = snap.now.timestamp() - snap.last_prompt_age
        if (prompt_epoch > self._last_seen_prompt_ts + 1.0
                and snap.last_prompt_age < 30):
            if self._last_seen_prompt_ts > 0:  # skip very first sighting
                self.last_prompt_event_t = now_t
                self._emit_particles(count=10, ttl=1.9, vy_range=(-85, -45), x_jitter=32)
            self._last_seen_prompt_ts = prompt_epoch

        if snap.sparkline != self.spark_target:
            self.spark_prev = list(self.displayed_sparkline(now_t))
            self.spark_target = list(snap.sparkline)
            self.spark_change_at = now_t

    def step(self, dt: float) -> None:
        # Frame-rate independent exponential approach for smooth tween
        alpha = 1 - math.exp(-dt / 0.12)
        for k, target in self.targets.items():
            cur = self.displayed[k]
            self.displayed[k] = cur + (target - cur) * alpha
        # Particles physics: drift up, mild gravity pulls them back, fade.
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 35 * dt
            p["life"] -= dt
        # Cap particle count so a bursty session can't balloon memory
        self.particles = [p for p in self.particles if p["life"] > 0][-60:]

    def displayed_sparkline(self, now_t: float) -> list[int]:
        t = (now_t - self.spark_change_at) / 0.5
        if t >= 1:
            return list(self.spark_target)
        a = ease_out_cubic(max(0.0, min(1.0, t)))
        return [int(p + (n - p) * a) for p, n in zip(self.spark_prev, self.spark_target)]

    def _emit_particles(self, *, count: int, ttl: float,
                        vy_range: tuple[float, float], x_jitter: int) -> None:
        for _ in range(count):
            self.particles.append({
                "x": random.uniform(-x_jitter, x_jitter),
                "y": random.uniform(-6, 10),
                "vx": random.uniform(-14, 14),
                "vy": random.uniform(*vy_range),
                "life": ttl,
                "max_life": ttl,
                "size": random.choice((2, 2, 3, 3, 4)),
            })

    def excitement(self, now_t: float) -> float:
        """0..1 — how active Clawd should look right now."""
        dt = now_t - self.last_token_event_t
        if dt < 0.2: return 1.0
        if dt > 6.0: return 0.0
        return max(0.0, 1.0 - (dt / 6.0))

    def jump_offset(self, now_t: float, peak: int = 14) -> int:
        """Negative-Y offset for a 0.5s ease-out jump after a new prompt."""
        dt = now_t - self.last_prompt_event_t
        DUR = 0.5
        if dt < 0 or dt > DUR:
            return 0
        return -int(math.sin(math.pi * (dt / DUR)) * peak)


# ---------- drawing primitives ----------

def card(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
         *, radius: int = 8, fill=None, border=None) -> None:
    fill = fill if fill is not None else T.BG_CARD
    d.rounded_rectangle([x, y, x + w, y + h], radius=radius,
                        fill=fill, outline=border)


def section_label(d: ImageDraw.ImageDraw, x: int, y: int, text: str,
                  *, color=None) -> None:
    f = font(T.F_SMALL, bold=True)
    d.text((x, y), text, fill=color or T.WARM_GRAY, font=f)


# ---------- static layer (rebuilt only when snapshot changes) ----------

def _bg_gradient() -> Image.Image:
    """Subtle warm vertical gradient — pre-built once."""
    grad = np.linspace(0, 14, T.HEIGHT, dtype=np.int16)[:, None]
    base = np.array(T.BG, dtype=np.int16)
    bgarr = np.clip(base + grad[:, :, None] * np.array([1, 0.6, 0.4]),
                    0, 255).astype(np.uint8)
    bgarr = np.broadcast_to(bgarr, (T.HEIGHT, T.WIDTH, 3)).copy()
    return Image.fromarray(bgarr, "RGB")


_BG_CACHE: Image.Image | None = None


def _get_bg() -> Image.Image:
    global _BG_CACHE
    if _BG_CACHE is None:
        _BG_CACHE = _bg_gradient()
    return _BG_CACHE.copy()


def build_static_base(snap, sparkline: list[int]) -> Image.Image:
    """Render everything that doesn't change per frame.

    Re-run only when the snapshot's identity-bearing fields change
    (session id, model/tier, sparkline values).
    """
    img = _get_bg()
    d = ImageDraw.Draw(img, "RGBA")

    # ----- top bar (labels only; clock + pulse dot are dynamic) -----
    d.text((28, 8), "CLAUDE", fill=T.CREAM, font=font(T.F_MED, bold=True))
    d.text((28, 27), "LIVE  ·  on-device", fill=T.WARM_GRAY,
           font=font(T.F_TINY, bold=True))

    # ----- HERO mascot zone (mascot itself is dynamic; just the caption here) -----
    mark_size = 120
    mark_y = 44
    sub = "clawd  ·  watching your tokens"
    sf = font(T.F_TINY, bold=True)
    sw = d.textlength(sub, font=sf)
    d.text(((T.WIDTH - sw) // 2, mark_y + mark_size + 2),
           sub, fill=T.WARM_GRAY, font=sf)

    # ----- TODAY card backdrop + label -----
    y0 = 188
    card(d, 10, y0, T.WIDTH - 20, 80, radius=10, fill=T.BG_CARD)
    section_label(d, 22, y0 + 10, "TODAY")

    # ----- SESSION card backdrop + section label + model badge + metric labels -----
    y0 = 278
    card(d, 10, y0, T.WIDTH - 20, 130, radius=10, fill=T.BG_CARD)
    sid = (snap.session["id"] or "—").split("-")[0]
    section_label(d, 22, y0 + 10, f"SESSION  ·  {sid}")

    model = snap.session["model"] or "—"
    short_model = (model.replace("claude-", "")
                        .replace("-2025", "").replace("-2026", ""))
    mf = font(T.F_TINY, bold=True)
    mw = d.textlength(short_model, font=mf)
    badge_x = T.WIDTH - 22 - mw - 12
    d.rounded_rectangle(
        [badge_x, y0 + 7, T.WIDTH - 22, y0 + 22],
        radius=4, fill=T.CORAL_DEEP)
    d.text((badge_x + 6, y0 + 9), short_model, fill=T.CREAM, font=mf)

    # column labels (values are dynamic)
    yr = y0 + 34
    col_w = (T.WIDTH - 20 - 16) // 3
    lf = font(T.F_TINY, bold=True)
    for i, label in enumerate(("INPUT", "OUTPUT", "CACHE RD")):
        cx = 18 + i * col_w
        d.text((cx + 2, yr), label, fill=T.WARM_GRAY, font=lf)

    # progress bar background (fill is dynamic)
    yp = y0 + 86
    bar_x, bar_w = 22, T.WIDTH - 44 - 70
    d.rounded_rectangle([bar_x, yp, bar_x + bar_w, yp + 7],
                        radius=3, fill=T.SUBTLE)

    # ----- ACTIVITY (sparkline bars are static per snapshot) -----
    y0 = 418
    section_label(d, 14, y0, "LAST 30 MIN")

    bars_y, bars_h = y0 + 18, T.HEIGHT - (y0 + 18) - 6
    vmax = max(sparkline) or 1
    n = len(sparkline)
    span = T.WIDTH - 28
    bar_w = span / n
    for i, v in enumerate(sparkline):
        bh = int((v / vmax) * bars_h) if vmax else 0
        bx = 14 + i * bar_w
        bx2 = bx + bar_w - 1
        if v > 0 and bh < 2:
            bh = 2
        by = bars_y + bars_h - bh
        if bh > 0:
            d.rounded_rectangle([bx, by, bx2, bars_y + bars_h],
                                radius=1, fill=T.CORAL_DEEP)
            if bh > 4:
                cap = max(2, bh // 4)
                d.rounded_rectangle([bx, by, bx2, by + cap],
                                    radius=1, fill=T.CORAL_HOT)
        else:
            d.line([bx, bars_y + bars_h - 1, bx2, bars_y + bars_h - 1],
                   fill=T.SUBTLE)

    return img


def static_key(snap) -> tuple:
    """Key that changes when the static layer needs a rebuild."""
    return (snap.session.get("id"),
            snap.session.get("model"),
            tuple(snap.sparkline))


# ---------- per-frame dynamic overlay ----------

def build_frame(snap, anim: AnimState, now_t: float,
                static_base: Image.Image | None = None) -> Image.Image:
    if static_base is None:
        static_base = build_static_base(snap, snap.sparkline)
    img = static_base.copy()
    d = ImageDraw.Draw(img, "RGBA")

    # ----- Top bar dynamic: pulsing status dot + clock -----
    pulse = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(now_t * 3.0))
    dot_color = tuple(int(c * pulse) for c in T.CORAL_HOT)
    d.ellipse([10, 12, 20, 22], fill=dot_color)

    clock = snap.now.astimezone().strftime("%H:%M:%S")
    cf = font(T.F_BASE, bold=True, mono=True)
    cw = d.textlength(clock, font=cf)
    d.text((T.WIDTH - 12 - cw, 14), clock, fill=T.CORAL, font=cf)

    # ----- Animated Clawd (Claude Code mascot) -----
    mark_size = 120
    excitement = anim.excitement(now_t)
    jump_y = anim.jump_offset(now_t, peak=14)
    mark = draw_clawd(mark_size, now_t, glow=True, excitement=excitement)
    mark_x = (T.WIDTH - mark_size) // 2
    mark_y = 44 + jump_y
    img.paste(mark, (mark_x, mark_y), mark)
    # Particles emanate from the top-center of the mascot
    draw_particles(img,
                   anchor_xy=(mark_x + mark_size // 2, mark_y + 12),
                   particles=anim.particles)
    d = ImageDraw.Draw(img, "RGBA")  # rebuild draw after paste

    # ----- TODAY card dynamic values -----
    y_today = 188
    cost_str = fmt_money(anim.displayed["t_cost"])
    cf = font(T.F_HERO, bold=True)
    cw = d.textlength(cost_str, font=cf)
    d.text(((T.WIDTH - cw) // 2, y_today + 22),
           cost_str, fill=T.CORAL_HOT, font=cf)

    msgs = int(anim.displayed["t_msgs"])
    toks = fmt_int(int(anim.displayed["t_total"]))
    sub = f"{msgs} msgs   ·   {toks} tokens"
    sf = font(T.F_SMALL, bold=True)
    sw = d.textlength(sub, font=sf)
    d.text(((T.WIDTH - sw) // 2, y_today + 62),
           sub, fill=T.CREAM_DIM, font=sf)

    # ----- SESSION card dynamic values -----
    y_sess = 278
    yr = y_sess + 34
    col_w = (T.WIDTH - 20 - 16) // 3
    metrics = [
        (fmt_int(int(anim.displayed["s_in"])),  T.CREAM),
        (fmt_int(int(anim.displayed["s_out"])), T.CORAL_HOT),
        (fmt_int(int(anim.displayed["s_rd"])),  T.CREAM_DIM),
    ]
    for i, (val, color) in enumerate(metrics):
        cx = 18 + i * col_w
        for vsize in (T.F_BIG, 22, 20, 18):
            vf = font(vsize, bold=True)
            if d.textlength(val, font=vf) <= col_w - 6:
                break
        d.text((cx + 2, yr + 13), val, fill=color, font=vf)

    # Progress bar fill + pct label + session cost
    yp = y_sess + 86
    t_total = max(int(anim.displayed["t_total"]), 1)
    s_total = (int(anim.displayed["s_in"]) + int(anim.displayed["s_out"])
               + int(anim.displayed["s_rd"]))
    pct = min(1.0, s_total / t_total) if t_total else 0
    bar_x, bar_w = 22, T.WIDTH - 44 - 70
    fill_w = int(bar_w * pct)
    if fill_w > 4:
        d.rounded_rectangle([bar_x, yp, bar_x + fill_w, yp + 7],
                            radius=3, fill=T.CORAL)
    d.text((bar_x, yp + 11), f"{pct*100:.0f}% of today",
           fill=T.WARM_GRAY, font=font(T.F_TINY, bold=True))

    sc = fmt_money(anim.displayed["s_cost"])
    sf = font(T.F_MED, bold=True)
    sw = d.textlength(sc, font=sf)
    d.text((T.WIDTH - 22 - sw, yp - 4), sc, fill=T.CORAL_HOT, font=sf)

    # ----- LIVE pulsing indicator over sparkline -----
    y_act = 418
    live_f = font(T.F_TINY, bold=True)
    live_w = d.textlength("LIVE", font=live_f)
    p2 = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(now_t * 4.0))
    live_dot = tuple(int(c * p2) for c in T.CORAL_HOT)
    live_x = T.WIDTH - 14 - live_w
    d.ellipse([live_x - 12, y_act + 3, live_x - 4, y_act + 11], fill=live_dot)
    d.text((live_x, y_act), "LIVE", fill=T.CREAM_DIM, font=live_f)

    return img


def to_rgb565_le(img: Image.Image) -> bytes:
    if img.mode != "RGB":
        img = img.convert("RGB")
    arr = np.asarray(img, dtype=np.uint16)
    r = (arr[:, :, 0] >> 3) << 11
    g = (arr[:, :, 1] >> 2) << 5
    b = (arr[:, :, 2] >> 3)
    return (r | g | b).astype("<u2").tobytes()
