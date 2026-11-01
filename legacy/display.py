"""Display sink — shows Pillow frames full-screen on a secondary monitor.

Pillow composes each RGB frame; this module blits it with pygame. On Windows
there is no framebuffer device, so we open a borderless full-screen window on
the chosen display index (the external monitor is usually display 1).

Modes:
    Display(png_out=PATH)        # save one frame to PNG and exit (no window)
    Display()                    # full-screen on display 1 (the external monitor)
    Display(display_index=0)     # full-screen on the primary monitor
    Display(windowed=True)       # 1024×600 window on the primary monitor (dev)
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

import theme as T


class Display:
    def __init__(
        self,
        png_out: Path | None = None,
        *,
        display: int | str = "auto",
        windowed: bool = False,
    ) -> None:
        self._png = png_out
        self._screen = None
        self._pygame = None
        if png_out is not None:
            return  # preview mode — no window needed

        import pygame  # imported lazily so --png works without pygame
        self._pygame = pygame
        # frombytes was added in pygame 2.1.3; fall back to fromstring on older.
        self._to_surface = getattr(pygame.image, "frombytes", None) \
            or pygame.image.fromstring
        pygame.init()
        pygame.display.set_caption("claude-dashboard")

        # Frames are always composed at the design resolution (1024×600) and
        # then scaled (letterboxed) to whatever the monitor actually runs at —
        # so the dashboard still works if the panel is stuck at 640×480/800×600.
        self._design = (T.WIDTH, T.HEIGHT)
        sizes = pygame.display.get_desktop_sizes()
        idx = self._pick_display(display, sizes)

        if windowed or idx is None:
            # Dev / no match: plain 1024×600 window on the primary monitor.
            self._screen = pygame.display.set_mode(self._design)
        else:
            # Full-screen at the chosen monitor's CURRENT resolution.
            self._screen = pygame.display.set_mode(
                sizes[idx], pygame.FULLSCREEN, display=idx
            )
            pygame.mouse.set_visible(False)

        self._surface_size = self._screen.get_size()

    @staticmethod
    def _pick_display(display: int | str, sizes: list[tuple[int, int]]) -> int | None:
        """Resolve which monitor to use. Returns a display index, or None to
        fall back to a window.

        'auto' picks the smallest screen attached — the little dashboard panel
        is always smaller than the laptop/desktop monitors, so this finds it
        regardless of how the OS happens to order the displays.
        """
        if not sizes:
            return None
        if display == "auto":
            return min(range(len(sizes)), key=lambda i: sizes[i][0] * sizes[i][1])
        try:
            idx = int(display)
        except (TypeError, ValueError):
            return None
        return idx if 0 <= idx < len(sizes) else None

    def show(self, img: Image.Image) -> None:
        """Render one PIL RGB frame to the screen (or PNG in preview mode)."""
        if self._png is not None:
            img.save(self._png)
            print(f"wrote {self._png}")
            return
        if img.mode != "RGB":
            img = img.convert("RGB")
        pg = self._pygame
        surf = self._to_surface(img.tobytes(), img.size, "RGB")

        sw, sh = self._surface_size
        if (img.width, img.height) == (sw, sh):
            self._screen.blit(surf, (0, 0))
        else:
            # Scale to fit, preserving aspect ratio (letterbox the remainder).
            scale = min(sw / img.width, sh / img.height)
            tw, th = max(1, int(img.width * scale)), max(1, int(img.height * scale))
            scaled = pg.transform.smoothscale(surf, (tw, th))
            self._screen.fill((0, 0, 0))
            self._screen.blit(scaled, ((sw - tw) // 2, (sh - th) // 2))
        pg.display.flip()

    def pump(self) -> bool:
        """Process window events. Returns False when the user wants to quit."""
        if self._pygame is None:
            return True
        pg = self._pygame
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return False
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return False
        return True

    def close(self) -> None:
        if self._pygame is not None:
            self._pygame.quit()
