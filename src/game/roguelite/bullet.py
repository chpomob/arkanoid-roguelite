import pygame
from game.assets import draw_projectile_sprite

class LaserBullet:
    def __init__(self, start_pos, dx=0, dy=None, damage=100, color=(255, 0, 0), bounces=0, bounds_width=None, bounds_height=None):
        self.x = start_pos[0]
        self.y = start_pos[1]
        self.width = 4
        self.height = 10
        self.rect = pygame.Rect(self.x - 2, self.y - 5, self.width, self.height)
        self.speed = 15
        self.dx = dx
        self.dy = -self.speed if dy is None else dy
        self.damage = damage
        self.active = True
        self.color = color
        self.bounces = bounces
        self.bounds_width = bounds_width
        self.bounds_height = bounds_height

    def update(self, dt):
        self.x += self.dx
        self.y += self.dy
        self.rect.center = (self.x, self.y)

        if self.bounds_width is not None and (self.rect.left <= 0 or self.rect.right >= self.bounds_width):
            if self.bounces > 0:
                self.dx = -self.dx
                self.bounces -= 1
                if self.rect.left <= 0:
                    self.rect.left = 0
                elif self.rect.right >= self.bounds_width:
                    self.rect.right = self.bounds_width
                self.x = self.rect.centerx
            else:
                self.active = False
        
        if self.rect.bottom < 0 or (self.bounds_height is not None and self.rect.top > self.bounds_height):
            self.active = False
        
    # Backward-compat aliases
    @property
    def ndx(self): return self.dx
    @ndx.setter
    def ndx(self, v): self.dx = v

    @property
    def ndy(self): return self.dy
    @ndy.setter
    def ndy(self, v): self.dy = v
    def draw(self, screen):
        draw_projectile_sprite(screen, self.rect, self.color)
