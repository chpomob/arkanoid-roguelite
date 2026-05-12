# Architecture Documentation

## 1. High-Level Flow
The game uses a **State Machine** pattern within `GameEngine`.
1. **Input Phase**: Captures keyboard/mouse events.
2. **Update Phase**: Calculates logic in `GameEngine.update()`.
3. **Render Phase**: Draws using `pygame` in `GameEngine.draw()`.

## 2. Key Modules

### `engine.py` (The Brain)
- Manages `GameEngine` states: `TITLE`, `PLAYING`, `SKILL_SELECTION`, `PAUSED`, `SCORES`, and `GAMEOVER`.
- Calls `update()` and `draw()` 60 times per second.
- Coordinates paddle/ball updates, projectile hits, special brick effects, scoring, persistence, and the `next_level()` loop.

### `entities/` (The Visuals)
- **`ball.py`**: Handles velocity `(dx, dy)`, wall bouncing, paddle-angle blending, and brick collision response.
- **`paddle.py`**: Handles movement, width scaling, and optional helper paddle hitboxes.
- **`brick.py`**: Handles brick HP, layouts, visual markers, and special brick kinds.

### `roguelite/` (The Progression)
- **`skill.py`**: Defines `SkillType` (ENUM) and `Skill` class.
- **`effects.py`**: 
  - `handle_skills()`: Applies selected skills to engine entities.
  - `apply_vampire()`: Manages `energy` for life regeneration.
  - `damage_brick()`: Centralizes brick damage for balls, projectiles, bombs, and blast effects.
- **`bullet.py`**: Handles laser and volley projectile movement.

## 3. Skill Application Logic
1. **Selection**: Player picks a card in `SKILL_SELECTION`.
2. **Accumulation**: `engine.py` stores the selected level in `global_skill_levels`.
3. **Application**: Paddle, ball, projectile, and charge effects are applied from the selected skill list.
4. **Synergy**: Skills can combine, such as `Wide` offsetting `Focus`, or `Volley` pairing with paddle-hit builds.

## 4. Scoring & Persistence
- **Scoring**: Bricks award small hit points and larger destruction points. Special bricks are worth more, and level-clear bonuses dominate the score curve.
- **Ranking**: High scores sort by `max_level_reached` first and raw score second, keeping run depth more important than score farming.
- **Save data**: `save_run()` stores level, score, lives, selected skills, global skill levels, charges, energy, brick HP/active state, and skill cards.
- **Resume**: `load_run()` restores progression and brick state, then starts with a fresh ball to avoid brittle physics snapshots.
- **Files**: Default local files are `arkanoid_save.json` and `arkanoid_high_scores.json`.

## 5. Code Quality & Testing
- **Test runner**: `python run_tests.py` runs the `unittest` suite in `tests/`.
- **Physics**: Collision tests align `pygame.Rect` centers with entity coordinates to avoid drift.
- **State isolation**: Tests patch `pygame.display.set_mode` when constructing engines.
- **Coverage focus**: Prioritize gameplay behavior over assignment-only or local simulation tests.
