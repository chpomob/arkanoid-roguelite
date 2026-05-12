"""Bot simulation framework metrics and result types."""

from dataclasses import dataclass, field


@dataclass
class RunResult:
    """Outcome of a single simulated run."""

    seed: int
    level_reached: int
    score: int
    skills: list[str] = field(default_factory=list)
    bricks_broken: int = 0
    deaths: int = 0
    boss_kills: list[str] = field(default_factory=list)
    frames: int = 0
    reason: str = "unknown"

    @property
    def survived_seconds(self) -> float:
        return self.frames / 60.0


def aggregate(results: list[RunResult]) -> dict:
    """Compute summary statistics over multiple runs."""
    if not results:
        return {}
    levels = [r.level_reached for r in results]
    scores = [r.score for r in results]
    frames = [r.frames for r in results]
    return {
        "runs": len(results),
        "avg_level": sum(levels) / len(levels),
        "min_level": min(levels),
        "max_level": max(levels),
        "avg_score": sum(scores) / len(scores),
        "min_score": min(scores),
        "max_score": max(scores),
        "avg_frames": sum(frames) / len(frames),
        "avg_survived_s": sum(frames) / len(frames) / 60.0,
        "boss_kills": sum(len(r.boss_kills) for r in results),
        "deaths": sum(r.deaths for r in results),
    }
