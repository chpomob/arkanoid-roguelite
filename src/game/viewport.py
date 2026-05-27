"""
Viewport: normalized [0,1] coordinate space ↔ pixel projection.

All game logic operates in normalized coords. The Viewport projects to screen
pixels only at draw() time. This makes the game resolution-independent —
same code runs on 1024×768 desktop, 2400×1080 phone, or 4K TV.
"""
import pygame


class Viewport:
    """Projects normalized [0,1] coords to pixel coords for a given screen size."""

    def __init__(self, screen_w: int, screen_h: int):
        self.w = float(screen_w)
        self.h = float(screen_h)
        # Legacy reference for backward-compatible speed calculations
        self._ref_w = 1024.0
        self._ref_h = 768.0

    # ── Normalized → pixel projections ──────────────────────────────

    def px(self, nx: float) -> int:
        """Normalized X → pixel X.  0.5 → screen_w/2."""
        return int(nx * self.w)

    def py(self, ny: float) -> int:
        """Normalized Y → pixel Y.  0.5 → screen_h/2."""
        return int(ny * self.h)

    def nsize(self, ns: float) -> int:
        """Normalized size → pixel size (uses min dimension).  0.01 → 1% of min(w,h)."""
        return int(ns * min(self.w, self.h))

    def rect(self, nx: float, ny: float, nw: float, nh: float) -> pygame.Rect:
        """Normalized rect → pygame.Rect. All four are fractions of screen dims."""
        return pygame.Rect(self.px(nx), self.py(ny), self.px(nw), self.py(nh))

    def rect_nw_nh(self, nx: float, ny: float, nw: float, nh: float) -> pygame.Rect:
        """Normalized pos, but nw/nh treated as width/height fractions (not X fractions)."""
        return pygame.Rect(
            self.px(nx), self.py(ny),
            int(nw * self.w), int(nh * self.h),
        )

    def rect_wh(self, nx: float, ny: float, pw: int, ph: int) -> pygame.Rect:
        """Mixed: normalized position, pixel size (for text labels, small elements)."""
        return pygame.Rect(self.px(nx), self.py(ny), pw, ph)

    def cen(self, nx: float, ny: float) -> tuple[int, int]:
        """Normalized pos → pixel center point."""
        return (self.px(nx), self.py(ny))

    # ── Pixel → normalized (touch/mouse input) ──────────────────────

    def from_screen(self, px: int, py: int) -> tuple[float, float]:
        """Pixel coords → normalized coords."""
        return (px / self.w, py / self.h)

    # ── Speed conversion ────────────────────────────────────────────

    def nspeed(self, old_px_per_frame: float, fps: float = 60.0) -> float:
        """Convert old pixel/frame speed to normalized/sec using actual screen width."""
        return (old_px_per_frame * fps) / self.w

    def nspeed_y(self, old_px_per_frame: float, fps: float = 60.0) -> float:
        """Same as nspeed but normalized against height."""
        return (old_px_per_frame * fps) / self.h

    # ── Legacy helpers (bridge old pixel → normalized) ──────────────

    def legacy_x(self, old_px: float) -> float:
        """Old 1024-based pixel X → normalized [0,1]."""
        return old_px / self._ref_w

    def legacy_y(self, old_px: float) -> float:
        """Old 768-based pixel Y → normalized [0,1]."""
        return old_px / self._ref_h

    def legacy_s(self, old_px: float) -> float:
        """Old pixel size → normalized (fraction of current min screen dimension)."""
        return old_px / min(self.w, self.h)

    def legacy_rect(self, x: float, y: float, w: float, h: float) -> pygame.Rect:
        """Old pixel rect → normalized rect → projected back.
        Used for quick migration of hardcoded pixel rects in screens.py.
        """
        return pygame.Rect(
            self.px(self.legacy_x(x)),
            self.py(self.legacy_y(y)),
            self.px(self.legacy_x(w)),
            self.py(self.legacy_y(h)),
        )

    # ── Font size ───────────────────────────────────────────────────

    def font_size(self, old_pt: int) -> int:
        """Old point size → proportional pixel size for current screen height."""
        return max(8, int(old_pt * self.h / self._ref_h))
