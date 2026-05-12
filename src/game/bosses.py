from dataclasses import dataclass
from random import choice
from typing import Optional

from game.ui import RETRO_PALETTE


BOSS_LEVEL_INTERVAL = 5


@dataclass(frozen=True)
class BossDefinition:
    boss_id: str
    name: str
    tier: int
    arena: str
    theme: str
    style: str
    hp: int
    cooldown: float
    speed: float
    color: tuple
    accent: tuple
    pattern: str
    briefing: str


BOSS_CATALOG: list[BossDefinition] = [
    BossDefinition(
        "gate_sentinel",
        "Gate Sentinel",
        1,
        "sentinel_gate",
        "Sentinel Gate",
        "Twin guard rails and a low central duelist.",
        8,
        1.55,
        1.05,
        RETRO_PALETTE["brick4"],
        RETRO_PALETTE["accent"],
        "spread",
        "Fires readable triple volleys. Break side cover, then punish the center lane.",
    ),
    BossDefinition(
        "pulse_mantis",
        "Pulse Mantis",
        1,
        "pulse_nest",
        "Pulse Nest",
        "Open center with pulse bricks bending rebounds.",
        7,
        1.25,
        1.35,
        RETRO_PALETTE["brick3"],
        RETRO_PALETTE["accent_alt"],
        "alternating",
        "Moves faster and alternates diagonal shots. Keep the ball angled, not vertical.",
    ),
    BossDefinition(
        "forge_warden",
        "Forge Warden",
        2,
        "forge_ring",
        "Forge Ring",
        "Bomb pockets around a heavy armored core.",
        10,
        2.00,
        1.20,
        (255, 128, 76),
        RETRO_PALETTE["brick1"],
        "burst",
        "Uses short burst fire. Bomb bricks can open big damage windows.",
    ),
    BossDefinition(
        "prism_regent",
        "Prism Regent",
        2,
        "prism_court",
        "Prism Court",
        "Prism lanes reward controlled split-ball pressure.",
        10,
        1.80,
        1.45,
        (204, 116, 255),
        RETRO_PALETTE["ball"],
        "fan",
        "Shoots wide fans and rewards builds that manage several balls safely.",
    ),
    BossDefinition(
        "sentry_archon",
        "Sentry Archon",
        3,
        "archon_bastion",
        "Archon Bastion",
        "Sentry pylons and charge bricks create a pressure arena.",
        16,
        1.60,
        1.55,
        (255, 92, 110),
        RETRO_PALETTE["danger"],
        "cross",
        "Layers side fire with sentry pressure. Shields and helper paddles shine here.",
    ),
    BossDefinition(
        "void_reactor",
        "Void Reactor",
        3,
        "reactor_eye",
        "Void Reactor",
        "Dense reactor shell with a dangerous central eye.",
        18,
        1.50,
        1.30,
        (94, 228, 198),
        RETRO_PALETTE["accent_alt"],
        "storm",
        "High health and escalating shot patterns. Clear charge bricks when you need tempo.",
    ),
]

BOSS_BY_ID: dict[str, BossDefinition] = {boss.boss_id: boss for boss in BOSS_CATALOG}


def is_boss_level(level: int) -> bool:
    return level > 0 and level % BOSS_LEVEL_INTERVAL == 0


def boss_tier_for_level(level: int) -> int:
    return max(1, min(3, level // BOSS_LEVEL_INTERVAL))


def bosses_for_level(level: int) -> list[BossDefinition]:
    tier = boss_tier_for_level(level)
    return [boss for boss in BOSS_CATALOG if boss.tier == tier]


def choose_boss_for_level(level: int) -> BossDefinition:
    return choice(bosses_for_level(level))


def boss_by_id(boss_id: str) -> BossDefinition:
    return BOSS_BY_ID[boss_id]
