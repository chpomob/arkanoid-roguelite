#!/usr/bin/env python3
"""Comprehensive gap-balance benchmark: 4 bots × many seeds × full simulation.

Tests the impact of the strategic gap (+45) above the brick area.
"""

import json
import multiprocessing
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC_PATH = os.path.join(_PROJECT_ROOT, 'src')

BOTS = {
    "simple": ("SimpleBot", 50, 150000),
    "pro": ("ProBot", 20, 150000),
    "sniper": ("SniperBot", 20, 150000),
    "survivor": ("SurvivorBot", 20, 150000),
}


def _run_one(args: tuple) -> dict:
    bot_key, seed, max_frames, src_path = args
    import sys as _sys
    _sys.path.insert(0, src_path)
    import random as _random
    from simulation.runner import GameRunner
    from simulation.bot import SimpleBot
    from simulation.pro_bot import ProBot
    from simulation.alt_bots import SniperBot, SurvivorBot

    bot_map = {
        "simple": SimpleBot, "pro": ProBot,
        "sniper": SniperBot, "survivor": SurvivorBot,
    }
    BotCls = bot_map[bot_key]

    _random.seed(seed)
    bot = BotCls(seed=seed)
    runner = GameRunner(bot, seed=seed, max_frames=max_frames)
    r = runner.run()

    return {
        "bot": bot_key, "seed": seed,
        "level": r.level_reached, "score": r.score,
        "bricks": r.bricks_broken, "deaths": r.deaths,
        "boss_kills": len(r.boss_kills),
        "boss_names": r.boss_kills,
        "skills": r.skills,
        "frames": r.frames, "reason": r.reason,
    }


def aggregate_results(results: list[dict]) -> dict:
    if not results:
        return {}
    levels = [r["level"] for r in results]
    scores = [r["score"] for r in results]
    bricks = [r["bricks"] for r in results]
    deaths = [r["deaths"] for r in results]
    n = len(results)
    return {
        "runs": n,
        "avg_level": sum(levels) / n,
        "min_level": min(levels), "max_level": max(levels),
        "avg_score": sum(scores) / n,
        "min_score": min(scores), "max_score": max(scores),
        "avg_bricks": sum(bricks) / n,
        "avg_deaths": sum(deaths) / n,
        "total_boss_kills": sum(r["boss_kills"] for r in results),
        "gameovers": sum(1 for r in results if r["reason"] == "gameover"),
        "max_frames_hit": sum(1 for r in results if r["reason"] == "max_frames"),
        "avg_frames": sum(r["frames"] for r in results) / n,
    }


def main():
    multiprocessing.freeze_support()
    workers = min(12, os.cpu_count() or 8)

    # Build task list
    tasks = []
    for bot_key, (name, seeds, max_frames) in BOTS.items():
        for seed in range(seeds):
            tasks.append((bot_key, seed, max_frames, _SRC_PATH))

    total = len(tasks)
    print(f"Gap Balance Benchmark")
    print(f"{'='*60}")
    print(f"Bots: { {k: f'{v[0]} ×{v[1]} seeds' for k,v in BOTS.items()} }")
    print(f"Total runs: {total}  Workers: {workers}")
    print(f"Max frames: 150,000 (~41 min game time per run)")
    print()

    all_results = []
    t0 = time.time()
    completed = 0

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_run_one, t): t for t in tasks}
        for future in as_completed(futures):
            task = futures[future]
            try:
                result = future.result()
                all_results.append(result)
            except Exception as e:
                print(f"  FAILED {task}: {e}")
            completed += 1
            elapsed = time.time() - t0
            rate = completed / elapsed if elapsed > 0 else 0
            remaining = (total - completed) / rate if rate > 0 else 0
            print(f"\r  [{completed:>3}/{total}] {result.get('bot','?'):>8} s{result.get('seed','?'):>2} "
                  f"Lv{result.get('level','?'):>3} Score{result.get('score',0):>8} "
                  f"Bricks{result.get('bricks',0):>5} {result.get('reason','?'):>10}  "
                  f"{elapsed:.0f}s ~{remaining:.0f}s", end="", flush=True)

    elapsed = time.time() - t0
    print(f"\n\nDone in {elapsed:.0f}s ({elapsed/60:.1f} min)\n")

    # Per-bot summary
    print(f"{'='*60}")
    print(f"{'Bot':<12} {'Runs':>4} {'AvgLv':>6} {'Range':>10} {'AvgScore':>10} {'AvgBrick':>8} {'AvgDth':>6} {'Bosses':>7} {'%Done':>6} {'AvgFrames':>9}")
    print(f"{'-'*80}")

    for bot_key, (name, _, _) in BOTS.items():
        bot_results = [r for r in all_results if r["bot"] == bot_key]
        if not bot_results:
            continue
        agg = aggregate_results(bot_results)
        print(f"{name:<12} {agg['runs']:>4} {agg['avg_level']:>6.1f} "
              f"{agg['min_level']:>3}-{agg['max_level']:<4} "
              f"{agg['avg_score']:>10.0f} {agg['avg_bricks']:>8.0f} "
              f"{agg['avg_deaths']:>5.1f} {agg['total_boss_kills']:>7} "
              f"{agg['gameovers']/agg['runs']*100:>5.0f}% {agg['avg_frames']:>9.0f}")

    # Level distribution per bot
    print(f"\n{'='*60}")
    print("Level distribution per bot:")
    for bot_key, (name, _, _) in BOTS.items():
        bot_results = [r for r in all_results if r["bot"] == bot_key]
        dist = {}
        for r in bot_results:
            dist[r["level"]] = dist.get(r["level"], 0) + 1
        print(f"\n  {name}:")
        for lv in sorted(dist):
            bar = "#" * dist[lv]
            print(f"    Lv{lv:>3}: {bar} ({dist[lv]})")

    # Boss kill summary
    print(f"\n{'='*60}")
    print("Boss kill counts:")
    boss_counts = {}
    for r in all_results:
        for b in r.get("boss_names", []):
            boss_counts[b] = boss_counts.get(b, 0) + 1
    for b, c in sorted(boss_counts.items(), key=lambda x: -x[1]):
        print(f"  {b}: {c}")

    # Reason distribution
    print(f"\n{'='*60}")
    print("Completion reasons per bot:")
    for bot_key, (name, _, _) in BOTS.items():
        bot_results = [r for r in all_results if r["bot"] == bot_key]
        reasons = {}
        for r in bot_results:
            reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
        print(f"  {name}: {reasons}")

    # Save results
    out_path = os.path.join(_PROJECT_ROOT, "gap_benchmark.json")
    with open(out_path, "w") as f:
        json.dump({"runs": all_results, "config": {
            "bots": {k: v[0] for k, v in BOTS.items()},
            "gap_size": 45,
            "elapsed_s": elapsed,
        }}, f, indent=2)
    print(f"\nResults → {out_path}")


if __name__ == "__main__":
    main()
