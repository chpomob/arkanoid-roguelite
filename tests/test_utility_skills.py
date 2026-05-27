"""Tests for utility-focused roguelite skills."""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.viewport import Viewport
from game.entities.ball import Ball
from game.entities.paddle import Paddle
from game.roguelite.skill import Skill, SkillType
import game.roguelite.effects as effects_module
from game.roguelite.effects import RunState
import game.engine as engine_module
from game.viewport import Viewport


class TestUtilitySkills(unittest.TestCase):
    def test_magnet_pulls_falling_ball_toward_paddle(self):
        """Test that Magnet nudges a falling ball toward the paddle."""
        paddle = Paddle(Viewport(1024, 768))
        ball = Ball(Viewport(1024, 768), paddle)
        paddle.rect.centerx = 700
        ball.rect.centerx = 400
        ball.ndx = 0
        ball.ndy = 5

        effects_module.apply_magnet(ball, paddle, [Skill(SkillType.MAGNET, "Magnet")])

        self.assertGreater(ball.ndx, 0)

    def test_shield_does_not_prevent_ball_miss(self):
        """Test that Shield no longer overlaps with life-loss recovery."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.shield_charges = 1
        game.balls[0].rect.top = game.height + 1
        game.balls[0].y = game.height + 20

        game.update(1 / 60)

        self.assertEqual(game.paddle.lives, 2)
        self.assertEqual(game.shield_charges, 1)
        self.assertEqual(game.state, "PLAYING")

    def test_shield_blocks_enemy_damage(self):
        """Test that Shield consumes a charge against incoming damage."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.shield_charges = 1

        game.handle_enemy_hit_player()

        self.assertEqual(game.paddle.lives, 3)
        self.assertEqual(game.shield_charges, 0)

    def test_choice_adds_one_upgrade_option(self):
        """Test that Choice adds a fourth upgrade card."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.selected_skills = [Skill(SkillType.CHOICE, "Choice")]

        game.next_level()

        self.assertEqual(len(game.skill_cards), 4)

    def test_stacked_choice_adds_fifth_upgrade_option(self):
        """Test that a second Choice upgrade still improves future drafts."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.selected_skills = [Skill(SkillType.CHOICE, "Choice"), Skill(SkillType.CHOICE, "Choice")]

        game.next_level()

        self.assertEqual(len(game.skill_cards), 5)

    def test_drones_fire_projectiles_over_time(self):
        """Test that Drones fire auto-projectiles after their cooldown."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.selected_skills = [Skill(SkillType.DRONES, "Drones")]

        # Call update_helper_paddles enough times to trigger drone fire
        for _ in range(100):
            game.update_helper_paddles()

        self.assertGreater(len(game.bullets), 0)

    def test_echo_paddles_create_hover_helper(self):
        """Test that Echo Paddles add a drone-like hover paddle."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.selected_skills = [Skill(SkillType.ECHO_PADDLES, "Echo")]

        game.update_helper_paddles()

        self.assertEqual(len(game.paddle.extra_rects), 1)
        self.assertLess(game.paddle.extra_rects[0].centery, game.paddle.rect.centery)

    def test_stacked_echo_paddles_add_more_helpers(self):
        """Test that upgraded Echo Paddles add more hover coverage."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.selected_skills = [Skill(SkillType.ECHO_PADDLES, "Echo"), Skill(SkillType.ECHO_PADDLES, "Echo")]

        game.update_helper_paddles()

        self.assertEqual(len(game.paddle.extra_rects), 3)

    def test_patrol_paddles_create_moving_helper(self):
        """Test that Patrol Paddles add another drone-like helper."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.selected_skills = [Skill(SkillType.PATROL_PADDLES, "Patrol")]

        game.update_helper_paddles()

        self.assertEqual(len(game.paddle.extra_rects), 1)
        self.assertLess(game.paddle.extra_rects[0].centery, game.paddle.rect.centery)

    def test_split_charge_spawns_one_ball_and_consumes_charge(self):
        """Test that Split creates one extra ball from a paddle hit charge."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        ball = game.balls[0]
        ball.ndx = 2
        ball.ndy = -5
        ball.hit_paddle = True
        game.split_charges = 1

        game.trigger_split_charge(ball)

        self.assertEqual(len(game.balls), 2)
        self.assertEqual(game.split_charges, 0)
        self.assertLess(game.balls[1].ndx, 0)

    def test_volley_fires_two_spread_projectiles(self):
        """Test that Volley fires two angled projectiles."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.selected_skills = [Skill(SkillType.VOLLEY, "Volley")]
        ball = game.balls[0]

        game.fire_paddle_projectiles(ball)

        self.assertEqual(len(game.bullets), 2)
        self.assertLess(game.bullets[0].ndx, 0)
        self.assertGreater(game.bullets[1].ndx, 0)

    def test_ricochet_fires_bouncing_projectile(self):
        """Test that Ricochet creates a bouncing diagonal projectile."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.selected_skills = [Skill(SkillType.RICOCHET, "Ricochet")]
        ball = game.balls[0]
        ball.ndx = 2

        game.fire_paddle_projectiles(ball)

        self.assertEqual(len(game.bullets), 1)
        self.assertGreater(game.bullets[0].bounces, 0)
        self.assertGreater(game.bullets[0].ndx, 0)

    def test_seeker_fires_at_nearest_target(self):
        """Test that Seeker automatically creates an aimed projectile."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.selected_skills = [Skill(SkillType.SEEKER, "Seeker")]
        game.seeker_cooldown = 0

        fired = game.fire_seeker()

        self.assertTrue(fired)
        self.assertEqual(len(game.bullets), 1)
        self.assertNotEqual(game.bullets[0].ndy, -game.bullets[0].speed)
        self.assertGreater(game.seeker_cooldown, 0)

    def test_scatter_shot_fires_projectile_fan(self):
        """Test that Scatter Shot creates several low-damage projectiles."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.selected_skills = [Skill(SkillType.SCATTER_SHOT, "Scatter")]
        ball = game.balls[0]

        game.fire_paddle_projectiles(ball)

        self.assertGreaterEqual(len(game.bullets), 2)
        self.assertLess(game.bullets[0].ndx, 0)
        self.assertGreater(game.bullets[-1].ndx, 0)

    def test_piercing_shots_keep_projectile_active_after_brick_hit(self):
        """Test that Piercing Shots let a projectile continue after impact."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.selected_skills = [Skill(SkillType.PIERCING_SHOTS, "Pierce")]
        brick = game.brick_grid.bricks[0]
        bullet = engine_module.LaserBullet(brick.rect.center)
        game.bullets = [bullet]

        game.handle_bullet_hits()

        self.assertTrue(game.bullets[0].active)
        self.assertEqual(game.bullets[0].pierce_remaining, 0)

    def test_chain_spark_damages_nearby_brick(self):
        """Test that Chain Spark arcs damage to a nearby active brick."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.selected_skills = [Skill(SkillType.CHAIN_SPARK, "Spark")]
        source = game.brick_grid.bricks[0]
        target = min(
            [brick for brick in game.brick_grid.bricks if brick is not source and brick.active],
            key=lambda brick: abs(brick.rect.centerx - source.rect.centerx) + abs(brick.rect.centery - source.rect.centery),
        )
        target.hp = 3

        chained = game.apply_chain_spark(source)

        self.assertIn(target, chained)
        self.assertEqual(target.hp, 1)

    def test_stasis_field_slows_falling_ball_near_paddle(self):
        """Test that Stasis Field slows readable falling returns."""
        paddle = Paddle(Viewport(1024, 768))
        ball = Ball(Viewport(1024, 768), paddle)
        ball.rect.centerx = paddle.rect.centerx
        ball.rect.bottom = paddle.rect.y - 40
        ball.ndy = 6

        effects_module.apply_stasis_field(ball, paddle, [Skill(SkillType.STASIS_FIELD, "Stasis")])

        self.assertLess(ball.ndy, 6)

    def test_focus_shrinks_paddle_and_increases_damage(self):
        """Test that Focus trades paddle size for more brick damage."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        initial_width = game.paddle.nw
        focus = Skill(SkillType.FOCUS, "Focus")
        brick = game.brick_grid.bricks[0]
        brick.hp = 5

        effects_module.apply_skills_to_paddle(game.paddle, [focus])
        rs = RunState()
        effects_module.handle_brick_hit(brick, game.balls[0], [focus], rs)

        self.assertLess(game.paddle.nw, initial_width)
        self.assertEqual(brick.hp, 3)  # 5 - (1 base + 1 focus) = 3

    def test_wide_and_focus_combine_predictably(self):
        """Test that Wide offsets Focus without runaway paddle scaling."""
        paddle = Paddle(Viewport(1024, 768))
        skills = [
            Skill(SkillType.PADDLE_WIDE, "Wide"),
            Skill(SkillType.FOCUS, "Focus"),
        ]

        effects_module.apply_skills_to_paddle(paddle, skills)

        # Wide: +24px, Focus: -8px → net +16px at 800 width = 16/800
        self.assertAlmostEqual(paddle.nw, paddle.vp.legacy_x(100 + 16), places=3)

    def test_cannon_fires_from_up_active_skill(self):
        """Test that Cannon creates an active projectile with a cooldown."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        game.selected_skills = [Skill(SkillType.CANNON, "Cannon")]

        fired = game.fire_cannon()
        fired_again = game.fire_cannon()

        self.assertTrue(fired)
        self.assertFalse(fired_again)
        self.assertEqual(len(game.bullets), 1)
        self.assertGreaterEqual(game.bullets[0].damage, 1)  # base damage is 1
        self.assertGreater(game.cannon_cooldown, 0)

    def test_stacked_cannon_adds_spread_projectiles(self):
        """Test that upgraded Cannon adds side bolts without removing cooldown."""
        game = engine_module.GameEngine(800, 600)
        game.start_game(initial_skill_draft=False)
        first = Skill(SkillType.CANNON, "Cannon")
        second = Skill(SkillType.CANNON, "Cannon")
        game.selected_skills = [first, second]

        self.assertTrue(game.fire_cannon())

        self.assertEqual(len(game.bullets), 3)
        self.assertLess(game.bullets[1].ndx, 0)
        self.assertGreater(game.bullets[2].ndx, 0)

    def test_gravity_well_bends_and_slows_falling_ball(self):
        """Test that holding Down with Gravity Well pulls and slows falling balls."""
        paddle = Paddle(Viewport(1024, 768))
        ball = Ball(Viewport(1024, 768), paddle)
        paddle.rect.centerx = 700
        ball.rect.centerx = 400
        ball.ndx = 0
        ball.ndy = 6

        effects_module.apply_gravity_well(ball, paddle, [Skill(SkillType.GRAVITY_WELL, "Well")], active=True)

        self.assertGreater(ball.ndx, 0)
        self.assertLess(ball.ndy, 6)


if __name__ == '__main__':
    unittest.main()
