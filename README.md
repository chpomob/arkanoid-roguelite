# 🧱 Arkanoid Roguelite

<p align="center">
  <em>Break bricks. Choose upgrades. Survive the run.</em>
</p>

<p align="center">
  <a href="https://github.com/chpomob/arkanoid-roguelite/releases"><img src="https://img.shields.io/github/v/release/chpomob/arkanoid-roguelite?label=release&color=success" alt="Release"></a>
  <a href="#quick-start"><img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python"></a>
  <a href="#tests"><img src="https://img.shields.io/badge/tests-196%20passing-brightgreen" alt="Tests"></a>
</p>

## Quick Start

|### Download (no Python needed)

**Windows** — download `arkanoid-roguelite.exe` from the [latest release](https://github.com/chpomob/arkanoid-roguelite/releases/latest) and double-click.

> First launch may take a few seconds (the exe unpacks itself). Windows SmartScreen may warn about an unsigned binary — click **"More info" → "Run anyway"**.

**Linux** — download, extract, run:

```bash
gunzip arkanoid-roguelite-linux.gz
chmod +x arkanoid-roguelite-linux
./arkanoid-roguelite-linux
```

### From source

```bash
git clone https://github.com/chpomob/arkanoid-roguelite.git
cd arkanoid-roguelite
pip install pygame
python3 src/main.py
```

## Features

- **30 upgrade skills** — Damage, Vampirism, Multi-ball, Cannons, Gravity Wells, Drones, and more. Synergy bonuses for combos.
- **6 boss fights** across 3 tiers — face the Gate Sentinel, Forge Warden, Sentry Archon, and others every 5 levels.
- **7 special brick types** — TOUGH, BOMB, PULSE, CHARGE, REGEN, PRISM, and SENTRY with unique mechanics.
- **Seeded procedural levels** — themed layouts and backgrounds that vary each run.
- **Strategic gap** — space above bricks for skillful angle play.
- **Procedural audio** — dynamic retro synth sounds.
- **Save & resume** — runs, high scores, and settings persist locally.
- **Rebindable controls** — fully customizable key bindings.

## Controls

| Key | Action |
|-----|--------|
| ← → / A D | Move paddle |
| ↑ / W | Cannon (active skill) |
| ↓ / S | Gravity Well (active skill) |
| Enter / Space | Confirm / Start |
| Esc | Pause / Back |
| F5 | Save run |
| C | Resume saved run |
| H | High scores |
| G | Skill guide |

## Tests

```bash
python3 run_tests.py              # 185 unit tests (~30s)
python3 run_simulation_tests.py   # 11 simulation tests (~4min)
```

## Architecture

```
src/
├── main.py                  # Entry point
├── game/
│   ├── engine.py            # Game loop & state machine
│   ├── entities/            # Ball, Paddle, Brick, Enemy
│   ├── roguelite/           # Skills, Effects, Bullets
│   ├── particles/           # Visual effects
│   ├── screens.py           # UI screens
│   ├── ui.py                # Retro UI primitives
│   ├── assets.py            # Sprite rendering
│   ├── audio.py             # Procedural synth audio
│   └── bosses.py            # Boss definitions
└── simulation/              # Headless bot testing
    ├── bot.py               # SimpleBot
    ├── pro_bot.py           # ProBot
    ├── elite_bot.py         # EliteBot
    └── runner.py            # Headless runner
```

## Balance

Skilled players can reach ~level 100 with good synergies. Casual play caps around level 15. Validated with 110+ headless bot simulation runs across 5 difficulty levels.

## License

MIT — see [CONTRIBUTING.md](CONTRIBUTING.md).
