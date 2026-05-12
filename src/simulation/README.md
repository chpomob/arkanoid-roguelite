# Bot Simulation Framework

Automated bot-driven game testing for Arkanoid Roguelite.

## Quick Start

```bash
# Full game benchmark (all bots, 20 seeds)
python3 run_full_game_benchmark.py --seeds 20

# Quick test (2 bots, 5 seeds)
python3 run_full_game_benchmark.py --bots tracker,agpro --seeds 5

# Level benchmark (boss levels only)
python3 run_level_benchmark.py --levels boss

# Skill correlation analysis (30 seeds)
python3 run_probot_longrun.py
```

## Architecture

```
src/simulation/
├── __init__.py          # Public API exports
├── bot.py               # BaseBot ABC, SimpleBot, enemy dodging
├── runners/
│   ├── tracker.py       # TrackerBot (perfect tracking baseline)
│   ├── sniper.py        # SniperBot (aims at clusters)
│   ├── survivor.py      # SurvivorBot (slow reactions, high deaths)
│   ├── noob.py          # NoobBot (random movements)
│   └── pro.py           # ProBot, VampirePro, AggroPro
├── runner.py            # GameRunner — headless engine wrapper
├── metrics.py           # RunResult, aggregate()
├── skill_bot.py         # SkillTestBot factory for skill targeting
├── skill_benchmark.py   # Benchmark helpers per skill
└── skill_rating.py      # SkillRating, rank_skills()

benchmarks/
├── full_game.py         # Full runs from level 1
├── level.py             # Single-level tests
├── comparison.py        # Bot vs bot skill comparison
└── longrun.py           # ProBot deep-run analysis
```

## Bots

| Bot | Style | Level (20 seeds) | Use Case |
|-----|-------|-----------------|----------|
| NoobBot | Random, terrible | L4 | Absolute floor |
| SurvivorBot | Slow, takes damage | L8-9 | Bad player benchmark |
| TrackerBot | Perfect tracking | L10-11 | Average player baseline |
| SniperBot | Aims at clusters | L9 | Offensive playstyle |
| ProBot | Optimal choices | L13-16 | Skilled player |
| VampirePro | VAMPIRE-first | L15-18 | Sustain strategy |
| AggroPro | Offense-first | L24-39 | Best strategy |

## Adding a New Bot

1. Create `src/simulation/runners/mybot.py`
2. Extend `SimpleBot` or `ProBot`
3. Override `held_keys()` and `events()`
4. Add to `BOTS` dict in benchmark scripts

## Key Metrics

- **level_reached**: highest level before death/max_frames
- **boss_kills**: list of boss names defeated
- **deaths**: total lives lost
- **skills**: skill types picked during run
- **score**: total score accumulated
