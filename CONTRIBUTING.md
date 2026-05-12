# Contributing to Arkanoid Roguelite

## Coding Standards
1. **Naming**: `PascalCase` for classes, `snake_case` for variables/functions.
2. **Comments**: Use comments only for non-obvious physics, collision, or progression logic.
3. **Scope**: Keep gameplay behavior in `engine.py`, entity state in `entities/`, and reusable skill effects in `roguelite/effects.py`.
4. **Imports**: Remove unused imports and avoid compatibility wrappers once callers are migrated.

## Testing Workflow
- **Runner**: Use `python run_tests.py` to run the `unittest` suite.
- **Isolation**: Patch `pygame.display.set_mode` when constructing `GameEngine` in tests.
- **Physics**: When testing collisions, align `pygame.Rect` centers with entity coordinates to avoid floating-point drift.
- **Signal**: Prefer tests that exercise production helpers or engine methods over assignment-only checks.

## Git Workflow
1. **Branching**:
   - `main`: Stable, production-ready code.
   - `dev`: Active development (merge PRs here before main).
   - `feat/add-vampire`: Feature branches.
2. **Commit Messages**: Use Conventional Commits:
   - `feat: add laser bullet mechanics`
   - `fix: resolve ball clipping on fast speeds`
   - `refactor: extract skill logic to effects module`

## Development Checklist
Before requesting a merge:
- [ ] `python run_tests.py` passes.
- [ ] New functionality has its own test class.
- [ ] No unused imports or commented-out code.
- [ ] Visible gameplay/UI changes include a screenshot or render smoke check when practical.
