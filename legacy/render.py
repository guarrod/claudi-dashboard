"""Renderer for the 1024×600 color dashboard.

Architecture (static/dynamic layer split, as in the original design):

  * a cached *static* layer  → background, card panels, title, section labels
  * a *dynamic* overlay drawn every frame → clock, numbers, Clawd, particles,
    halo and the 30-minute sparkline.

The `Renderer` is stateful: `update_data(snap)` feeds it a fresh Snapshot and
fires reactive animations (Clawd jumps on a new prompt, particles fly out when
tokens grow); `step(dt)` advances the animation; `frame()` composes one image.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

import theme as T
from collector import Snapshot


# ── small formatting helpers (unchanged behaviour) ───────────────────
@lru_cache(maxsize=24)
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


# ── particle system ──────────────────────────────────────────────────
@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float


def _blend(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    """Linear blend a→b by t in [0,1]."""
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Renderer:
    GRAVITY = 320.0  # px/s² for burst particles

    def __init__(self) -> None:
        self.t = 0.0
        self.snap: Snapshot | None = None

        # animation state
        self.particles: list[Particle] = []
        self.halo = 0.0          # 0..1 glow intensity behind Clawd
        self.active = 0.0        # >0 while tokens are actively growing
        self.jump_y = 0.0        # vertical jump offset (≤0 = above ground)
        self.jump_v = 0.0
        self.blink_next = 2.0    # seconds until next blink
        self.blink_t = 0.0       # remaining blink time (>0 = eyes closed/squash)

        # deltas
        self.prev_total: int | None = None
        self.prev_prompt_age: float | None = None

        # cached layers
        self._static: Image.Image | None = None
        self._clawd = self._load_clawd()

    # ── assets ───────────────────────────────────────────────────────
    def _load_clawd(self) -> Image.Image | None:
        try:
            img = Image.open(T.CLAWD_PNG).convert("RGBA")
        except (OSError, FileNotFoundError):
            return None
        img.thumbnail((T.CLAWD_SIZE, T.CLAWD_SIZE), Image.LANCZOS)
        return img

    # ── data / reactive triggers ─────────────────────────────────────
    def update_data(self, snap: Snapshot) -> None:
        total = snap.session.get("total", 0)
        age = snap.last_prompt_age or 0.0

        # New prompt → last_prompt_age dropped sharply since the last snapshot.
        if self.prev_prompt_age is not None and age + 1.0 < self.prev_prompt_age:
            self._on_new_prompt()

        # Tokens grew → trickle of particles + halo bump.
        if self.prev_total is not None and total > self.prev_total:
            grew = total - self.prev_total
            self._on_token_growth(grew)

        self.prev_total = total
        self.prev_prompt_age = age
        self.snap = snap

    def _clawd_center(self) -> tuple[int, int]:
        x0, y0, x1, y1 = T.CLAWD_BOX
        return (x0 + x1) // 2, (y0 + y1) // 2

    def _on_new_prompt(self) -> None:
        self.jump_v = -400.0
        self.halo = 1.0
        self.active = 3.0
        self._spawn(26, burst=True)

    def _on_token_growth(self, grew: int) -> None:
        self.halo = min(1.0, max(self.halo, 0.55))
        self.active = max(self.active, 2.0)
        n = min(10, 2 + grew // 4000)
        self._spawn(n, burst=False)

    def _spawn(self, n: int, *, burst: bool) -> None:
        cx, cy = self._clawd_center()
        for _ in range(n):
            ang = random.uniform(0, 2 * math.pi)
            if burst:
                spd = random.uniform(120, 280)
                vx, vy = math.cos(ang) * spd, math.sin(ang) * spd - 60
                life = random.uniform(0.8, 1.5)
                size = random.uniform(3, 6)
            else:
                spd = random.uniform(20, 70)
                vx, vy = math.cos(ang) * spd * 0.5, -abs(math.sin(ang) * spd) - 30
                life = random.uniform(0.6, 1.1)
                size = random.uniform(2, 4)
            self.particles.append(
                Particle(cx, cy, vx, vy, life, life, size)
            )

    # ── animation step ───────────────────────────────────────────────
    def step(self, dt: float) -> None:
        self.t += dt
        self.halo = max(0.0, self.halo - dt * 0.6)
        self.active = max(0.0, self.active - dt)

        # jump physics
        if self.jump_y < 0 or self.jump_v < 0:
            self.jump_v += self.GRAVITY * dt
            self.jump_y += self.jump_v * dt
            if self.jump_y >= 0:
                self.jump_y = 0.0
                self.jump_v = 0.0

        # blink scheduling
        self.blink_next -= dt
        if self.blink_t > 0:
            self.blink_t -= dt
        elif self.blink_next <= 0:
            self.blink_t = 0.12
            self.blink_next = random.uniform(2.5, 5.5)

        # particles
        alive: list[Particle] = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += self.GRAVITY * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self.particles = alive

    # ── static layer ─────────────────────────────────────────────────
    def _build_static(self) -> Image.Image:
        img = Image.new("RGB", (T.WIDTH, T.HEIGHT), T.BG)
        d = ImageDraw.Draw(img)

        # header
        d.text(T.TITLE_POS, "CLAUDE CODE", fill=T.FG, font=font(T.F_TITLE, bold=True))
        d.line([(0, T.HEADER_H), (T.WIDTH, T.HEADER_H)], fill=T.PANEL_EDGE, width=2)

        # stat-card panels + section labels
        for rect, label in ((T.CARD_SESSION, "SESSION"), (T.CARD_TODAY, "TODAY")):
            d.rounded_rectangle(rect, radius=14, fill=T.PANEL, outline=T.PANEL_EDGE, width=2)
            d.text((rect[0] + 18, rect[1] + 16), label,
                   fill=T.ACCENT, font=font(T.F_LABEL, bold=True))

        # footer divider
        d.line([(T.MARGIN, T.FOOTER_Y), (T.WIDTH - T.MARGIN, T.FOOTER_Y)],
               fill=T.PANEL_EDGE, width=1)

        # sparkline label + baseline
        d.text((T.MARGIN, T.SPARK_LABEL_Y), "TOKENS · LAST 30 MIN",
               fill=T.GRAY, font=font(T.F_SPARK, bold=True))
        sx0, sy0, sx1, sy1 = T.SPARK_RECT
        d.line([(sx0, sy1), (sx1, sy1)], fill=T.PANEL_EDGE, width=1)
        return img

    # ── one composed frame ───────────────────────────────────────────
    def frame(self) -> Image.Image:
        if self._static is None:
            self._static = self._build_static()
        if self.snap is None:
            return self._static.copy()

        img = self._static.copy().convert("RGBA")

        # halo (behind Clawd) ------------------------------------------
        if self.halo > 0.02:
            img = Image.alpha_composite(img, self._halo_layer())

        # Clawd --------------------------------------------------------
        self._paste_clawd(img)

        # particles + dynamic text -------------------------------------
        d = ImageDraw.Draw(img)
        self._draw_particles(d)
        self._draw_dynamic_text(d)
        self._draw_sparkline(d)

        return img.convert("RGB")

    # ── dynamic pieces ───────────────────────────────────────────────
    def _halo_layer(self) -> Image.Image:
        layer = Image.new("RGBA", (T.WIDTH, T.HEIGHT), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        cx, cy = self._clawd_center()
        cy += int(self.jump_y)
        base = T.CLAWD_SIZE // 2 + 20
        for i in range(6, 0, -1):
            r = base * i / 6
            a = int(70 * self.halo * (i / 6) ** 2)
            d.ellipse([cx - r, cy - r, cx + r, cy + r],
                      fill=(T.ACCENT[0], T.ACCENT[1], T.ACCENT[2], a))
        return layer

    def _paste_clawd(self, img: Image.Image) -> None:
        if self._clawd is None:
            return
        sprite = self._clawd
        # blink → quick vertical squash
        if self.blink_t > 0:
            w, h = sprite.size
            sprite = sprite.resize((w, int(h * 0.82)), Image.LANCZOS)

        cx, cy = self._clawd_center()
        bob = math.sin(self.t * (0.8 if self.active > 0 else 0.4) * 2 * math.pi)
        bob *= (10 if self.active > 0 else 6)
        x = cx - sprite.width // 2
        y = cy - sprite.height // 2 + int(bob) + int(self.jump_y)
        img.paste(sprite, (x, y), sprite)

    def _draw_particles(self, d: ImageDraw.ImageDraw) -> None:
        for p in self.particles:
            frac = p.life / p.max_life
            col = _blend(T.BG, T.ACCENT, frac)
            a = int(255 * min(1.0, frac * 1.3))
            r = p.size
            d.ellipse([p.x - r, p.y - r, p.x + r, p.y + r],
                      fill=(col[0], col[1], col[2], a))

    def _draw_dynamic_text(self, d: ImageDraw.ImageDraw) -> None:
        snap = self.snap
        assert snap is not None
        sess, today = snap.session, snap.today

        # header: clock + model badge
        d.text(T.CLOCK_POS, snap.now.astimezone().strftime("%H:%M"),
               fill=T.FG, font=font(T.F_CLOCK, bold=True), anchor="ra")
        d.text(T.BADGE_POS, _short_model(sess.get("model") or ""),
               fill=T.GRAY, font=font(T.F_BADGE, bold=True))

        # stat cards
        for rect, data in ((T.CARD_SESSION, sess), (T.CARD_TODAY, today)):
            x = rect[0] + 18
            d.text((x, rect[1] + 56), f"{fmt_int(data['total'])}",
                   fill=T.FG, font=font(T.F_BIG, bold=True))
            d.text((x, rect[1] + 124), "tokens",
                   fill=T.GRAY, font=font(T.F_BADGE))
            d.text((x, rect[1] + 162), fmt_money(data["cost"]),
                   fill=T.ACCENT, font=font(T.F_COST, bold=True))
            d.text((x, rect[1] + 226),
                   f"IN {fmt_int(data['input'])}   OUT {fmt_int(data['output'])}",
                   fill=T.GRAY, font=font(T.F_IO))

        # footer
        d.text((T.MARGIN, T.FOOTER_Y - 26),
               f"last: {_fmt_age(snap.last_prompt_age)}",
               fill=T.GRAY, font=font(T.F_FOOT))
        sid = (sess.get("id") or "")[:18]
        if sid:
            d.text((T.WIDTH - T.MARGIN, T.FOOTER_Y - 26), sid,
                   fill=T.GRAY, font=font(T.F_FOOT), anchor="ra")

    def _draw_sparkline(self, d: ImageDraw.ImageDraw) -> None:
        spark = self.snap.sparkline if self.snap else []
        sx0, sy0, sx1, sy1 = T.SPARK_RECT
        w, h = sx1 - sx0, sy1 - sy0
        n = len(spark)
        if n == 0:
            return
        peak = max(spark) or 1
        gap = 3
        bar_w = max(2, (w - gap * (n - 1)) // n)
        for i, val in enumerate(spark):
            bar_h = int(val / peak * h)
            if val > 0 and bar_h < 3:
                bar_h = 3
            bx = sx0 + i * (bar_w + gap)
            if bar_h > 0:
                col = _blend(T.ACCENT_DIM, T.ACCENT, val / peak)
                d.rectangle([bx, sy1 - bar_h, bx + bar_w, sy1], fill=col)


# ── backward-compatible one-shot helper ──────────────────────────────
def build_frame(snap: Snapshot) -> Image.Image:
    r = Renderer()
    r.update_data(snap)
    return r.frame()
