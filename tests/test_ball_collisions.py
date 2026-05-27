"""Tests for Ball collision mechanics"""
import inspect
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pygame
import game.engine as engine_module
import game.entities.ball as ball_module
import game.entities.paddle as paddle_module
import game.entities.brick as brick_module
import math


class SpatialOnlyLayer:
    def __init__(self, bricks, name=None, order_log=None):
        self._bricks = bricks
        self.name = name
        self.order_log = order_log
        self.query_count = 0
        self.query_calls = []

    @property
    def bricks(self):
        raise AssertionError("Ball.update must use query_rect() instead of iterating bricks")

    def query_rect(self, rect, active_only=True):
        self.query_count += 1
        self.query_calls.append((rect.copy(), active_only))
        if self.order_log is not None:
            self.order_log.append(self.name)
        return [
            candidate
            for candidate in self._bricks
            if (candidate.active or not active_only) and rect.colliderect(candidate.rect)
        ]


def position_ball_to_enter_brick_from_left(ball, brick, dx=2):
    ball.rect.midright = (brick.rect.left - 1, brick.rect.centery)
    ball.x = ball.rect.centerx
    ball.y = ball.rect.centery
    ball.dx = dx
    ball.dy = 0


class TestPaddleBallCollision(unittest.TestCase):
    def test_bounce_dynamics(self):
        """Test that ball bounces off paddle."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(width, height)
        
        # Create a ball that matches our intended rect position
        ball = ball_module.Ball(width, height, paddle)
        
        # Position ball to clearly overlap paddle
        # Paddle is at bottom, moving down
        target_y = paddle.rect.centery - ball.size - 1
        target_x = paddle.rect.centerx
        
        # Update internal ball state
        ball.x = target_x
        ball.y = target_y
        ball.rect.topleft = (ball.x - ball.size/2, ball.y - ball.size/2)
        ball.dy = 5
        
        mock_layers = []
        ball.update(width, height, mock_layers)
        
        # Should have bounced back up (dy must be negative)
        self.assertLess(ball.dy, 0)
        self.assertAlmostEqual(ball.rect.bottom, paddle.rect.top, places=0)

    def test_angle_variation(self):
        """Test that hitting the edge of the paddle changes horizontal direction."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(width, height)
        ball = ball_module.Ball(width, height, paddle)
        
        # Hit the right side of the paddle (ensure actual overlap)
        target_x = paddle.rect.centerx + (paddle.rect.width / 2) - 5
        target_y = paddle.rect.y - (ball.size // 2)
        
        ball.x = target_x
        ball.y = target_y
        ball.rect.center = (int(target_x), int(target_y))
        ball.dy = 5
        initial_dx = ball.dx
        
        mock_layers = []
        ball.update(width, height, mock_layers)
        
        # Should have bounced back up
        self.assertLess(ball.dy, 0)

    def test_center_hit_keeps_horizontal_motion(self):
        """Test that center hits do not create a perfect vertical bounce."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(width, height)
        ball = ball_module.Ball(width, height, paddle)

        ball.x = paddle.rect.centerx
        ball.y = paddle.rect.y - (ball.size // 2)
        ball.rect.center = (int(ball.x), int(ball.y))
        ball.dx = 0
        ball.dy = 5

        ball.update(width, height, [])

        self.assertLess(ball.dy, 0)
        self.assertGreater(abs(ball.dx), 0.3)

    def test_paddle_position_progressively_changes_angle(self):
        """Test that hits farther from center produce wider bounce angles."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(width, height)
        ball = ball_module.Ball(width, height, paddle)

        center = abs(ball.paddle_bounce_angle(0.08, 0, 5))
        mid = abs(ball.paddle_bounce_angle(0.45, 0, 5))
        edge = abs(ball.paddle_bounce_angle(0.95, 0, 5))

        self.assertLess(center, mid)
        self.assertLess(mid, edge)
        self.assertLessEqual(edge, math.radians(68))

    def test_arrival_angle_influences_paddle_bounce(self):
        """Test that incoming horizontal motion affects the outgoing paddle angle."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(width, height)

        left_arrival = ball_module.Ball(width, height, paddle)
        left_arrival.rect.center = (paddle.rect.centerx, paddle.rect.y - left_arrival.size // 2)
        left_arrival.x = left_arrival.rect.centerx
        left_arrival.y = left_arrival.rect.centery
        left_arrival.dx = -4
        left_arrival.dy = 5

        right_arrival = ball_module.Ball(width, height, paddle)
        right_arrival.rect.center = (paddle.rect.centerx, paddle.rect.y - right_arrival.size // 2)
        right_arrival.x = right_arrival.rect.centerx
        right_arrival.y = right_arrival.rect.centery
        right_arrival.dx = 4
        right_arrival.dy = 5

        left_arrival.bounce_off_paddle()
        right_arrival.bounce_off_paddle()

        self.assertLess(left_arrival.dx, 0)
        self.assertGreater(right_arrival.dx, 0)
        self.assertGreater(right_arrival.dx, left_arrival.dx)

    def test_edge_hit_still_dominates_arrival_angle(self):
        """Test that paddle position remains stronger than incoming angle."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(width, height)
        ball = ball_module.Ball(width, height, paddle)

        ball.rect.center = (paddle.rect.centerx + paddle.rect.width // 2 - 4, paddle.rect.y - ball.size // 2)
        ball.x = ball.rect.centerx
        ball.y = ball.rect.centery
        ball.dx = -4
        ball.dy = 5

        ball.bounce_off_paddle()

        self.assertGreater(ball.dx, 0)

    def test_bounce_preserves_current_speed(self):
        """Test that paddle bounce keeps the current speed magnitude."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(width, height)
        ball = ball_module.Ball(width, height, paddle)

        ball.x = paddle.rect.centerx + 20
        ball.y = paddle.rect.y - (ball.size // 2)
        ball.rect.center = (int(ball.x), int(ball.y))
        ball.dx = 3
        ball.dy = 7

        before = math.hypot(ball.dx, ball.dy)
        ball.update(width, height, [])
        after = math.hypot(ball.dx, ball.dy)

        self.assertAlmostEqual(after, before, places=5)


class TestBrickBallCollision(unittest.TestCase):
    # Spatial contract regressions live here because they protect Ball.update's brick collision path.
    def test_brick_grid_query_rect_signature_matches_spatial_contract(self):
        """Test that BrickGrid.query_rect keeps the contract Ball.update relies on."""
        signature = inspect.signature(brick_module.BrickGrid.query_rect)
        parameters = list(signature.parameters.values())

        self.assertEqual([parameter.name for parameter in parameters], ["self", "rect", "active_only"])
        self.assertEqual(parameters[2].default, True)

    def test_ball_update_uses_spatial_query_layer(self):
        """Test that Ball.update queries candidate bricks through the spatial index."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(width, height)
        ball = ball_module.Ball(width, height, paddle)
        brick = brick_module.Brick(pygame.Rect(500, 500, 20, 20), hp=2)
        brick.active = True
        self.assertTrue(brick.active)

        position_ball_to_enter_brick_from_left(ball, brick)
        layer = SpatialOnlyLayer([brick])

        hit = ball.update(width, height, [layer], apply_damage=True)

        self.assertIs(hit, brick)
        self.assertGreaterEqual(layer.query_count, 1)
        self.assertTrue(all(active_only for _, active_only in layer.query_calls))
        self.assertEqual(brick.hp, 1)

    def test_ball_update_requires_query_rect_layer(self):
        """Test that Ball.update does not silently fall back to iterating .bricks."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(width, height)
        ball = ball_module.Ball(width, height, paddle)
        brick = brick_module.Brick(pygame.Rect(500, 500, 20, 20), hp=2)
        brick.active = True
        position_ball_to_enter_brick_from_left(ball, brick)

        class BricksOnlyLayer:
            def __init__(self, bricks):
                self.bricks = bricks

        with self.assertRaises(AttributeError):
            ball.update(width, height, [BricksOnlyLayer([brick])])

    def test_ball_update_queries_all_layers_in_order(self):
        """Test that Ball.update keeps iterating spatial layers in caller order."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(width, height)
        ball = ball_module.Ball(width, height, paddle)
        brick = brick_module.Brick(pygame.Rect(500, 500, 20, 20), hp=2)
        brick.active = True
        position_ball_to_enter_brick_from_left(ball, brick)
        query_order = []
        empty_layer = SpatialOnlyLayer([], name="empty", order_log=query_order)
        target_layer = SpatialOnlyLayer([brick], name="target", order_log=query_order)

        hit = ball.update(width, height, [empty_layer, target_layer], apply_damage=True)

        self.assertIs(hit, brick)
        self.assertEqual(query_order, ["empty", "target"])
        self.assertGreaterEqual(empty_layer.query_count, 1)
        self.assertGreaterEqual(target_layer.query_count, 1)

    def test_engine_update_balls_passes_brick_grid_as_spatial_layer(self):
        """Test that GameEngine.update_balls passes BrickGrid itself to Ball.update."""
        try:
            game = engine_module.GameEngine(1024, 768)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")
        game.start_game(initial_skill_draft=False)

        brick = brick_module.Brick(pygame.Rect(500, 500, 20, 20), hp=200)
        brick.active = True
        layer = SpatialOnlyLayer([brick])
        ball = game.balls[0]
        position_ball_to_enter_brick_from_left(ball, brick)
        game.brick_grid = layer
        game.selected_skills = []

        active_balls = game.update_balls()

        self.assertEqual(active_balls, 1)
        self.assertGreaterEqual(layer.query_count, 1)
        self.assertEqual(brick.hp, 100)

    def test_brick_damage_on_hit(self):
        """Test that ball hitting a brick damages it."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(width, height)
        ball = ball_module.Ball(width, height, paddle)
        brick = brick_module.Brick(pygame.Rect(500, 500, 20, 20), hp=2)
        
        # Position ball center exactly on the brick center
        brick_center = brick.rect.center
        ball.x = brick_center[0]
        ball.y = brick_center[1]
        ball.rect.center = brick_center
        ball.dy = 3
        
        grid = brick_module.BrickGrid(1024, 768)
        grid.bricks.append(brick)
        
        layers = [grid]
        ball.update(1024, 768, layers)
        
        # Brick should have taken damage
        self.assertEqual(brick.hp, 1)

    def test_brick_destroyed(self):
        """Test that brick is removed from grid after HP reaches 0."""
        width, height = 1024, 768
        paddle = paddle_module.Paddle(width, height)
        ball = ball_module.Ball(width, height, paddle)
        brick = brick_module.Brick(pygame.Rect(500, 500, 20, 20), hp=1)
        
        brick_center = brick.rect.center
        ball.x = brick_center[0]
        ball.y = brick_center[1]
        ball.rect.center = brick_center
        ball.dy = 3
        
        grid = brick_module.BrickGrid(1024, 768)
        grid.bricks.append(brick)
        
        layers = [grid]
        ball.update(1024, 768, layers)
        
        self.assertFalse(brick.active)

    def test_vertical_gap_hit_between_two_bricks_bounces_vertically(self):
        """Test that a vertical shot in a narrow brick gap avoids side trapping."""
        width, height = 800, 600
        paddle = paddle_module.Paddle(width, height)
        ball = ball_module.Ball(width, height, paddle)
        left = brick_module.Brick(pygame.Rect(100, 100, 40, 25), hp=2)
        right = brick_module.Brick(pygame.Rect(150, 100, 40, 25), hp=2)
        grid = brick_module.BrickGrid(width, height)
        grid.bricks = [left, right]

        ball.x = 145
        ball.y = 134
        ball.rect.center = (int(ball.x), int(ball.y))
        ball.dx = 0
        ball.dy = -6

        hit = ball.update(width, height, [grid])

        self.assertIn(hit, (left, right))
        self.assertGreater(ball.dy, 0)
        self.assertGreaterEqual(abs(ball.dx), ball.min_horizontal_speed)

    def test_opposing_brick_side_contacts_choose_vertical_axis(self):
        """Test that simultaneous left/right brick contacts honor vertical travel."""
        width, height = 800, 600
        paddle = paddle_module.Paddle(width, height)
        ball = ball_module.Ball(width, height, paddle)
        left = brick_module.Brick(pygame.Rect(100, 100, 40, 25), hp=2)
        right = brick_module.Brick(pygame.Rect(150, 100, 40, 25), hp=2)

        ball.rect.center = (145, 122)
        ball.x = ball.rect.centerx
        ball.y = ball.rect.centery
        ball.previous_rect = ball.rect.move(0, 6)
        ball.dx = 0
        ball.dy = -6

        axis = ball.brick_collision_axis(left, [left, right])

        self.assertEqual(axis, "vertical")


if __name__ == '__main__':
    unittest.main()
