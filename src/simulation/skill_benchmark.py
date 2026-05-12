"""Skill benchmark: runs bot with each skill to measure performance impact."""

from game.roguelite.skill import SkillType
from simulation.runner import GameRunner, run_many
from simulation.skill_bot import SkillTestBot
from simulation.skill_rating import SkillRating, format_ranking, rating_from_results


# Skill names (from get_description in skill_descriptions.py, without level suffix)
SKILL_NAMES = {
    SkillType.DAMAGE: "Piercing Shot",
    SkillType.VAMPIRE: "Vampirism",
    SkillType.MULTI_BALL: "Twin Core",
    SkillType.LASER: "Laser Paddle",
    SkillType.SPEED_UP: "Tempo Stabilizer",
    SkillType.PADDLE_WIDE: "Wide Guard",
    SkillType.HEAL: "Repair",
    SkillType.CONTROL: "Guidance",
    SkillType.GIANT_BALL: "Heavy Core",
    SkillType.EXPLOSIVE: "Blast Core",
    SkillType.SHIELD: "Aegis",
    SkillType.MAGNET: "Magnet Field",
    SkillType.CHOICE: "Tactical Draft",
    SkillType.DRONES: "Drone Paddles",
    SkillType.SPLIT_CHARGE: "Split Charge",
    SkillType.VOLLEY: "Volley Shot",
    SkillType.FOCUS: "Focus Core",
    SkillType.CANNON: "Cannon Core",
    SkillType.GRAVITY_WELL: "Gravity Well",
    SkillType.RICOCHET: "Ricochet Bolts",
    SkillType.SEEKER: "Seeker Core",
    SkillType.ECHO_PADDLES: "Echo Paddles",
    SkillType.SCATTER_SHOT: "Scatter Array",
    SkillType.PIERCING_SHOTS: "Piercing Lines",
    SkillType.CHAIN_SPARK: "Chain Spark",
    SkillType.STASIS_FIELD: "Stasis Field",
    SkillType.PATROL_PADDLES: "Patrol Paddles",
}


def benchmark_skill(skill: SkillType, seeds: int = 10, max_frames: int = 80000) -> SkillRating:
    """Run bot with target skill across N seeds, return rating.
    
    Patches build_skill_cards to ensure the target skill is always in the draft.
    """
    from unittest import mock
    from game import engine as engine_module

    original_build = engine_module.GameEngine.build_skill_cards

    def patched_build(self, selected_types):
        # Replace first type with target if not already present
        if skill not in selected_types:
            selected_types = [skill] + list(selected_types[1:])
        return original_build(self, selected_types)

    results = []
    for seed in range(seeds):
        bot = SkillTestBot(target_skill=skill, seed=seed)
        with mock.patch.object(engine_module.GameEngine, 'build_skill_cards', patched_build):
            runner = GameRunner(bot, seed=seed, max_frames=max_frames)
            results.append(runner.run())

    name = SKILL_NAMES.get(skill, skill.value)
    return rating_from_results(skill, name, results, seeds)


def benchmark_baseline(seeds: int = 10, max_frames: int = 80000) -> SkillRating:
    """Baseline: bot picks the first available skill (no targeting)."""
    from simulation.bot import SimpleBot

    results = run_many(SimpleBot, seeds=list(range(seeds)), max_frames=max_frames)
    # Baseline doesn't have a specific skill type — use DAMAGE as placeholder
    return SkillRating(
        skill_type=SkillType.DAMAGE,
        skill_name="(baseline first-pick)",
        seeds=seeds,
        success_count=len(results),
        avg_level=sum(r.level_reached for r in results) / len(results),
        avg_score=sum(r.score for r in results) / len(results),
        avg_frames=sum(r.frames for r in results) / len(results),
        avg_bricks=sum(r.bricks_broken for r in results) / len(results),
        completion_rate=sum(1 for r in results if r.reason == "gameover") / len(results),
    )


def benchmark_all(skills: list[SkillType] | None = None, seeds: int = 10, max_frames: int = 80000) -> tuple[list[SkillRating], SkillRating]:
    """Benchmark all (or specified) skills and return (ratings, baseline)."""
    if skills is None:
        skills = list(SkillType)

    print(f"Benchmarking {len(skills)} skills with {seeds} seeds each...")
    baseline = benchmark_baseline(seeds=seeds, max_frames=max_frames)
    print(f"Baseline: Lvl={baseline.avg_level:.1f} Score={baseline.avg_score:.0f}")

    ratings = []
    for i, skill in enumerate(skills):
        name = SKILL_NAMES.get(skill, skill.value)
        rating = benchmark_skill(skill, seeds=seeds, max_frames=max_frames)
        ratings.append(rating)
        print(f"  [{i+1}/{len(skills)}] {name}: Lvl={rating.avg_level:.1f} Score={rating.avg_score:.0f} Tier={rating.tier}")

    return ratings, baseline


if __name__ == "__main__":
    # Run from project root: python3 -m simulation.skill_benchmark
    ratings, baseline = benchmark_all(seeds=5, max_frames=50000)
    print("\n" + format_ranking(ratings, baseline))
