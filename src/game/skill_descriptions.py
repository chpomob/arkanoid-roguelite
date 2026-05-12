"""Shared skill names and descriptions, used by engine and screens."""

from game.roguelite.skill import SkillType

HIGH_SCORE_LIMIT = 8


def get_description(skill_type: SkillType, level: int) -> str:
    names = {
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
        SkillType.TIME_WARP: "Time Warp",
        SkillType.CRITICAL_HIT: "Critical Hit",
        SkillType.GHOST_BALL: "Ghost Ball",
    }
    base = names.get(skill_type, skill_type.value)
    return f"{base} (Level {level})"
