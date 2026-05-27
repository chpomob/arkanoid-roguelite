## Fichiers modifies
- [tests/test_ball_collisions.py](/media/chpo/HDD-papa/localllmtest/CSE-claude/tests/test_ball_collisions.py:154) — ajout d’un test de régression garantissant que `Ball.update()` utilise `query_rect()` et ne parcourt pas `.bricks`.

`src/game/entities/ball.py` et `src/game/engine.py` étaient déjà conformes à la spec: `Ball.update()` utilise `brick_layer.query_rect(self.rect)`, et `update_balls()` passe `[self.brick_grid]`.

## Code
```python
# src/game/entities/ball.py
collisions = []
for brick_layer in brick_layers:
    collisions.extend(brick_layer.query_rect(self.rect))

# src/game/engine.py
hit_brick = ball.update(
    self.width,
    self.height,
    [self.brick_grid],
    apply_damage=False,
    playfield_top=self.playfield_top,
)
```

## Tests
```python
def test_ball_update_uses_spatial_query_layer(self):
    """Test that Ball.update queries candidate bricks through the spatial index."""
    width, height = 1024, 768
    paddle = paddle_module.Paddle(width, height)
    ball = ball_module.Ball(width, height, paddle)
    brick = brick_module.Brick(pygame.Rect(500, 500, 20, 20), hp=2)

    class SpatialOnlyLayer:
        def __init__(self, bricks):
            self._bricks = bricks
            self.query_count = 0

        @property
        def bricks(self):
            raise AssertionError("Ball.update must use query_rect() instead of iterating bricks")

        def query_rect(self, rect, active_only=True):
            self.query_count += 1
            return [
                candidate
                for candidate in self._bricks
                if (candidate.active or not active_only) and rect.colliderect(candidate.rect)
            ]

    ball.rect.center = brick.rect.center
    ball.x = ball.rect.centerx
    ball.y = ball.rect.centery
    ball.dx = 0
    ball.dy = 0
    layer = SpatialOnlyLayer([brick])

    hit = ball.update(width, height, [layer])

    self.assertIs(hit, brick)
    self.assertEqual(layer.query_count, 1)
    self.assertEqual(brick.hp, 1)
```

Validation: `python3 run_tests.py` passe, `193 tests OK`. `python run_tests.py` n’a pas pu être lancé car `python` n’existe pas dans ce shell.

## Hypotheses
- `Ball.update()` reçoit des couches compatibles `BrickGrid`, donc exposant `query_rect(rect, active_only=True)`.
- L’ordre de destruction reste celui de `query_rect()`, qui trie déjà selon l’ordre de grille.