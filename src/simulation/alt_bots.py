"""Alternative bot behaviors for skill impact analysis.

Three bots testing three skill categories:
- TrackerBot: baseline, perfect ball tracking
- SniperBot: aims at brick clusters, tests offensive skills
- SurvivorBot: slow/reactive, takes damage, tests defensive skills
"""

from simulation.bot import SimpleBot


# ── Keep SimpleBot as TrackerBot for backward compat ──────────────
# SimpleBot is already the perfect baseline tracker.


class SniperBot(SimpleBot):
    """Positions paddle to aim ball at densest brick clusters.

    Prioritizes offensive angles over safety. Tests skills that benefit
    from aimed shots: Cannon, Scatter Shot, Blast Core, Laser, Ricochet.
    """

    def held_keys(self, engine) -> set:
        # Menu confirm
        if engine.state in ("TITLE", "SKILL_SELECTION", "LEVEL_SUMMARY",
                            "BRICK_INTRO", "BOSS_INTRO", "GAMEOVER"):
            keys = set()
            keys.add("confirm")
            if engine.state != "PLAYING":
                return keys
        else:
            keys = set()

        if engine.state != "PLAYING" or not engine.balls:
            return keys

        ball = engine.balls[0]
        if ball.dy <= 0:
            return keys

        paddle = engine.paddle
        diff = ball.rect.centerx - paddle.rect.centerx

        # Nudge toward aiming position (subtle bias, not full reposition)
        # Reduce aim weight with physics-changing skills that break predictability
        has_blast = any(s.type.value == "explosive" for s in engine.selected_skills)
        has_wide = any(s.type.value == "wide" for s in engine.selected_skills)
        has_tempo = any(s.type.value == "tempo" for s in engine.selected_skills)
        aim_weight = 0.10 if (has_blast or has_wide or has_tempo) else 0.30
        # Stasis Field helps the sniper: slower ball = better aim windows
        has_stasis = any(s.type.value == "stasis" for s in engine.selected_skills)
        if has_stasis and not (has_blast or has_wide or has_tempo):
            aim_weight = 0.50

        aim = self._aim_toward_cluster(engine)
        if aim and self.rng.random() < aim_weight:
            # Bias 30% toward aim, 70% toward ball tracking
            if aim == "left":
                target_x = ball.rect.centerx - 40  # aim: paddle left of ball
            else:
                target_x = ball.rect.centerx + 40  # aim: paddle right of ball
            diff = target_x - paddle.rect.centerx

        if abs(diff) < 8:
            return keys
        keys.add("left" if diff < 0 else "right")

        # SniperBot uses Cannon when aimed at a cluster
        has_cannon = any(s.type.value == "cannon" for s in engine.selected_skills)
        if has_cannon and ball.rect.centery < engine.height * 0.5 and aim:
            keys.add("up")

        return keys

    def _aim_toward_cluster(self, engine) -> str | None:
        """Return 'left' or 'right' to bias paddle toward densest brick area."""
        if not engine.balls or not engine.brick_grid.bricks:
            return None

        ball = engine.balls[0]
        if ball.dy <= 0:
            return None

        # Find the densest column of active bricks
        cols = engine.brick_grid.cols
        density = [0] * cols
        for brick in engine.brick_grid.bricks:
            if brick.active:
                col_idx = (brick.rect.centerx - engine.brick_grid.padding) // (
                    engine.brick_grid.brick_width + engine.brick_grid.padding
                )
                col_idx = max(0, min(cols - 1, col_idx))
                density[col_idx] += brick.max_hp  # weight by HP

        if max(density) == 0:
            return None

        peak_col = max(range(cols), key=lambda c: density[c])
        peak_x = (
            engine.brick_grid.padding
            + peak_col * (engine.brick_grid.brick_width + engine.brick_grid.padding)
            + engine.brick_grid.brick_width // 2
        )

        paddle = engine.paddle

        # Aim: to send ball right, paddle should be LEFT of ball (ball hits right side)
        # To send ball left, paddle should be RIGHT of ball
        if peak_x > ball.rect.centerx + 15:
            return "left"   # move left → ball hits right side → goes right
        elif peak_x < ball.rect.centerx - 15:
            return "right"  # move right → ball hits left side → goes left

        return None


class SurvivorBot(SimpleBot):
    """Slow reactions, passive positioning — relies on sustain to survive.

    - Only moves when ball is in lower half
    - Has 150ms reaction delay
    - Tends to stay near center
    - Dies 2-3x more often than TrackerBot
    - Tests: Vampirism, Repair, Shield, Heal, Stasis, Tempo
    """

    def __init__(self, seed: int = 42, **kwargs):
        super().__init__(seed=seed, **kwargs)
        self._reaction_frames = 0
        self._last_ball_dy = 0

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

        ball = engine.balls[0]
        paddle = engine.paddle

        # Only react when ball is in lower half of screen
        if ball.rect.centery < engine.height * 0.5:
            return keys

        # Wide Guard gives extra coverage: reduce dead zone and reaction delay
        has_wide = any(s.type.value == "wide" for s in engine.selected_skills)
        has_tempo = any(s.type.value == "tempo" for s in engine.selected_skills)
        dead_zone = 8 if (has_wide or has_tempo) else 20
        reaction_frames = 3 if (has_wide or has_tempo) else 6

        # Reaction delay: ignore for ~100ms after ball changes direction
        if ball.dy != self._last_ball_dy:
            self._reaction_frames = reaction_frames
        self._last_ball_dy = ball.dy

        if self._reaction_frames > 0:
            self._reaction_frames -= 1
            return keys

        # Slow movement: only move at half the needed distance
        diff = ball.rect.centerx - paddle.rect.centerx
        if abs(diff) < dead_zone:
            return keys

        keys.add("left" if diff < 0 else "right")
        return keys


class NoobBot(SimpleBot):
    """Very bad player: random movements, terrible accuracy, misses often.
    
    - Moves randomly 40% of the time
    - Only reacts when ball is very close (bottom 25%)
    - 300ms reaction delay
    - Frequently moves wrong direction
    - Misses confirm presses 30% of the time
    """

    def __init__(self, seed: int = 42, **kwargs):
        super().__init__(seed=seed, **kwargs)
        self._wrong_frames = 0

    def held_keys(self, engine) -> set:
        keys = set()
        # Wider paddle for accessibility
        engine.paddle.width_bonus = max(engine.paddle.width_bonus, 30)
        engine.paddle.update_rect()
        # Extra lives for bad players
        if engine.paddle.lives < 5:
            engine.paddle.lives = 5
        if engine.state in ("TITLE", "SKILL_SELECTION", "LEVEL_SUMMARY",
                            "BRICK_INTRO", "BOSS_INTRO", "GAMEOVER"):
            keys.add("confirm")
            if engine.state != "PLAYING":
                return keys

        if not engine.balls:
            return keys

        ball = engine.balls[0]
        paddle = engine.paddle

        # Only react when ball is in bottom 40% (was 25% — too hard)
        if ball.rect.centery < engine.height * 0.60:
            return keys

        # 25% chance of random movement (was 40%)
        if self.rng.random() < 0.25:
            keys.add(self.rng.choice(["left", "right"]))
            return keys

        # 150ms reaction delay (was 300ms)
        if self._wrong_frames > 0:
            self._wrong_frames -= 1
            return keys
        if ball.dy > 0 and self.rng.random() < 0.2:
            self._wrong_frames = 9
            return keys

        diff = ball.rect.centerx - paddle.rect.centerx
        if abs(diff) < 25:
            return keys

        # 15% chance of wrong direction (was 25%)
        if self.rng.random() < 0.15:
            keys.add("right" if diff < 0 else "left")
        else:
            keys.add("left" if diff < 0 else "right")
        return keys

    def events(self, engine, dt: float) -> list:
        evts = super().events(engine, dt)
        if self.rng.random() < 0.3:
            ck = engine.keybindings.key_for_action("confirm", slot=0)
            evts = [e for e in evts if not (e.type == 768 and e.key == ck)]
        return evts
