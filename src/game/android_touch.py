"""
Android touch input handler — logical 1024x768 space.

Virtual buttons and paddle tracking operate in game logic coordinates,
converting screen touches via the Viewport.
"""

import pygame


# Virtual button zones in logical 1024x768 pixels
BUTTONS = [
    {"action": "pause",   "rect": pygame.Rect(874, 16,  130, 44),  "label": "Pause", "color": (200, 180, 60)},
    {"action": "up",      "rect": pygame.Rect( 20, 680, 60, 60),   "label": "Cannon", "color": (220, 100, 60)},
    {"action": "down",    "rect": pygame.Rect( 90, 680, 60, 60),   "label": "Well", "color": (60, 120, 220)},
]


class VirtualButton:
    def __init__(self, action, rect, label, color):
        self.action = action
        self.rect = rect
        self.label = label
        self.color = color
        self.pressed = False

    def draw(self, surface):
        c = tuple(min(255, x + 40) for x in self.color) if self.pressed else self.color
        alpha = 220 if self.pressed else 140
        bg = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        bg.fill((*c, alpha))
        pygame.draw.rect(bg, (*c, alpha), bg.get_rect(), border_radius=6)
        surface.blit(bg, self.rect)

        font = pygame.font.Font(None, max(14, self.rect.height - 8))
        text = font.render(self.label, True, (255, 255, 255))
        tx = self.rect.x + (self.rect.width - text.get_width()) // 2
        ty = self.rect.y + (self.rect.height - text.get_height()) // 2
        surface.blit(text, (tx, ty))


class AndroidInput:
    """Touch → logical 1024x768 paddle tracking + virtual buttons."""

    def __init__(self):
        self.buttons = [VirtualButton(**b) for b in BUTTONS]
        self.touch_active = False
        self.touch_lx = 0     # logical X (pixels)
        self.touch_ly = 0     # logical Y
        self._action = None   # action triggered this frame
        self._click_pos = None  # logical click position for menus
        self._finger_id = None

    def process(self, events, viewport):
        """Process pygame events. viewport converts screen→logical coords."""
        self._action = None
        self._click_pos = None

        for event in events:
            if event.type == pygame.FINGERDOWN:
                lx, ly = viewport.from_screen(
                    int(event.x * viewport.sw),
                    int(event.y * viewport.sh),
                )
                self.touch_active = True
                self.touch_lx = lx
                self.touch_ly = ly
                self._finger_id = event.finger_id

                for btn in self.buttons:
                    if btn.rect.collidepoint(lx, ly):
                        btn.pressed = True
                        self._action = btn.action
                        break
                else:
                    self._click_pos = (lx, ly)

            elif event.type == pygame.FINGERMOTION:
                if event.finger_id == self._finger_id:
                    lx, ly = viewport.from_screen(
                        int(event.x * viewport.sw),
                        int(event.y * viewport.sh),
                    )
                    self.touch_lx = lx
                    self.touch_ly = ly

            elif event.type == pygame.FINGERUP:
                if event.finger_id == self._finger_id:
                    self.touch_active = False
                    self._finger_id = None
                    for btn in self.buttons:
                        btn.pressed = False

            # Mouse fallback for desktop testing
            if event.type == pygame.MOUSEBUTTONDOWN:
                for btn in self.buttons:
                    if btn.rect.collidepoint(event.pos):
                        btn.pressed = True
                        self._action = btn.action
                        break
                else:
                    self._click_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONUP:
                for btn in self.buttons:
                    btn.pressed = False

    def paddle_target_x(self):
        """Logical X position for paddle, or None."""
        if self.touch_active and not self._action:
            return self.touch_lx
        return None

    def action(self):
        """Virtual button action triggered this frame, or None."""
        return self._action

    def click_pos(self):
        """Logical click position for menus, or None."""
        return self._click_pos

    def draw(self, surface):
        """Draw virtual buttons on the logical surface."""
        for btn in self.buttons:
            btn.draw(surface)
