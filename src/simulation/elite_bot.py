"""EliteBot — a genuinely skilled player bot for balance validation.

Features:
- Wall-bounce landing prediction (reliable, no brick bounce guessing)
- Brick weak-point targeting (aims at special bricks and clusters)
- Gap awareness (positions under ball when above bricks)
- Dynamic skill evaluation with synergy awareness
- Optimal active skill usage (Cannon, Gravity Well)
"""

import math
import pygame
from game.roguelite.skill import SkillType
from simulation.bot import SimpleBot


class EliteBot(SimpleBot):
    """Skilled player bot for accurate balance validation."""

    def __init__(self, seed: int = 42, **kwargs):
        super().__init__(seed=seed, **kwargs)
        self._stuck_frames = 0
        self._prev_bricks = 0

    # ── Core movement ──────────────────────────────────────────────

    def held_keys(self, engine) -> set:
        """Enhanced: wall-bounce prediction + brick targeting. Falls back to SimpleBot."""
        keys = super().held_keys(engine)

        if engine.state != "PLAYING" or not engine.balls:
            return keys

        ball = engine.balls[0]
        paddle = engine.paddle

        # Anti-stuck recovery
        active = sum(1 for b in engine.brick_grid.bricks if b.active)
        if active == self._prev_bricks:
            self._stuck_frames += 1
        else:
            self._stuck_frames = 0
        self._prev_bricks = active

        if self._stuck_frames > 400:
            return keys  # let SimpleBot's tracking + oscillation handle it

        # Try smarter positioning — only override if we have a better target
        target = self._compute_target(ball, paddle, engine)
        if target is not None:
            keys.discard("left")
            keys.discard("right")
            diff = target - paddle.rect.centerx
            if abs(diff) > 3:
                keys.add("left" if diff < 0 else "right")

        # Active skills
        self._use_active_skills(keys, ball, engine)

        return keys

    def _compute_target(self, ball, paddle, engine) -> float | None:
        """Compute optimal paddle target. Returns None to keep SimpleBot's default."""
        if ball.dy > 0:
            # Ball falling — predict landing, then bias toward valuable bricks
            landing = self._predict_landing(ball, engine, paddle)
            if landing is None:
                return None  # keep SimpleBot tracking
            # Bias toward brick clusters above the landing zone
            bias = self._brick_target_bias(landing, paddle, engine)
            return max(12, min(engine.width - 12, landing + bias))
        else:
            # Ball rising — use shadow position (SimpleBot already does this)
            return None

    # ── Ball prediction ────────────────────────────────────────────

    def _predict_landing(self, ball, engine, paddle) -> float | None:
        """Predict where ball crosses paddle line (walls + ceiling only, no bricks)."""
        x = float(ball.rect.centerx)
        y = float(ball.rect.centery)
        dx = float(ball.dx)
        dy = float(ball.dy)
        target_y = paddle.rect.y - 6
        playfield_top = engine.playfield_top
        w = engine.width

        for _ in range(600):
            x += dx
            y += dy
            if y >= target_y:
                return max(8, min(w - 8, x))
            if y > engine.height:
                return None
            if x <= 1:
                x = 1; dx = abs(dx)
            elif x >= w - 1:
                x = w - 1; dx = -abs(dx)
            if y <= playfield_top:
                y = playfield_top; dy = abs(dy)

        return max(8, min(w - 8, x))

    # ── Brick targeting ────────────────────────────────────────────

    def _brick_target_bias(self, landing_x, paddle, engine) -> float:
        """Calculate a small offset to aim at valuable bricks above the landing zone."""
        left_score = 0.0
        right_score = 0.0

        for brick in engine.brick_grid.bricks:
            if not brick.active:
                continue
            if brick.rect.bottom >= paddle.rect.y - 20:
                continue

            # Brick value: specials > low HP > high HP, closer = more valuable
            value = 1.0
            if brick.kind.value != "normal":
                value += 2.5
            if brick.hp <= 1:
                value += 1.5
            value *= brick.hp ** 0.3  # slight bonus for tough bricks

            # Distance weight: closer bricks matter more
            dist = abs(brick.rect.centerx - landing_x)
            if dist < 60:
                weight = value * (1.0 - dist / 60.0)
                if brick.rect.centerx < landing_x:
                    left_score += weight
                else:
                    right_score += weight

        if left_score + right_score < 0.01:
            return 0.0

        # Bias toward the side with more brick value
        return (right_score - left_score) * 6.0

    # ── Active skills ──────────────────────────────────────────────

    def _use_active_skills(self, keys, ball, engine):
        """Fire Cannon or use Gravity Well at optimal times."""
        has_cannon = any(s.type == SkillType.CANNON for s in engine.selected_skills)
        has_well = any(s.type == SkillType.GRAVITY_WELL for s in engine.selected_skills)

        if has_cannon and engine.cannon_cooldown <= 0:
            # Fire when cannon is aligned with brick clusters above
            if ball.rect.centery < engine.height * 0.48:
                bricks_above = sum(1 for b in engine.brick_grid.bricks
                                   if b.active and b.rect.centery < ball.rect.centery)
                if bricks_above > 2:
                    keys.add("up")

        if has_well and ball.dy > 0:
            # Use well when ball is far from paddle and high up
            dist = abs(ball.rect.centerx - engine.paddle.rect.centerx)
            if dist > 70 and ball.rect.centery < engine.height * 0.45:
                keys.add("down")

    # ── Skill selection ────────────────────────────────────────────

    def events(self, engine, dt: float) -> list:
        """Pick best skill on draft screens."""
        evts = super().events(engine, dt)

        if engine.state == "SKILL_SELECTION" and engine.skill_cards:
            card = self._pick_skill(engine) or engine.skill_cards[0]
            evts.append(pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"pos": (card.rect.centerx, card.rect.centery), "button": 1},
            ))

        return evts

    def _pick_skill(self, engine):
        """Evaluate available skills based on run state + synergy."""
        cards = engine.skill_cards
        if not cards:
            return None
        best, best_score = cards[0], -1
        for card in cards:
            s = self._skill_score(card.skill.type, engine)
            if s > best_score:
                best_score = s
                best = card
        return best

    def _skill_score(self, sk, engine) -> float:
        score = 5.0
        lv = engine.level
        lives = engine.paddle.lives
        have = set(s.type for s in engine.selected_skills)
        already = sum(1 for s in engine.selected_skills if s.type == sk)

        # ── Sustain (always valuable) ──
        if sk == SkillType.VAMPIRE:
            score += 5.5
            # Synergy: stronger with CHARGE bricks (at higher levels)
            if lv >= 6:
                score += 1.5
        elif sk == SkillType.HEAL:
            score += 6.5 if lives <= 2 else 1.5
        elif sk == SkillType.SHIELD:
            score += 4.5
            # Synergy: shield + wide paddle = great defense
            if SkillType.PADDLE_WIDE in have or SkillType.ECHO_PADDLES in have:
                score += 1.0

        # ── Offense ──
        if sk == SkillType.DAMAGE:
            score += 2.5 + lv * 0.15
            # Synergy: damage + crit/ghost/explosive
            if SkillType.CRITICAL_HIT in have or SkillType.EXPLOSIVE in have:
                score += 1.5
        elif sk == SkillType.EXPLOSIVE:
            score += 3.5 + lv * 0.1
            # Synergy: explosive + chain spark
            if SkillType.CHAIN_SPARK in have:
                score += 1.5
        elif sk == SkillType.CRITICAL_HIT:
            score += 3.0 + lv * 0.12
        elif sk == SkillType.GHOST_BALL:
            score += 3.0 + lv * 0.12
        elif sk == SkillType.CHAIN_SPARK:
            score += 3.0
            if SkillType.EXPLOSIVE in have:
                score += 1.5

        # ── Ball control (critical for survival) ──
        if sk == SkillType.MAGNET:
            score += 4.0
        elif sk == SkillType.GRAVITY_WELL:
            score += 3.5
        elif sk == SkillType.STASIS_FIELD:
            score += 3.5
        elif sk == SkillType.TIME_WARP:
            score += 3.5

        # ── Speed control ──
        if sk == SkillType.SPEED_UP:
            score += 2.0 + lv * 0.3  # more valuable at high levels
        elif sk == SkillType.CONTROL:
            score += 2.5 + lv * 0.05

        # ── Projectiles ──
        proj_scores = {
            SkillType.SCATTER_SHOT: 4.0, SkillType.CANNON: 3.5,
            SkillType.SEEKER: 3.5, SkillType.LASER: 3.0,
            SkillType.VOLLEY: 3.0, SkillType.RICOCHET: 2.5,
        }
        if sk in proj_scores:
            score += proj_scores[sk]
            # Synergy: pierce makes all projectiles better
            if SkillType.PIERCING_SHOTS in have:
                score += 2.0

        # ── Pierce synergy ──
        if sk == SkillType.PIERCING_SHOTS:
            score += 2.5
            has_proj = any(p in have for p in (
                SkillType.CANNON, SkillType.LASER, SkillType.VOLLEY,
                SkillType.SCATTER_SHOT, SkillType.SEEKER, SkillType.RICOCHET))
            if has_proj:
                score += 2.5

        # ── Multi-ball ──
        if sk == SkillType.MULTI_BALL:
            score += 2.5 + min(3, lv * 0.1)
            if SkillType.MAGNET in have:
                score += 1.0
        elif sk == SkillType.SPLIT_CHARGE:
            score += 3.0

        # ── Paddle helpers / auto-fire ──
        if sk in (SkillType.ECHO_PADDLES, SkillType.PATROL_PADDLES):
            score += 3.0
        elif sk == SkillType.DRONES:
            score += 3.0  # auto-projectiles; synergizes with pierce
        elif sk == SkillType.PADDLE_WIDE:
            score += 2.5

        # ── Giant ball ──
        if sk == SkillType.GIANT_BALL:
            score += 2.5

        # ── Diminishing returns ──
        if already >= 3:
            score -= 6.0
        elif already >= 2:
            score -= 3.0
        elif already >= 1:
            score -= 1.5

        # ── First-time bonus ──
        if already == 0 and sk not in (SkillType.CHOICE, SkillType.FOCUS):
            score += 2.5

        # ── Situational ──
        if sk == SkillType.CHOICE:
            score = 4.5 if lv <= 3 else 0.5
        if sk == SkillType.FOCUS:
            # Only take FOCUS if we have width to spare
            if engine.paddle.width_bonus >= 20:
                score += 2.0
            else:
                score -= 10.0  # hard avoid

        return score
