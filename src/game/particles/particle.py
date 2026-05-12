import pygame
import random
import math


class Particle:
    """Glowing particle with spark variety, directional bias, and color lifecycle."""

    def __init__(self, x, y, color, speed=3, size_range=(1, 3), decay_range=(0.02, 0.05),
                 directional=False, angle_bias=None):
        self.x = float(x)
        self.y = float(y)
        self.start_color = color
        self.color = color
        self.size = random.randint(size_range[0], size_range[1])
        self.start_size = self.size

        # Directional or random velocity
        if directional and angle_bias is not None:
            spread = math.radians(random.uniform(-30, 30))
            angle = angle_bias + spread
            mag = random.uniform(speed * 0.5, speed)
            self.dx = math.cos(angle) * mag
            self.dy = math.sin(angle) * mag
        else:
            self.dx = random.uniform(-speed, speed)
            self.dy = random.uniform(-speed, speed)

        self.life = 1.0
        self.decay = random.uniform(decay_range[0], decay_range[1])
        # Spark type: 0=circle, 1=elongated
        self.spark_type = random.randint(0, 1)
        self.angle = random.uniform(0, math.pi * 2)
        self.rect = pygame.Rect(int(x), int(y), 1, 1)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= self.decay
        self.size = max(0.2, self.start_size * max(0.0, self.life) ** 0.6)
        # Color shifts toward white as it fades (hotter spark)
        t = 1.0 - self.life
        self.color = tuple(
            int(self.start_color[i] * (1 - t) + 255 * t * 0.5)
            for i in range(3)
        )
        # Slow down
        self.dx *= 0.985
        self.dy *= 0.985
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, screen):
        if self.life <= 0:
            return
        alpha = int(self.life * 220)
        if alpha < 5:
            return

        s = int(self.size)
        if s < 1:
            return

        # Draw on a small alpha surface for glow
        pad = s + 4
        surf = pygame.Surface((pad * 2, pad * 2), pygame.SRCALPHA)
        cx, cy = pad, pad

        if self.spark_type == 0:
            # Circular spark with glow
            for i in range(3, 0, -1):
                r = max(1, s + i)
                a = alpha // (i + 1)
                pygame.draw.circle(surf, (*self.color, a), (cx, cy), r)
            pygame.draw.circle(surf, (*self.color, alpha), (cx, cy), max(1, s))
            # Hot core
            core_a = min(alpha + 30, 255)
            pygame.draw.circle(surf, (255, 245, 235, core_a), (cx, cy), max(1, s // 2))
        else:
            # Elongated spark line
            length = s * 2
            dx = int(math.cos(self.angle) * length)
            dy = int(math.sin(self.angle) * length)
            for i in range(2, 0, -1):
                w = max(1, i + 1)
                a = alpha // (i + 1)
                pygame.draw.line(surf, (*self.color, a),
                                 (cx - dx // 2, cy - dy // 2),
                                 (cx + dx // 2, cy + dy // 2), w)
            pygame.draw.line(surf, (*self.color, alpha),
                             (cx - dx // 2, cy - dy // 2),
                             (cx + dx // 2, cy + dy // 2), max(1, s // 2 + 1))
            # Hot center dot
            pygame.draw.circle(surf, (255, 245, 235, min(alpha + 20, 255)),
                               (cx, cy), max(1, s // 3))

        screen.blit(surf, (int(self.x) - pad, int(self.y) - pad))
