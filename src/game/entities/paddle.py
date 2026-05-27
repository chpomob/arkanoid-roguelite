import pygame
from game.assets import draw_paddle_sprite, mix

class Paddle:
    def __init__(self, screen_width, screen_height, color=(0, 228, 54), width=100, height=15):
        self.base_width = width
        self.width = width
        self.width_bonus = 0
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.height = height
        self.x = (screen_width - self.width) / 2
        self.y = screen_height - 40
        self.speed = 7
        self.color = color
        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        self.lives = 3
        self.is_alive = True
        self.last_move_direction = 1
        self.extra_rects = []

    def add_width(self, amount):
        self.width_bonus += amount
        self.update_rect()

    def move(self, screen_width, keys, keybindings=None):
        self.last_move_direction = 0
        left_pressed = keybindings.action_down(keys, "left") if keybindings else keys[pygame.K_LEFT]
        right_pressed = keybindings.action_down(keys, "right") if keybindings else keys[pygame.K_RIGHT]

        if left_pressed:
            self.rect.x -= self.speed
            self.last_move_direction = -1
        if right_pressed:
            self.rect.x += self.speed
            self.last_move_direction = 1
        
        if self.rect.x < 0:
            self.rect.x = 0
        if self.rect.x + self.width > screen_width:
            self.rect.x = screen_width - self.width
        self.x = self.rect.x

    def update_rect(self):
        self.width = max(52, self.base_width + self.width_bonus)
        self.rect.width = self.width
        # Keep centered
        self.rect.x = (self.screen_width - self.rect.width) / 2
        self.x = self.rect.x

    def draw(self, screen, feedback=0.0):
        feedback = max(0.0, min(1.0, feedback))
        for rect in self.extra_rects:
            self.draw_segment(screen, rect, mix((70, 212, 255), (255, 255, 255), feedback * 0.45))
        self.draw_segment(screen, self.rect, mix(self.color, (255, 255, 255), feedback * 0.55))

    def draw_segment(self, screen, rect, color):
        draw_paddle_sprite(screen, rect, color)

    def reset(self, screen_width, screen_height):
        self.lives = 3
        self.is_alive = True
        self.rect.x = (screen_width - self.width) / 2
        self.rect.y = screen_height - 40
        self.x = self.rect.x
        self.y = self.rect.y
