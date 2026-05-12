"""Tests for moving enemies and enemy shots."""
import os
import sys
import unittest
from unittest import mock

import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.entities.enemy import Enemy, EnemyShot
from game.engine import GameEngine


class TestEnemies(unittest.TestCase):
    def test_enemy_moves_and_bounces_inside_bounds(self):
        enemy = Enemy(12, 100, bounds=(10, 30), speed=25)

        enemy.update(1 / 60)

        self.assertEqual(enemy.direction, -1)
        self.assertEqual(enemy.x, 30)

    def test_enemy_fires_when_ready(self):
        enemy = Enemy(100, 100, bounds=(30, 200), cooldown=0.01)
        enemy.update(1)

        shots = enemy.fire()

        self.assertIsInstance(shots, list)
        self.assertEqual(len(shots), 1)
        self.assertIsInstance(shots[0], EnemyShot)
        self.assertGreater(enemy.fire_timer, 0)

    def test_enemy_shot_can_move_diagonally(self):
        shot = EnemyShot((100, 100), dx=1.5)

        shot.update(1 / 60)

        self.assertGreater(shot.x, 100)
        self.assertEqual(shot.rect.centerx, int(shot.x))

    def test_level_enemies_spawn_after_unlock_level(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.level = 7

            game.spawn_level_enemies()

            self.assertEqual(len(game.enemies), 2)

    def test_enemy_shot_costs_one_life(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.start_game(initial_skill_draft=False)
            shot = EnemyShot(game.paddle.rect.center)
            game.enemy_shots = [shot]

            game.handle_enemy_shot_hits()

            self.assertEqual(game.paddle.lives, 2)
            self.assertEqual(game.enemy_shots, [])

    def test_player_bullet_can_destroy_enemy(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.start_game(initial_skill_draft=False)
            game.spawn_enemy(120, 120, speed=0, cooldown=10)
            bullet = mock.MagicMock()
            bullet.active = True
            bullet.damage = 1
            bullet.rect = game.enemies[0].rect.copy()
            game.bullets = [bullet]

            game.handle_bullet_hits()

            self.assertFalse(game.enemies[0].active)
            self.assertGreater(game.score, 0)


if __name__ == '__main__':
    unittest.main()
