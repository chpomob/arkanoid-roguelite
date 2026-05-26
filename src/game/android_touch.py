"""
Android touch input handler for Arkanoid Roguelite.

Provides:
- Paddle tracking (finger X → paddle X)
- Virtual buttons (pause, cannon, gravity well)
- Touch-to-menu navigation
"""

import pygame

# Virtual button zones (fractional, relative to screen size)
BUTTON_ZONES = {
    "pause":    pygame.Rect(0.85, 0.02, 0.13, 0.06),   # top-right
    "cannon":   pygame.Rect(0.02, 0.85, 0.08, 0.12),   # bottom-left
    "gravity":  pygame.Rect(0.12, 0.85, 0.08, 0.12),   # bottom-left-ish
}

VIRTUAL_BTN_COLORS = {
    "pause":  (200, 180, 60),
    "cannon": (220, 100, 60),
    "gravity": (60, 120, 220),
}


class TouchState:
    """Tracks the current touch state for one finger."""
    def __init__(self):
        self.active = False          # finger currently on screen
        self.x = 0                   # current X position
        self.y = 0                   # current Y position
        self.start_x = 0             # X where finger started
        self.start_y = 0             # Y where finger started
        self.paddle_x = None         # paddle X when touch started (for relative drag)
        self.tapped = False          # True for one frame after a tap
        self.tap_handled = False     # Whether this tap was consumed
        self.current_touch_id = None # SDL touch finger id

    def reset_tap(self):
        self.tapped = False
        self.tap_handled = False


class VirtualButton:
    def __init__(self, zone_rect, action, label, color):
        # zone_rect is fractional (0-1 range), stored as-is
        self.zone = zone_rect
        self.action = action
        self.label = label
        self.color = color
        self.pressed = False

    def screen_rect(self, screen_w, screen_h):
        return pygame.Rect(
            int(self.zone.x * screen_w),
            int(self.zone.y * screen_h),
            int(self.zone.w * screen_w),
            int(self.zone.h * screen_h),
        )

    def contains(self, x, y, screen_w, screen_h):
        return self.screen_rect(screen_w, screen_h).collidepoint(x, y)

    def draw(self, surface, screen_w, screen_h):
        rect = self.screen_rect(screen_w, screen_h)
        color = tuple(min(255, c + 40) for c in self.color) if self.pressed else self.color
        alpha = 160 if not self.pressed else 220

        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        bg.fill((*color, alpha))
        pygame.draw.rect(bg, (*color, alpha), bg.get_rect(), border_radius=6)
        surface.blit(bg, rect)

        # Icon text
        font = pygame.font.Font(None, rect.height - 6)
        text = font.render(self.label, True, (255, 255, 255))
        tx = rect.x + (rect.width - text.get_width()) // 2
        ty = rect.y + (rect.height - text.get_height()) // 2
        surface.blit(text, (tx, ty))


class AndroidInput:
    """
    Manages touch input and virtual buttons for the Android build.

    Call once per frame:
      input.update_touch_events(events, screen_w, screen_h)  -> processes event list
      input.draw(surface, screen_w, screen_h)                -> draws virtual buttons
      input.paddle_target_x(screen_w)                        -> returns desired paddle X or None
      input.wants_action(action)                              -> True if btn pressed this frame
    """
    def __init__(self):
        self.touch = TouchState()
        self.buttons = [
            VirtualButton(BUTTON_ZONES["pause"], "pause", "⏸", VIRTUAL_BTN_COLORS["pause"]),
            VirtualButton(BUTTON_ZONES["cannon"], "up", "🔫", VIRTUAL_BTN_COLORS["cannon"]),
            VirtualButton(BUTTON_ZONES["gravity"], "down", "🌀", VIRTUAL_BTN_COLORS["gravity"]),
        ]
        self._action_queue = set()   # actions triggered this frame
        self._screen_w = 1024
        self._screen_h = 768
        self._menu_action = None     # menu action from a tap
        self._menu_click_pos = None  # raw tap position for menu click

    def update_touch_events(self, events, screen_w, screen_h):
        """Process pygame events and update touch state."""
        self._screen_w = screen_w
        self._screen_h = screen_h
        self._action_queue.clear()
        self._menu_action = None
        self._menu_click_pos = None
        self.touch.reset_tap()

        for event in events:
            if event.type == pygame.FINGERDOWN:
                self.touch.active = True
                self.touch.x = int(event.x * screen_w)
                self.touch.y = int(event.y * screen_h)
                self.touch.start_x = self.touch.x
                self.touch.start_y = self.touch.y
                self.touch.current_touch_id = event.finger_id

                # Check virtual buttons first
                handled = False
                for btn in self.buttons:
                    if btn.contains(self.touch.x, self.touch.y, screen_w, screen_h):
                        btn.pressed = True
                        handled = True
                        self._action_queue.add(btn.action)
                        break

                if not handled:
                    # Start paddle tracking (relative)
                    self.touch.paddle_x = None

            elif event.type == pygame.FINGERUP:
                if event.finger_id == self.touch.current_touch_id:
                    # Was it a short tap (not a drag)?
                    dx = abs(self.touch.x - self.touch.start_x)
                    dy = abs(self.touch.y - self.touch.start_y)
                    if dx < 20 and dy < 20 and not self._action_queue:
                        self.touch.tapped = True
                        self._menu_action = "confirm"
                        self._menu_click_pos = (self.touch.x, self.touch.y)
                    self.touch.active = False
                    self.touch.current_touch_id = None
                    self.touch.paddle_x = None
                    for btn in self.buttons:
                        btn.pressed = False

            elif event.type == pygame.FINGERMOTION:
                if event.finger_id == self.touch.current_touch_id:
                    self.touch.x = int(event.x * screen_w)
                    self.touch.y = int(event.y * screen_h)

        # Also handle MOUSEBUTTONDOWN for desktop testing
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check if touch isn't already active
                if not self.touch.active:
                    # Check virtual buttons
                    for btn in self.buttons:
                        if btn.contains(event.pos[0], event.pos[1], screen_w, screen_h):
                            btn.pressed = True
                            self._action_queue.add(btn.action)
                            break
                    else:
                        # Treat as menu click
                        self._menu_click_pos = event.pos
                        self._menu_action = "confirm"

            elif event.type == pygame.MOUSEBUTTONUP:
                for btn in self.buttons:
                    btn.pressed = False

    def paddle_target_x(self, screen_w):
        """Return the X position the paddle should move to, or None."""
        if not self.touch.active or self._action_queue:
            return None
        return self.touch.x

    def wants_action(self, action):
        """Check if a virtual button action was triggered this frame."""
        return action in self._action_queue

    def menu_action(self):
        """Return (action, click_pos) or None for menu taps."""
        if self._menu_action:
            return (self._menu_action, self._menu_click_pos)
        return None

    def draw(self, surface, screen_w, screen_h):
        """Draw virtual buttons and instructions on the game surface."""
        for btn in self.buttons:
            btn.draw(surface, screen_w, screen_h)

        # Small hint text for first-time users
        if not self.touch.active:
            font = pygame.font.Font(None, 18)
            hint = font.render("Touch screen to move paddle", True, (120, 140, 160))
            hint.set_alpha(80)
            hx = (screen_w - hint.get_width()) // 2
            hy = screen_h - 30
            surface.blit(hint, (hx, hy))
