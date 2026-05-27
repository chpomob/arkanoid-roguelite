# Arkanoid Roguelite — Performance Optimization Spec

## Context
The game runs on pygbag/WASM in the browser. Recent optimizations (font caching, scale skip, particle in-place removal, brick dirty tracking) have been applied. Further profiling and optimization is needed.

## Task
Analyze the codebase for remaining WASM/web performance bottlenecks and apply optimizations. Focus on:

1. **Render pipeline** — The draw() method is called every frame. Look for:
   - Unnecessary surface allocations (pygame.Surface created each frame)
   - Redundant draw calls (HUD elements redrawn when not changed)
   - Background regeneration (draw_background called every frame, could be cached)
   - Any code that creates temporary surfaces inside draw loops

2. **Collision detection** — O(n²) checks between entities:
   - Ball vs bricks: check if spatial partitioning could help (grid-based lookup)
   - Enemy shots vs paddle: check efficiency
   - Bullets vs bricks: iterates all bricks per bullet

3. **Audio** — SoundManager.play() called frequently:
   - Could add a cooldown/throttle for rapid-fire sounds (cannon, projectile)
   - Check if set_volume is called unnecessarily

4. **Memory** — Check for:
   - Object allocations in hot paths (e.g., creating new Random() instances)
   - List comprehensions recreating lists
   - Unbounded growth (particles, events)

5. **WASM-specific** — Code that's especially slow in pygbag:
   - font.render() calls (mitigated by font cache but still per-frame)
   - Any remaining SysFont() calls not going through the cache
   - Surface alpha blending operations

## Constraints
- Do NOT change game behavior or visuals
- Do NOT sacrifice code quality
- Preserve all existing tests (187 unit tests must pass)
- Keep changes minimal and targeted
- The project uses Python 3.10+, pygame, pygbag for WASM
- Entry point: src/main.py (async def main)
- Main loop: src/game/engine.py (async def run, def update, def draw)
- UI: src/game/ui.py (draw_background, draw_text, draw_panel, etc.)
- No clock.tick() — uses time.time() for dt

## Deliverable
Produce optimized code with specific changes, each justified by a performance rationale. 
Include any new test coverage for the changed behavior.

Produce ALL code INLINE in markdown code blocks. Do NOT attempt file writes or ask for permission.
