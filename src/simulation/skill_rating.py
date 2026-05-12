"""Skill rating dataclass and analysis functions."""

from dataclasses import dataclass, field
from typing import Optional

from game.roguelite.skill import SkillType
from simulation.metrics import RunResult, aggregate


@dataclass
class SkillRating:
    """Performance metrics for a single skill across multiple seeded runs."""

    skill_type: SkillType
    skill_name: str
    seeds: int
    success_count: int  # runs where skill was acquired
    avg_level: float
    avg_score: float
    avg_frames: float
    avg_bricks: float
    completion_rate: float  # fraction that reached gameover (not max_frames)

    @property
    def tier(self) -> str:
        """Simple tier based on average level."""
        if self.avg_level >= 7:
            return "S"
        if self.avg_level >= 5:
            return "A"
        if self.avg_level >= 4:
            return "B"
        if self.avg_level >= 3:
            return "C"
        return "D"


def rating_from_results(skill_type: SkillType, name: str, results: list[RunResult], total_seeds: int) -> SkillRating:
    """Compute a SkillRating from a list of RunResults."""
    acquired = [r for r in results if skill_type.name in r.skills]
    if not acquired:
        return SkillRating(
            skill_type=skill_type, skill_name=name, seeds=total_seeds,
            success_count=0, avg_level=0, avg_score=0, avg_frames=0,
            avg_bricks=0, completion_rate=0,
        )

    stats = aggregate(acquired)
    completed = sum(1 for r in acquired if r.reason == "gameover")
    return SkillRating(
        skill_type=skill_type,
        skill_name=name,
        seeds=total_seeds,
        success_count=len(acquired),
        avg_level=stats["avg_level"],
        avg_score=stats["avg_score"],
        avg_frames=stats["avg_frames"],
        avg_bricks=sum(r.bricks_broken for r in acquired) / len(acquired),
        completion_rate=completed / len(acquired),
    )


def rank_skills(ratings: list[SkillRating]) -> list[SkillRating]:
    """Sort skills by average level (descending), breaking ties with score."""
    return sorted(ratings, key=lambda r: (r.avg_level, r.avg_score), reverse=True)


def format_ranking(ratings: list[SkillRating], baseline: Optional[SkillRating] = None) -> str:
    """Produce a human-readable skill ranking table."""
    lines = [f"{'#':>3} {'Skill':<24} {'Tier':>4} {'Lvl':>6} {'Score':>8} {'Frames':>8} {'Bricks':>7} {'Done%':>6}"]
    lines.append("-" * 72)

    ranked = rank_skills(ratings)
    for i, r in enumerate(ranked, 1):
        delta = ""
        if baseline and baseline.avg_level > 0:
            pct = (r.avg_level / baseline.avg_level - 1) * 100
            delta = f" {pct:+.0f}%"
        lines.append(
            f"{i:>3} {r.skill_name:<24} {r.tier:>4} "
            f"{r.avg_level:>6.1f} {r.avg_score:>8.0f} {r.avg_frames:>8.0f} "
            f"{r.avg_bricks:>7.0f} {r.completion_rate:>5.0%}{delta}"
        )

    if baseline:
        lines.append("")
        lines.append(f"Baseline (first-pick): Lvl={baseline.avg_level:.1f} Score={baseline.avg_score:.0f}")

    return "\n".join(lines)
