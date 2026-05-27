# Arkanoid Roguelite — Ball Collision Spatial Index

## Context
BrickGrid.query_rect() exists (spatial grid index) but is only used in handle_bullet_hits(). The biggest remaining bottleneck is ball.update() which iterates ALL bricks in O(n) for collision detection every frame.

## Task
Modify Ball.update() to use BrickGrid.query_rect() instead of iterating self.brick_grid.bricks for collision detection. Keep identical behavior.

## Files to modify
- src/game/entities/ball.py — update() method, around line 82
  - Currently: loops over brick_layers, iterates each brick_grid.bricks
  - Target: use brick_grid.query_rect(ball_rect) instead
- src/game/engine.py — update_balls() passes brick_grid to ball.update()

## Constraints
- Do NOT change ball physics or collision behavior
- Keep identical brick destruction order
- All 192 unit tests must pass
- query_rect already exists and is tested

## Code reference
```python
# ball.py update() signature:
def update(self, screen_width, screen_height, brick_layers, apply_damage=True, playfield_top=0):
    # brick_layers is a list of BrickGrid objects (usually [self.brick_grid])
    for layer in brick_layers:
        for brick in layer.bricks:  # <-- O(n) per ball per frame
            if brick.active and self.rect.colliderect(brick.rect):
                ...

# brick.py — already exists:
def query_rect(self, rect, active_only=True) -> list[Brick]:
    """Return bricks whose rects collide with rect, preserving grid order."""
```

## Deliverable
Modified ball.py (and engine.py if needed) using query_rect(). All tests pass.

Produce ALL code INLINE. Do NOT ask for file write permission.
