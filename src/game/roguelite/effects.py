from dataclasses import dataclass
from typing import Any
import random

from game.roguelite.skill import SkillType
from game.entities.ball import Ball
import math


@dataclass
class RunState:
    """Mutable state shared across effects functions for a single run."""
    energy: int = 0
    balls_count: int = 1


def skill_count(selected_skills: list, skill_type: SkillType) -> int:
    return sum(1 for skill in selected_skills if skill.type == skill_type)


def apply_skills_to_paddle(paddle, selected_skills: list) -> None:
    wide_count = skill_count(selected_skills, SkillType.PADDLE_WIDE)
    focus_count = skill_count(selected_skills, SkillType.FOCUS)
    # Convert old pixel bonuses to normalized via paddle's viewport
    vp = paddle.vp
    paddle.width_bonus = vp.legacy_x(wide_count * 24) - vp.legacy_x(min(32, focus_count * 8))
    paddle.update_rect()


def handle_skills(engine, selected_skills: list, run_state: RunState, heal_already_applied: bool = False) -> None:
    # Multi-ball: Adds N balls
    multi_ball_count = skill_count(selected_skills, SkillType.MULTI_BALL)
    current_balls = len(engine.balls)
    for i in range(multi_ball_count):
        new_ball = Ball(engine.viewport, engine.paddle, y_offset=engine.viewport.legacy_y((current_balls + i) * 12))
        new_ball.ndx = new_ball.speed * (-2 * ((run_state.balls_count + i) % 2) + 1)
        new_ball.ndy = -new_ball.speed
        new_ball.color = (100, 220, 255)  # cyan twin ball
        engine.balls.append(new_ball)
        run_state.balls_count += 1
        # Spawn split particles at the paddle
        from game.particles.particle import Particle
        for i in range(12):
            angle = math.radians(i * 30)
            engine.particle_system.append(Particle(
                engine.paddle.rect.centerx, engine.paddle.rect.centery - 5,
                (100, 220, 255), speed=4, size_range=(2, 4),
                directional=True, angle_bias=angle))

    for ball in engine.balls:
        apply_skills_to_ball(ball, selected_skills)

    if not heal_already_applied:
        apply_heal(engine.paddle, selected_skills)


def apply_vampire(paddle, current_energy: int, selected_skills: list = None) -> int:
    vampire_count = sum(1 for s in (selected_skills or []) if s.type.value == "vampire")
    threshold = 8 + vampire_count * 2
    if current_energy >= threshold:
        if paddle.lives < 5:
            paddle.lives += 1
            return current_energy - threshold
    return current_energy


def spawn_vampire_particles(engine):
    """Spawn crimson energy swirl when Vampirism heals."""
    from game.particles.particle import Particle
    cx, cy = engine.paddle.rect.centerx, engine.paddle.rect.y
    for i in range(10):
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(0, 30)
        px = cx + math.cos(angle) * dist
        py = cy + random.uniform(-10, 5)
        engine.particle_system.append(Particle(
            px, py, (200, 30, 40), speed=3, size_range=(2, 5),
            directional=True, angle_bias=math.radians(-90)))  # float upward


def damage_brick(brick, amount: int) -> bool:
    if hasattr(brick, "take_damage"):
        return brick.take_damage(amount)

    brick.hp -= amount
    brick.active = brick.hp > 0
    return not brick.active


def apply_skills_to_ball(ball: Ball, selected_skills: list) -> None:
    stabilizer_count = skill_count(selected_skills, SkillType.SPEED_UP)
    control_count = skill_count(selected_skills, SkillType.CONTROL)
    giant_count = skill_count(selected_skills, SkillType.GIANT_BALL)

    base_size = getattr(ball, "base_nsize", getattr(ball, "base_size", None))
    # Only check numeric values — skip mocks/None
    if isinstance(base_size, (int, float)):
        if base_size > 1.0:
            base_size = ball.vp.legacy_s(base_size)
    else:
        base_size = ball.vp.legacy_s(12)

    # Convert old pixel speeds to normalized via ball's viewport
    old_speed_px = max(3.0, 5 * (1 - stabilizer_count * 0.08))
    ball.speed = ball.vp.nspeed(old_speed_px)
    ball.nsize = min(ball.vp.legacy_s(24), base_size + ball.vp.legacy_s(giant_count * 3))
    # Giant balls leave a particle trail
    if giant_count > 0 and hasattr(ball, 'rect'):
        from game.particles.particle import Particle
        trail_chance = min(0.8, giant_count * 0.25)
        ball._giant_trail_chance = trail_chance
        ball._giant_color = ball.color if hasattr(ball, 'color') else (255, 200, 100)
    # Tempo also improves control (easier to track slower ball)
    angle_cap = 68 + control_count * 4 - (stabilizer_count * 3 if stabilizer_count > 0 else 0)
    ball.max_bounce_angle = math.radians(min(78, angle_cap))
    # Wide Guard: wider paddle naturally creates wider angles.
    # Compensate by capping the max angle so the ball stays controllable.
    wide_count = skill_count(selected_skills, SkillType.PADDLE_WIDE)
    if wide_count > 0:
        angle_reduction = math.radians(min(22, wide_count * 6))
        ball.max_bounce_angle = max(math.radians(38), ball.max_bounce_angle - angle_reduction)
    ball.center_nudge = min(0.22, 0.13 + control_count * 0.02)
    if hasattr(ball, "rect"):
        ball.rect.size = (ball.size, ball.size)
        if isinstance(getattr(ball, "x", None), (int, float)) and isinstance(getattr(ball, "y", None), (int, float)):
            ball.rect.center = (int(ball.x), int(ball.y))


def handle_brick_hit(brick, ball, selected_skills: list, run_state: RunState) -> bool:
    laser_count = skill_count(selected_skills, SkillType.LASER)
    laser_active = laser_count > 0

    dmg_count = skill_count(selected_skills, SkillType.DAMAGE)
    focus_count = skill_count(selected_skills, SkillType.FOCUS)
    crit_count = skill_count(selected_skills, SkillType.CRITICAL_HIT)
    ghost_count = skill_count(selected_skills, SkillType.GHOST_BALL)
    total_dmg = 1 + dmg_count + focus_count  # base 1, ghost no longer adds damage
    # Critical hit: % chance to double damage
    if crit_count > 0:
        import random
        crit_chance = min(0.40, crit_count * 0.10)
        if random.random() < crit_chance:
            total_dmg *= 2
            brick.hit_color = (255, 255, 0)
    else:
        brick.hit_color = (255, 180, 30) if total_dmg >= 3 else (255, 255, 255)
    if ghost_count > 0 and not (crit_count > 0):
        brick.hit_color = (150, 200, 255)

    damage_brick(brick, total_dmg)

    vampire_count = skill_count(selected_skills, SkillType.VAMPIRE)
    if vampire_count:
        run_state.energy += min(vampire_count, 2)  # cap energy per hit at 2

    return laser_active


def apply_heal(paddle, selected_skills: list) -> None:
    heal_count = skill_count(selected_skills, SkillType.HEAL)
    if heal_count > 0 and paddle.lives < 5:
        paddle.lives = min(5, paddle.lives + min(heal_count, 2))


def spawn_heal_particles(engine):
    """Spawn ascending golden-green sparkles when Repair heals."""
    from game.particles.particle import Particle
    cx, cy = engine.paddle.rect.centerx, engine.paddle.rect.y - 10
    for i in range(10):
        angle = math.radians(-90 + random.uniform(-30, 30))
        ox = cx + random.uniform(-20, 20)
        oy = cy + random.uniform(-5, 5)
        engine.particle_system.append(Particle(
            ox, oy, (120, 255, 140), speed=3, size_range=(2, 5),
            directional=True, angle_bias=angle))


def apply_explosive(engine, source_brick, selected_skills: list) -> list:
    blast_count = skill_count(selected_skills, SkillType.EXPLOSIVE)
    if blast_count == 0:
        return []

    radius = 40 + (blast_count - 1) * 10
    damaged = []
    destroyed_in_blast = []

    # Phase 1: Cross-pattern direct blast (double damage to neighbors)
    cross_dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    for brick in engine.brick_grid.bricks:
        if brick is source_brick or not brick.active:
            continue
        dx = brick.rect.centerx - source_brick.rect.centerx
        dy = brick.rect.centery - source_brick.rect.centery
        # Check if brick is directly adjacent (cross pattern)
        brick_w = getattr(engine.brick_grid, 'brick_width', 60)
        brick_h = getattr(engine.brick_grid, 'brick_height', 25)
        pad = getattr(engine.brick_grid, 'padding', 10)
        bw = brick_w + pad
        bh = brick_h + pad
        for cdx, cdy in cross_dirs:
            if abs(dx - cdx * bw) < bw * 0.6 and abs(dy - cdy * bh) < bh * 0.6:
                destroyed = damage_brick(brick, 2)  # double damage to neighbors
                brick.hit_color = (255, 140, 30)  # orange blast
                damaged.append(brick)
                if destroyed:
                    destroyed_in_blast.append(brick)
                break

    # Phase 2: Circular splash damage (1 HP to everything in radius)
    for brick in engine.brick_grid.bricks:
        if brick is source_brick or not brick.active or brick in damaged:
            continue
        dx = brick.rect.centerx - source_brick.rect.centerx
        dy = brick.rect.centery - source_brick.rect.centery
        if math.hypot(dx, dy) <= radius:
            destroyed = damage_brick(brick, 1)
            brick.hit_color = (255, 200, 80)  # yellow splash
            damaged.append(brick)
            if destroyed:
                destroyed_in_blast.append(brick)

    # Phase 3: Chain reaction (level 2+): destroyed bricks may explode too
    if blast_count >= 2:
        chain_chance = min(0.6, blast_count * 0.15)
        import random
        for chain_brick in destroyed_in_blast[:]:
            if random.random() < chain_chance:
                chain_damaged = _explosive_splash(engine, chain_brick, radius * 0.7)
                for b in chain_damaged:
                    if b not in damaged:
                        b.hit_color = (255, 100, 20)
                        damaged.append(b)

    return damaged


def _explosive_splash(engine, source_brick, radius):
    """Small secondary explosion (chain reaction)."""
    damaged = []
    for brick in engine.brick_grid.bricks:
        if brick is source_brick or not brick.active:
            continue
        dx = brick.rect.centerx - source_brick.rect.centerx
        dy = brick.rect.centery - source_brick.rect.centery
        if math.hypot(dx, dy) <= radius:
            damage_brick(brick, 1)
            damaged.append(brick)
    return damaged


def apply_magnet(ball: Ball, paddle, selected_skills: list) -> None:
    magnet_count = skill_count(selected_skills, SkillType.MAGNET)
    if magnet_count == 0 or ball.dy <= 0:
        return

    delta = paddle.rect.centerx - ball.rect.centerx
    pull = max(-0.18 * magnet_count, min(0.18 * magnet_count, delta * 0.002 * magnet_count))
    ball.dx += pull
    max_dx = max(1.0, ball.speed * 0.9)
    ball.dx = max(-max_dx, min(max_dx, ball.dx))


def apply_gravity_well(ball: Ball, paddle, selected_skills: list, active: bool) -> None:
    well_count = skill_count(selected_skills, SkillType.GRAVITY_WELL)
    if not active or well_count == 0 or ball.dy <= 0:
        return

    delta = paddle.rect.centerx - ball.rect.centerx
    pull = max(-0.25 * well_count, min(0.25 * well_count, delta * 0.002 * well_count))
    ball.dx += pull
    ball.dy = max(2.4, ball.dy * (0.94 - min(0.08, well_count * 0.02)))
    max_dx = max(1.0, ball.speed * 1.05)
    ball.dx = max(-max_dx, min(max_dx, ball.dx))


def apply_stasis_field(ball: Ball, paddle, selected_skills: list) -> None:
    stasis_count = skill_count(selected_skills, SkillType.STASIS_FIELD)
    if stasis_count == 0 or ball.dy <= 0:
        return

    close_to_paddle = ball.rect.bottom >= paddle.rect.y - 260
    horizontally_relevant = abs(ball.rect.centerx - paddle.rect.centerx) <= 260
    if not close_to_paddle or not horizontally_relevant:
        return

    # Also slightly slow horizontal movement for better control
    slow_h = 0.995 - min(0.030, stasis_count * 0.008)
    ball.dx *= slow_h
    slow = 0.97 - min(0.06, stasis_count * 0.015)
    ball.dy = max(2.8, ball.dy * slow)


def apply_time_warp(ball, paddle, selected_skills: list) -> None:
    """Slows ball when near paddle, giving reaction time."""
    warp_count = sum(1 for s in selected_skills if s.type.value == "timewarp")
    if warp_count == 0:
        return
    zone = 160 + warp_count * 30
    if ball.dy > 0 and ball.rect.bottom >= paddle.rect.y - zone:
        slow = 0.92 - warp_count * 0.03
        ball.dy *= slow
        ball.dx *= slow


def apply_ghost_ball(brick, ball, selected_skills):
    """Ball pierces first brick without bouncing. Returns True if pierced."""
    ghost_count = sum(1 for s in selected_skills if s.type.value == "ghost")
    if ghost_count == 0 or ball is None:
        return False
    return True  # Engine handles the pierce logic


def apply_score_boost(score, selected_skills):
    """Multiply score by boost factor."""
    boost_count = sum(1 for s in selected_skills if s.type.value == "score+")
    if boost_count == 0:
        return score
    mult = 1.3 + (boost_count - 1) * 0.3
    return int(score * mult)


def apply_life_steal(engine, selected_skills):
    """Chance to restore life on brick destruction."""
    steal_count = sum(1 for s in selected_skills if s.type.value == "steal")
    if steal_count == 0:
        return
    import random
    chance = min(0.4, steal_count * 0.1)
    if random.random() < chance and engine.paddle.lives < 5:
        engine.paddle.lives += 1
        from game.particles.particle import Particle
        cx, cy = engine.paddle.rect.centerx, engine.paddle.rect.y
        for i in range(12):
            angle = math.radians(i * 30)
            engine.particle_system.append(Particle(
                cx, cy, (255, 80, 60), speed=4, size_range=(2, 5),
                directional=True, angle_bias=angle))
