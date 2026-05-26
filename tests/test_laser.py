"""Tests for LaserBullet behavior"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import game.roguelite.bullet as bullet_module


class TestLaserBullet(unittest.TestCase):
    def test_laser_bullet_init(self):
        """Test that a LaserBullet initializes at the correct position."""
        start_pos = (100, 200)
        bullet = bullet_module.LaserBullet(start_pos)
        
        self.assertEqual(bullet.x, start_pos[0])
        self.assertEqual(bullet.y, start_pos[1])
        self.assertTrue(bullet.active)
        self.assertTrue(hasattr(bullet, 'speed'))

    def test_laser_bullet_moves_up(self):
        """Test that the laser bullet moves vertically."""
        bullet = bullet_module.LaserBullet((50, 50))
        speed = bullet.speed
        
        bullet.update(1/60)
        bullet.update(1/60)
        
        # After 2 updates, Y should be significantly lower (moving up on screen)
        self.assertLess(bullet.y, 50 - speed)

    def test_laser_bullet_deactivates_off_screen(self):
        """Test that the bullet becomes inactive when it moves above the top edge."""
        bullet = bullet_module.LaserBullet((50, 0))
        bullet.update(1/60) # Move above the top
        
        self.assertFalse(bullet.active)

    def test_ricochet_bullet_bounces_off_side_wall(self):
        """Test that bouncing projectiles reverse horizontal travel at walls."""
        bullet = bullet_module.LaserBullet((198, 100),.ndx=5,.ndy=-1, bounces=1, bounds_width=200)

        bullet.update(1 / 60)

        self.assertTrue(bullet.active)
        self.assertLess(bullet.ndx, 0)
        self.assertEqual(bullet.bounces, 0)


if __name__ == '__main__':
    unittest.main()
