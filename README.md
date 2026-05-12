# 🧱 Arkanoid Roguelite

A modular Breakout clone with roguelite progression, upgrade cards, boss fights, and seeded procedural levels. Built in Python with Pygame.

<p align="center">
  <em>Break bricks. Choose upgrades. Survive the run.</em>
</p>

## 🎮 Features

- **30 upgrade skills** — Damage, Vampirism, Multi-ball, Cannons, Gravity Wells, Drones, and more. Skills combine with synergy bonuses.
- **6 boss fights** across 3 tiers — face the Gate Sentinel, Forge Warden, Sentry Archon, and others every 5 levels.
- **7 special brick types** — TOUGH, BOMB, PULSE, CHARGE, REGEN, PRISM, and SENTRY bricks with unique mechanics.
- **Seeded procedural levels** — themed layouts and backgrounds that vary each run.
- **Strategic gap** — space above the bricks for skillful angle play.
- **Procedural audio** — dynamic retro synth sounds for every action.
- **Save & resume** — runs, high scores, and settings persist locally.
- **Rebindable controls** — fully customizable key bindings.

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/chpomob/arkanoid-roguelite.git
cd arkanoid-roguelite

# Setup
python3 -m venv venv
source venv/bin/activate
pip install pygame

# Play
python3 src/main.py
```

## 🎯 Controls

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
| K | Controls |
| M | Settings |

## 🧪 Tests

```bash
python3 run_tests.py              # 185 unit tests (~30s)
python3 run_simulation_tests.py   # 11 bot simulation tests (~4min)
```

## 🏗️ Architecture

```
src/
├── main.py                  # Entry point
├── game/
│   ├── engine.py            # Game loop & state machine
│   ├── entities/            # Ball, Paddle, Brick, Enemy
│   ├── roguelite/           # Skills, Effects, Bullets
│   ├── particles/           # Visual effects
│   ├── screens.py           # UI screens (title, HUD, pause, etc.)
│   ├── ui.py                # Retro UI primitives
│   ├── assets.py            # Sprite rendering
│   ├── audio.py             # Procedural synth audio
│   ├── bosses.py            # Boss definitions
│   └── input.py             # Key bindings
└── simulation/              # Headless bot-driven testing
    ├── bot.py               # SimpleBot (ball tracking)
    ├── pro_bot.py           # ProBot (trajectory prediction)
    ├── elite_bot.py         # EliteBot (targeting + skill eval)
    └── runner.py            # Headless game runner
```

## 📊 Balance

The game is tuned so that skilled players can reach ~level 100 with good skill synergies, while casual play caps around level 15. Validated with 110+ headless bot simulation runs across 5 bot difficulty levels.

## 📄 License

MIT — see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
