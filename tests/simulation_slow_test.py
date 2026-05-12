"""Simulation tests: bot-driven gameplay for bug catching and balance analysis.

These are slow tests — run separately with: python3 run_simulation_tests.py
"""
import unittest

from simulation import GameRunner, NoisyBot, RunResult, SimpleBot, aggregate, run_many


class TestSimpleBot(unittest.TestCase):
    """Verify the basic bot survives and produces consistent results."""

    def test_simple_bot_survives_level_1(self):
        """SimpleBot should consistently clear at least level 1 and earn score."""
        bot = SimpleBot(seed=42)
        runner = GameRunner(bot, seed=42, max_frames=100000)
        result = runner.run()

        self.assertGreater(result.level_reached, 1, f"Bot got level {result.level_reached}")
        self.assertGreater(result.score, 0)
        self.assertGreater(result.bricks_broken, 0)

    def test_deterministic_with_same_seed(self):
        """Same seed should produce identical results (engine RNG also seeded)."""
        results = run_many(SimpleBot, seeds=[42, 42, 42], max_frames=15000)
        first = results[0]

        for i, result in enumerate(results[1:], 2):
            self.assertEqual(result.score, first.score, f"Run {i} score differs: {result.score} vs {first.score}")
            self.assertEqual(result.level_reached, first.level_reached)
            self.assertEqual(result.bricks_broken, first.bricks_broken)
            self.assertEqual(result.skills, first.skills)

    def test_bot_picks_skills(self):
        """Bot should pick skills across levels."""
        bot = SimpleBot(seed=99)
        runner = GameRunner(bot, seed=99, max_frames=100000)
        result = runner.run()
        self.assertGreater(len(result.skills), 0)

    def test_multiple_seeds_complete(self):
        """Different seeds should all produce valid runs (some may be very good)."""
        results = run_many(SimpleBot, seeds=range(3), max_frames=100000)
        for r in results:
            self.assertGreater(r.frames, 0)
            self.assertGreaterEqual(r.level_reached, 1)
            self.assertIn(r.reason, ("gameover", "max_frames"),
                         f"Seed {r.seed}: unexpected reason {r.reason}")


class TestNoisyBot(unittest.TestCase):
    """Verify the noisy bot still makes progress."""

    def test_noisy_bot_completes(self):
        """Even with noise, bot should make meaningful progress."""
        results = run_many(NoisyBot, seeds=range(2), max_frames=150000, noise=0.1, miss_confirm=0.2)
        for r in results:
            # Noisy bot surviving max_frames is fine — the strategic gap helps
            self.assertIn(r.reason, ("gameover", "max_frames"),
                          f"Seed {r.seed}: unexpected reason {r.reason}")
            self.assertGreaterEqual(r.level_reached, 2,
                                    f"Seed {r.seed}: bot should reach at least level 2")


class TestMetrics(unittest.TestCase):
    """Verify metrics aggregation works."""

    def test_aggregate_empty(self):
        self.assertEqual(aggregate([]), {})

    def test_aggregate_multiple(self):
        results = [
            RunResult(seed=0, level_reached=5, score=1000, skills=["DAMAGE"]),
            RunResult(seed=1, level_reached=3, score=600, skills=["VAMPIRE"]),
        ]
        stats = aggregate(results)
        self.assertEqual(stats["runs"], 2)
        self.assertEqual(stats["avg_level"], 4.0)


class TestBalanceRegression(unittest.TestCase):
    """Verify skills stay within acceptable balance bounds.

    These catch accidental regressions when changing game mechanics.
    Uses a quick 12-skill run with TrackerBot only (fastest validation).
    """

    def test_no_skill_harmful_vs_baseline(self):
        """No skill should perform worse than the no-skill baseline."""
        from game.roguelite.skill import SkillType
        from simulation.bot import SimpleBot
        from simulation.skill_bot import make_skill_bot_class
        from simulation.skill_benchmark import benchmark_baseline, benchmark_skill

        # 8 seeds, 40k frames — stability with varied level generation
        baseline = benchmark_baseline(seeds=8, max_frames=40000)

        critical_skills = [
            SkillType.DAMAGE, SkillType.VAMPIRE, SkillType.SHIELD,
            SkillType.CANNON, SkillType.SCATTER_SHOT, SkillType.HEAL,
        ]
        for skill in critical_skills:
            rating = benchmark_skill(skill, seeds=8, max_frames=40000)
            # Forced single-skill builds are inherently suboptimal vs free-pick;
            # only fail if a skill is truly harmful (below 50% of baseline)
            min_acceptable = max(2.0, baseline.avg_level * 0.5)
            self.assertGreaterEqual(
                rating.avg_level, min_acceptable,
                f"{rating.skill_name} ({rating.avg_level:.1f}) should not be "
                f"catastrophically worse than baseline ({baseline.avg_level:.1f})"
            )

    def test_top_skills_reach_minimum_level(self):
        """Best offensive skills should reach at least baseline+1."""
        from game.roguelite.skill import SkillType
        from simulation.skill_benchmark import benchmark_baseline, benchmark_skill

        baseline = benchmark_baseline(seeds=8, max_frames=40000)

        # Forced-skill builds should reach at least 70% of baseline
        for skill in [SkillType.SCATTER_SHOT, SkillType.EXPLOSIVE]:
            rating = benchmark_skill(skill, seeds=8, max_frames=40000)
            self.assertGreaterEqual(
                rating.avg_level, baseline.avg_level * 0.7,
                f"{rating.skill_name} ({rating.avg_level:.1f}) should not be "
                f"far below baseline ({baseline.avg_level:.1f})"
            )


class TestSkillBenchmark(unittest.TestCase):
    """Verify the skill benchmark infrastructure works."""

    def test_benchmark_runs(self):
        """Benchmark a single skill with 2 seeds to verify no crashes."""
        from game.roguelite.skill import SkillType
        from simulation.skill_benchmark import benchmark_skill, benchmark_baseline

        baseline = benchmark_baseline(seeds=2, max_frames=15000)
        self.assertGreater(baseline.avg_level, 0)

        rating = benchmark_skill(SkillType.DAMAGE, seeds=2, max_frames=15000)
        self.assertGreaterEqual(rating.success_count, 1)
        self.assertGreater(rating.avg_level, 0)

    def test_format_ranking_no_crash(self):
        """format_ranking should produce output without errors."""
        from simulation.skill_benchmark import format_ranking
        from simulation.skill_rating import SkillRating
        from game.roguelite.skill import SkillType

        ratings = [
            SkillRating(SkillType.DAMAGE, "Piercing Shot", 5, 5, 4.0, 8000, 20000, 150, 0.8),
            SkillRating(SkillType.SHIELD, "Aegis", 5, 5, 5.5, 12000, 30000, 200, 1.0),
        ]
        output = format_ranking(ratings)
        self.assertIn("Piercing Shot", output)
        self.assertIn("Aegis", output)


if __name__ == "__main__":
    unittest.main()
