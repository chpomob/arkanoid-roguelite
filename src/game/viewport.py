"""
Viewport: logical game space (1024×768) ↔ screen pixel projection.

Game logic and physics operate in the logical 1024×768 space (pixels).
The Viewport projects to screen pixels at draw() time, enabling
resolution-independent rendering without changing gameplay.
"""
import pygame


class Viewport:
    """Projects game coordinates from logical space to screen pixels."""

    def __init__(self, logical_w: int = 1024, logical_h: int = 768,
                 screen_w: int = None, screen_h: int = None):
        """
        logical_w, logical_h: game logic resolution (default 1024×768)
        screen_w, screen_h: actual screen for rendering (defaults to logical)
        """
        self.lw = float(logical_w)
        self.lh = float(logical_h)
        self.sw = float(screen_w or logical_w)
        self.sh = float(screen_h or logical_h)
        self.sx = self.sw / self.lw   # scale X: logical px → screen px
        self.sy = self.sh / self.lh   # scale Y: logical px → screen px

    # ── Pixel projections (logical → screen) ────────────────────────

    def px(self, lx: float) -> int:
        """Logical X (pixels in 1024 space) → screen X."""
        return int(lx * self.sx)

    def py(self, ly: float) -> int:
        """Logical Y (pixels in 768 space) → screen Y."""
        return int(ly * self.sy)

    def rect(self, lx: float, ly: float, lw: float, lh: float) -> pygame.Rect:
        """Logical rect → screen Rect. All four in logical pixels."""
        return pygame.Rect(
            int(lx * self.sx), int(ly * self.sy),
            int(lw * self.sx), int(lh * self.sy),
        )

    def cen(self, lx: float, ly: float) -> tuple[int, int]:
        """Logical center point → screen (x, y)."""
        return (self.px(lx), self.py(ly))

    # ── Screen → logical (for touch/mouse input) ────────────────────

    def from_screen(self, sx: int, sy: int) -> tuple[float, float]:
        """Screen coords → logical coords."""
        return (sx / self.sx, sy / self.sy)

    # ── Size projection ─────────────────────────────────────────────

    def psize(self, logical_px: float) -> int:
        """Logical pixel size → screen pixel size (uses X scale)."""
        return int(logical_px * self.sx)

    # ── Speed conversion (legacy helpers for code migration) ────────

    def nspeed(self, old_px_per_frame: float, fps: float = 60.0) -> float:
        """Old pixel/frame speed → logical px per frame (identity at 1024)."""
        return old_px_per_frame

    def nspeed_y(self, old_px_per_frame: float, fps: float = 60.0) -> float:
        """Same as nspeed for vertical."""
        return old_px_per_frame

    # ── Legacy helpers (identity at logical 1024×768) ───────────────

    def legacy_x(self, old_px: float) -> float:
        """Old 1024-based pixel X → same (identity, game uses logical px)."""
        return old_px

    def legacy_y(self, old_px: float) -> float:
        """Old 768-based pixel Y → same (identity)."""
        return old_px

    def legacy_s(self, old_px: float) -> float:
        """Old pixel size → same (identity)."""
        return old_px

    # ── Font size ───────────────────────────────────────────────────

    def font_size(self, old_pt: int) -> int:
        """Old point size → scaled for current screen height."""
        return max(8, int(old_pt * self.sy))

    # Backward-compat aliases for code using .w / .h
    @property
    def w(self): return self.lw
    @property
    def h(self): return self.lh
    @property
    def _ref_w(self): return self.lw
    @property
    def _ref_h(self): return self.lh
