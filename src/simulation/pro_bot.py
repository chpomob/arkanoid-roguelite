"""ProBot — simulates a super-skilled player with optimal decision-making.

Features:
- Ball trajectory prediction (anticipates where ball will land)
- Perfect pixel-precision paddle positioning
- Smart skill evaluation and drafting
- Optimal active skill usage timing
- Laser anticipation and dodging
"""

from game.roguelite.skill import SkillType, SKILL_GUIDE, skill_synergy
from simulation.bot import SimpleBot


# Skill tier list for drafting priority (based on benchmark data)
SKILL_TIER = {
    # S-tier: sustain
    SkillType.VAMPIRE: 10,
    SkillType.HEAL: 9,
    # A-tier: strong offense
    SkillType.SCATTER_SHOT: 8,
    SkillType.EXPLOSIVE: 8,
    SkillType.SEEKER: 7,
    SkillType.LASER: 7,
    SkillType.CANNON: 7,
    # A-tier: defense/utility
    SkillType.SHIELD: 7,
    SkillType.MAGNET: 6,
    SkillType.GRAVITY_WELL: 6,
    SkillType.DRONES: 6,
    SkillType.ECHO_PADDLES: 6,
    SkillType.PATROL_PADDLES: 6,
    # A-tier: stats
    SkillType.DAMAGE: 7,
    SkillType.FOCUS: 6,
    SkillType.GIANT_BALL: 6,
    SkillType.CONTROL: 6,
    SkillType.MULTI_BALL: 6,
    SkillType.SPEED_UP: 5,
    # B-tier: situational
    SkillType.CHAIN_SPARK: 5,
    SkillType.RICOCHET: 5,
    SkillType.VOLLEY: 5,
    SkillType.SPLIT_CHARGE: 5,
    SkillType.PIERCING_SHOTS: 5,
    SkillType.PADDLE_WIDE: 4,
    SkillType.CHOICE: 4,
    SkillType.STASIS_FIELD: 4,
    SkillType.TIME_WARP: 6,
    SkillType.CRITICAL_HIT: 7,
    SkillType.GHOST_BALL: 7,
}


class ProBot(SimpleBot):
    """Super-skilled player bot with optimal decision-making."""

    def __init__(self, seed: int = 42, **kwargs):
        super().__init__(seed=seed, **kwargs)
        self._predicted_x = None

    def held_keys(self, engine) -> set:
        keys = set()

        # Menu confirm
        if engine.state in ("TITLE", "SKILL_SELECTION", "LEVEL_SUMMARY",
                            "BRICK_INTRO", "BOSS_INTRO", "GAMEOVER"):
            keys.add("confirm")
            if engine.state != "PLAYING":
                return keys

        if not engine.balls:
            return keys

        # Laser dodging (priority 1)
        dodge = self._dodge_shots(engine)
        if dodge:
            keys.add(dodge)
            return keys

        ball = engine.balls[0]
        paddle = engine.paddle

        # Predict where ball will cross the paddle line
        target_x = self._predict_landing(ball, paddle, engine)

        if target_x is not None:
            diff = target_x - paddle.rect.centerx
            if abs(diff) > 3:  # pixel-precise
                keys.add("left" if diff < 0 else "right")
            self._predicted_x = target_x
        elif ball.dy <= 0:
            # Ball moving up — position under its shadow for the return
            diff = ball.rect.centerx - paddle.rect.centerx
            if abs(diff) > 8:
                keys.add("left" if diff < 0 else "right")

        # Active skill usage
        if engine.state == "PLAYING":
            # Cannon: fire when ball is in upper half (near bricks)
            has_cannon = any(s.type == SkillType.CANNON for s in engine.selected_skills)
            if has_cannon and ball.rect.centery < engine.height * 0.45:
                keys.add("up")

            # Gravity Well: only when ball is falling and high up
            has_well = any(s.type == SkillType.GRAVITY_WELL for s in engine.selected_skills)
            if has_well and ball.dy > 0 and ball.rect.centery < engine.height * 0.4:
                keys.add("down")

        return keys

    def _predict_landing(self, ball, paddle, engine) -> float | None:
        """Predict where the ball will cross the paddle's y-level using step simulation."""
        if ball.dy <= 0:
            return None

        x, y = float(ball.rect.centerx), float(ball.rect.centery)
        dx, dy = float(ball.dx), float(ball.dy)
        target_y = paddle.rect.y - 12
        playfield_top = engine.playfield_top

        for _ in range(600):
            # Step forward
            x += dx
            y += dy

            # Wall bounces
            if x <= 1:
                x = 1; dx = abs(dx)
            elif x >= engine.width - 1:
                x = engine.width - 1; dx = -abs(dx)

            # Ceiling bounce
            if y <= playfield_top and dy < 0:
                y = playfield_top; dy = abs(dy)

            # Brick collision (check rect, not just point)
            if engine.brick_grid.top <= y <= engine.brick_grid.top + engine.brick_grid.rows * 35:
                for brick in engine.brick_grid.bricks:
                    if brick.active and brick.rect.collidepoint(x, y):
                        # Determine collision axis
                        if abs(dx) >= abs(dy):
                            dx = -dx
                        else:
                            dy = -dy
                        # Push ball outside brick
                        if dy > 0:
                            y = brick.rect.bottom + 2
                        break

            # Reached paddle
            if y >= target_y:
                return max(20, min(engine.width - 20, x))

            # Fell off screen
            if y > engine.height:
                return None

        return max(20, min(engine.width - 20, x))

    def events(self, engine, dt: float) -> list:
        evts = super().events(engine, dt)

        # Smart skill selection: pick the best available card
        if engine.state == "SKILL_SELECTION" and engine.skill_cards:
            best_card = self._pick_best_skill(engine)
            if best_card:
                # Click the best card
                evts.append(
                    __import__('pygame').event.Event(
                        1025,  # MOUSEBUTTONDOWN
                        {"pos": (best_card.rect.centerx, best_card.rect.centery), "button": 1},
                    )
                )

        return evts

    def _pick_best_skill(self, engine):
        """Evaluate available skill cards and return the best one."""
        cards = engine.skill_cards
        if not cards:
            return None

        best = cards[0]
        best_score = -1

        for card in cards:
            skill_type = card.skill.type
            score = SKILL_TIER.get(skill_type, 3)
            already_have = any(s.type == skill_type for s in engine.selected_skills)
            if not already_have:
                score += 2
            synergy_text = skill_synergy(skill_type)
            for existing in engine.selected_skills:
                if existing.type.name.lower() in synergy_text.lower():
                    score += 3
            if already_have and score < 6:
                score -= 2
            if score > best_score:
                best_score = score
                best = card

        return best


class VampirePro(ProBot):
    """ProBot that always picks VAMPIRE first, then uses ProBot logic."""

    def _pick_best_skill(self, engine):
        cards = engine.skill_cards
        if not cards:
            return None
        # Always pick VAMPIRE if available
        for card in cards:
            if card.skill.type == SkillType.VAMPIRE:
                return card
        return super()._pick_best_skill(engine)


class AggroPro(ProBot):
    """ProBot that prioritizes offensive skills."""

    def _pick_best_skill(self, engine):
        cards = engine.skill_cards
        if not cards:
            return None
        # Aggro tier: offense first, sustain second
        aggro_tier = [SkillType.SCATTER_SHOT, SkillType.EXPLOSIVE, SkillType.SEEKER,
                      SkillType.CANNON, SkillType.LASER, SkillType.VOLLEY, SkillType.RICOCHET]
        for skill in aggro_tier:
            for card in cards:
                if card.skill.type == skill:
                    return card
        return super()._pick_best_skill(engine)

    def held_keys(self, engine) -> set:
        keys = super().held_keys(engine)
        if engine.state == "PLAYING" and engine.balls:
            keys.add("up")  # always fire cannon if available
        return keys
