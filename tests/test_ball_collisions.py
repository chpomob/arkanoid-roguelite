"""Tests for Ball collision mechanics"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.viewport import Viewport
import pygame
import game.entities.ball as ball_module
import game.entities.paddle as paddle_module
import game.entities.brick as brick_module
import math


class TestPaddleBallCollision(unittest.TestCase):
    def test_bounce_dynamics(self):
        """Test that ball bounces off paddle."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(Viewport(width, height))
        
        # Create a ball that matches our intended rect position
        ball = ball_module.Ball(Viewport(width, height), paddle)
        
        # Position ball to clearly overlap paddle
        # Paddle is at bottom, moving down
        target_y = paddle.rect.centery - ball.nsize - 1
        target_x = paddle.rect.centerx
        
        # Update internal ball state
        ball.nx = target_x
        ball.ny = target_y
        ball.rect.topleft = (ball.nx - ball.nsize/2, ball.ny - ball.nsize/2)
        ball.ndy = 5
        
        mock_layers = []
        ball.update(width, height, mock_layers)
        
        # Should have bounced back up .ndy must be negative)
        self.assertLess(ball.ndy, 0)
        self.assertAlmostEqual(ball.rect.bottom, paddle.rect.top, places=0)

    def test_angle_variation(self):
        """Test that hitting the edge of the paddle changes horizontal direction."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(Viewport(width, height))
        ball = ball_module.Ball(Viewport(width, height), paddle)
        
        # Hit the right side of the paddle (ensure actual overlap)
        target_x = paddle.rect.centerx + (paddle.rect.width / 2) - 5
        target_y = paddle.rect.y - (ball.nsize // 2)
        
        ball.nx = target_x
        ball.ny = target_y
        ball.rect.center = (int(target_x), int(target_y))
        ball.ndy = 5
        initial.ndx = ball.ndx
        
        mock_layers = []
        ball.update(width, height, mock_layers)
        
        # Should have bounced back up
        self.assertLess(ball.ndy, 0)

    def test_center_hit_keeps_horizontal_motion(self):
        """Test that center hits do not create a perfect vertical bounce."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(Viewport(width, height))
        ball = ball_module.Ball(Viewport(width, height), paddle)

        ball.nx = paddle.rect.centerx
        ball.ny = paddle.rect.y - (ball.nsize // 2)
        ball.rect.center = (int(ball.nx), int(ball.ny))
        ball.ndx = 0
        ball.ndy = 5

        ball.update(width, height, [])

        self.assertLess(ball.ndy, 0)
        self.assertGreater(abs(ball.ndx), 0.3)

    def test_paddle_position_progressively_changes_angle(self):
        """Test that hits farther from center produce wider bounce angles."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(Viewport(width, height))
        ball = ball_module.Ball(Viewport(width, height), paddle)

        center = abs(ball.paddle_bounce_angle(0.08, 0, 5))
        mid = abs(ball.paddle_bounce_angle(0.45, 0, 5))
        edge = abs(ball.paddle_bounce_angle(0.95, 0, 5))

        self.assertLess(center, mid)
        self.assertLess(mid, edge)
        self.assertLessEqual(edge, math.radians(68))

    def test_arrival_angle_influences_paddle_bounce(self):
        """Test that incoming horizontal motion affects the outgoing paddle angle."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(Viewport(width, height))

        left_arrival = ball_module.Ball(Viewport(width, height), paddle)
        left_arrival.rect.center = (paddle.rect.centerx, paddle.rect.y - left_arrival.nsize // 2)
        left_arrival.x = left_arrival.rect.centerx
        left_arrival.y = left_arrival.rect.centery
        left_arrival.ndx = -4
        left_arrival.ndy = 5

        right_arrival = ball_module.Ball(Viewport(width, height), paddle)
        right_arrival.rect.center = (paddle.rect.centerx, paddle.rect.y - right_arrival.nsize // 2)
        right_arrival.x = right_arrival.rect.centerx
        right_arrival.y = right_arrival.rect.centery
        right_arrival.ndx = 4
        right_arrival.ndy = 5

        left_arrival.bounce_off_paddle()
        right_arrival.bounce_off_paddle()

        self.assertLess(left_arrival.ndx, 0)
        self.assertGreater(right_arrival.ndx, 0)
        self.assertGreater(right_arrival.ndx, left_arrival.ndx)

    def test_edge_hit_still_dominates_arrival_angle(self):
        """Test that paddle position remains stronger than incoming angle."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(Viewport(width, height))
        ball = ball_module.Ball(Viewport(width, height), paddle)

        ball.rect.center = (paddle.rect.centerx + paddle.rect.width // 2 - 4, paddle.rect.y - ball.nsize // 2)
        ball.nx = ball.rect.centerx
        ball.ny = ball.rect.centery
        ball.ndx = -4
        ball.ndy = 5

        ball.bounce_off_paddle()

        self.assertGreater(ball.ndx, 0)

    def test_bounce_preserves_current_speed(self):
        """Test that paddle bounce keeps the current speed magnitude."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(Viewport(width, height))
        ball = ball_module.Ball(Viewport(width, height), paddle)

        ball.nx = paddle.rect.centerx + 20
        ball.ny = paddle.rect.y - (ball.nsize // 2)
        ball.rect.center = (int(ball.nx), int(ball.ny))
        ball.ndx = 3
        ball.ndy = 7

        before = math.hypot(ball.ndx, ball.ndy)
        ball.update(width, height, [])
        after = math.hypot(ball.ndx, ball.ndy)

        self.assertAlmostEqual(after, before, places=5)


class TestBrickBallCollision(unittest.TestCase):
    def test_brick_damage_on_hit(self):
        """Test that ball hitting a brick damages it."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(Viewport(width, height))
        ball = ball_module.Ball(Viewport(width, height), paddle)
        brick = brick_module.Brick(pygame.Rect(500, 500, 20, 20), hp=2)
        
        # Position ball center exactly on the brick center
        brick_center = brick.rect.center
        ball.nx = brick_center[0]
        ball.ny = brick_center[1]
        ball.rect.center = brick_center
        ball.ndy = 3
        
        grid = brick_module.BrickGrid(1024, 768)
        grid.bricks.append(brick)
        
        layers = [grid]
        ball.update(1024, 768, layers)
        
        # Brick should have taken damage
        self.assertEqual(brick.hp, 1)

    def test_brick_destroyed(self):
        """Test that brick is removed from grid after HP reaches 0."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(Viewport(width, height))
        ball = ball_module.Ball(Viewport(width, height), paddle)
        brick = brick_module.Brick(pygame.Rect(500, 500, 20, 20), hp=1)
        
        brick_center = brick.rect.center
        ball.nx = brick_center[0]
        ball.ny = brick_center[1]
        ball.rect.center = brick_center
        ball.ndy = 3
        
        grid = brick_module.BrickGrid(1024, 768)
        grid.bricks.append(brick)
        
        layers = [grid]
        ball.update(1024, 768, layers)
        
        self.assertFalse(brick.active)

    def test_vertical_gap_hit_between_two_bricks_bounces_vertically(self):
        """Test that a vertical shot in a narrow brick gap avoids side trapping."""
        width, height = 800, 600
        paddle = paddle_module.Paddle(Viewport(width, height))
        ball = ball_module.Ball(Viewport(width, height), paddle)
        left = brick_module.Brick(pygame.Rect(100, 100, 40, 25), hp=2)
        right = brick_module.Brick(pygame.Rect(150, 100, 40, 25), hp=2)
        grid = brick_module.BrickGrid(width, height)
        grid.bricks = [left, right]

        ball.nx = 145
        ball.ny = 134
        ball.rect.center = (int(ball.nx), int(ball.ny))
        ball.ndx = 0
        ball.ndy = -6

        hit = ball.update(width, height, [grid])

        self.assertIn(hit, (left, right))
        self.assertGreater(ball.ndy, 0)
        self.assertGreaterEqual(abs(ball.ndx), ball.min_horizontal_speed)

    def test_opposing_brick_side_contacts_choose_vertical_axis(self):
        """Test that simultaneous left/right brick contacts honor vertical travel."""
        width, height = 800, 600
        paddle = paddle_module.Paddle(Viewport(width, height))
        ball = ball_module.Ball(Viewport(width, height), paddle)
        left = brick_module.Brick(pygame.Rect(100, 100, 40, 25), hp=2)
        right = brick_module.Brick(pygame.Rect(150, 100, 40, 25), hp=2)

        ball.rect.center = (145, 122)
        ball.nx = ball.rect.centerx
        ball.ny = ball.rect.centery
        ball.previous_rect = ball.rect.move(0, 6)
        ball.ndx = 0
        ball.ndy = -6

        axis = ball.brick_collision_axis(left, [left, right])

        self.assertEqual(axis, "vertical")


if __name__ == '__main__':
    unittest.main()
