# Repository Guidelines

## Project Structure & Module Organization
This repository contains a Python Arkanoid roguelite engine. Runtime code lives in `src/`, with `src/main.py` as the entry point and `src/game/engine.py` coordinating the main loop, scoring, persistence, and state transitions. Core gameplay objects are in `src/game/entities/`, roguelite mechanics are in `src/game/roguelite/`, rendering helpers are in `src/game/ui.py`, and particle effects are in `src/game/particles/`. Tests live in `tests/` and mirror gameplay areas such as ball physics, bricks, skills, progression, scoring, and engine state. See `ARCHITECTURE.md` for deeper flow notes.

## Build, Test, and Development Commands
- `python -m venv venv && source venv/bin/activate`: create and activate a local virtual environment on Linux/macOS.
- `pip install -r requirements.txt`: install runtime dependencies, currently Pygame.
- `python src/main.py`: run the game locally at the default 1024x768 resolution.
- `python run_tests.py`: run the standard test suite using `unittest` discovery.
- Runtime save files are `arkanoid_save.json` and `arkanoid_high_scores.json`; they are ignored by git.

## Coding Style & Naming Conventions
Use Python 3.10+ syntax and keep modules focused by gameplay area. Follow `PascalCase` for classes and `snake_case` for functions, variables, and test methods. Prefer explicit type hints for public functions and methods, especially when passing engine, entity, or skill objects. Add docstrings for public methods and short comments only where physics, collision, or skill interactions are not obvious. Keep imports clean and avoid committing commented-out code.

## Testing Guidelines
Tests are written as `unittest.TestCase` classes in files named `tests/test_*.py`. Add or update tests with every behavior change, especially for collision handling, state transitions, and roguelite effects. Run `python run_tests.py` before handing work back. When testing skills, isolate engine state or mock only what is needed to avoid state leakage. For collision tests, keep `pygame.Rect` positions aligned with entity coordinates to reduce floating-point drift.

## Commit & Pull Request Guidelines
Existing history is minimal, but `CONTRIBUTING.md` asks for Conventional Commits such as `feat: add laser bullet mechanics`, `fix: resolve ball clipping on fast speeds`, and `refactor: extract skill logic to effects module`. Keep commits scoped to one logical change. Pull requests should include a short summary, the tests run, linked issues when applicable, and screenshots or short recordings for visible gameplay/UI changes.

## Agent-Specific Instructions
Do not rewrite unrelated game systems while making a focused fix. Preserve existing module boundaries, update tests alongside behavior changes, and prefer small patches that are easy to review.
