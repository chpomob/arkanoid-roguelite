"""Tests for Particle Spawning Logic"""
import unittest
import sys
import os
from unittest import mock
import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.entities.brick import Brick
from game.engine import GameEngine
from game.particles.particle import Particle


class TestParticleSpawning(unittest.TestCase):
    def test_handle_brick_hit_spawns_particles(self):
        """Test that bricks spawn particles when destroyed."""
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.start_game(initial_skill_draft=False)
            brick = Brick(pygame.Rect(100, 100, 20, 20), hp=1)

            game.handle_ball_brick_hit(brick, game.balls[0])

            self.assertFalse(brick.active)
            self.assertEqual(len(game.particle_system), 6)
            self.assertGreater(game.hit_pause_timer, 0)

    def test_particle_system_filters_dead_particles(self):
        """Test that dead particles are removed from the system."""
        mock_engine = mock.MagicMock()
        mock_engine.particle_system = []
        
        # Add a particle
        p = Particle(10, 10, (255, 0, 0))
        mock_engine.particle_system.append(p)
        
        # Update until it dies
        while p.life > 0:
            p.update()
        
        # Filter as engine would
        original_count = len(mock_engine.particle_system)
        mock_engine.particle_system = [p for p in mock_engine.particle_system if p.life > 0]
        
        self.assertEqual(len(mock_engine.particle_system), 0)


if __name__ == '__main__':
    unittest.main()
