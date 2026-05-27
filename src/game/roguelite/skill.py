import pygame
from enum import Enum
from game.assets import draw_skill_icon, shade
from game.ui import draw_bar, draw_glow_text, draw_panel, draw_soft_glow, draw_text, draw_wrapped_text, RETRO_PALETTE, _font

class SkillType(Enum):
    DAMAGE = "Dmg"
    VAMPIRE = "Vamp"
    MULTI_BALL = "Multi"
    LASER = "Laser"
    SPEED_UP = "Tempo"
    PADDLE_WIDE = "Wide"
    HEAL = "Heal"
    CONTROL = "Aim"
    GIANT_BALL = "Heavy"
    EXPLOSIVE = "Blast"
    SHIELD = "Shield"
    MAGNET = "Mag"
    CHOICE = "Choice"
    DRONES = "Drone"
    SPLIT_CHARGE = "Split"
    VOLLEY = "Volley"
    FOCUS = "Focus"
    CANNON = "Cannon"
    GRAVITY_WELL = "Well"
    RICOCHET = "Bounce"
    SEEKER = "Seeker"
    ECHO_PADDLES = "Echo"
    SCATTER_SHOT = "Scatter"
    PIERCING_SHOTS = "Pierce"
    CHAIN_SPARK = "Spark"
    STASIS_FIELD = "Stasis"
    PATROL_PADDLES = "Patrol"
    TIME_WARP = "TimeWarp"
    CRITICAL_HIT = "Crit"
    GHOST_BALL = "Ghost"

class Skill:
    def __init__(self, skill_type: SkillType, description: str):
        self.type = skill_type
        self.description = description
        self.level = 1 # Can scale

SKILL_META = {
    SkillType.DAMAGE: ("DMG", RETRO_PALETTE["brick4"], "Extra brick damage"),
    SkillType.VAMPIRE: ("VMP", RETRO_PALETTE["brick2"], "Charge healing on hits"),
    SkillType.MULTI_BALL: ("MB", RETRO_PALETTE["brick3"], "Add another ball"),
    SkillType.LASER: ("LZR", RETRO_PALETTE["brick1"], "Paddle-hit projectile"),
    SkillType.SPEED_UP: ("TMP", RETRO_PALETTE["accent"], "Slower, steadier tempo"),
    SkillType.PADDLE_WIDE: ("WID", RETRO_PALETTE["paddle"], "Wider paddle"),
    SkillType.HEAL: ("HP", RETRO_PALETTE["paddle"], "Restore a life"),
    SkillType.CONTROL: ("CTL", RETRO_PALETTE["accent_alt"], "Sharper paddle aiming"),
    SkillType.GIANT_BALL: ("HVY", RETRO_PALETTE["ball"], "Larger hit box"),
    SkillType.EXPLOSIVE: ("BST", RETRO_PALETTE["brick1"], "Splash brick damage"),
    SkillType.SHIELD: ("SHD", RETRO_PALETTE["brick3"], "Blocks incoming damage"),
    SkillType.MAGNET: ("MAG", RETRO_PALETTE["accent_alt"], "Pull falling balls"),
    SkillType.CHOICE: ("OPT", RETRO_PALETTE["accent"], "More upgrade choices"),
    SkillType.DRONES: ("DRN", RETRO_PALETTE["paddle"], "Auto-fire projectiles"),
    SkillType.SPLIT_CHARGE: ("SPL", RETRO_PALETTE["brick2"], "Charged ball split"),
    SkillType.VOLLEY: ("VOL", RETRO_PALETTE["brick3"], "Spread projectiles"),
    SkillType.FOCUS: ("FCS", RETRO_PALETTE["brick4"], "Smaller, stronger paddle"),
    SkillType.CANNON: ("CAN", RETRO_PALETTE["brick1"], "Up fires a bolt"),
    SkillType.GRAVITY_WELL: ("WEL", RETRO_PALETTE["accent_alt"], "Down bends falling balls"),
    SkillType.RICOCHET: ("RCH", RETRO_PALETTE["brick3"], "Diagonal shots bounce"),
    SkillType.SEEKER: ("SKR", RETRO_PALETTE["brick2"], "Auto-aiming shots"),
    SkillType.ECHO_PADDLES: ("ECO", RETRO_PALETTE["paddle"], "Extra hover paddles"),
    SkillType.SCATTER_SHOT: ("SCT", RETRO_PALETTE["brick1"], "Fan of quick shots"),
    SkillType.PIERCING_SHOTS: ("PRC", RETRO_PALETTE["brick4"], "Shots pierce bricks"),
    SkillType.CHAIN_SPARK: ("SPK", RETRO_PALETTE["brick2"], "Hit chains damage"),
    SkillType.STASIS_FIELD: ("STS", RETRO_PALETTE["accent_alt"], "Slows falling balls"),
    SkillType.PATROL_PADDLES: ("PTL", RETRO_PALETTE["paddle"], "Moving helper paddle"),
    SkillType.TIME_WARP: ("WARP", RETRO_PALETTE["brick3"], "Slows ball near paddle"),
    SkillType.CRITICAL_HIT: ("CRIT", RETRO_PALETTE["brick1"], "Chance to deal 2x damage"),
    SkillType.GHOST_BALL: ("GHST", RETRO_PALETTE["ball"], "Pierce first brick"),
}

RARITY_COLORS = {
    "common": RETRO_PALETTE["line"],
    "uncommon": RETRO_PALETTE["paddle"],
    "rare": RETRO_PALETTE["brick3"],
    "epic": RETRO_PALETTE["brick2"],
}

SYNERGY_HINTS = {
    SkillType.CANNON: "Pairs with Volley and Damage",
    SkillType.VOLLEY: "Pairs with Cannon and Focus",
    SkillType.SPLIT_CHARGE: "Pairs with Multi and Control",
    SkillType.MULTI_BALL: "Pairs with Split and Magnet",
    SkillType.PADDLE_WIDE: "Pairs with Focus and Echo",
    SkillType.FOCUS: "Pairs with Wide and Cannon",
    SkillType.GRAVITY_WELL: "Pairs with Magnet and Control",
    SkillType.MAGNET: "Pairs with Multi and Well",
    SkillType.EXPLOSIVE: "Pairs with Damage",
    SkillType.VAMPIRE: "Pairs with Charge bricks",
    SkillType.RICOCHET: "Pairs with Volley and Cannon",
    SkillType.SEEKER: "Pairs with Damage and Focus",
    SkillType.ECHO_PADDLES: "Pairs with Patrol and Wide",
    SkillType.SCATTER_SHOT: "Pairs with Pierce and Ricochet",
    SkillType.PIERCING_SHOTS: "Pairs with Cannon and Scatter",
    SkillType.CHAIN_SPARK: "Pairs with Damage and Blast",
    SkillType.STASIS_FIELD: "Pairs with Tempo and Magnet",
    SkillType.PATROL_PADDLES: "Pairs with Echo and Control",
}

UPGRADE_HINTS = {
    SkillType.DAMAGE: "+damage on every brick hit",
    SkillType.VAMPIRE: "faster heal charge gain",
    SkillType.MULTI_BALL: "more active ball pressure",
    SkillType.LASER: "improved reliability",
    SkillType.SPEED_UP: "stronger level speed reduction",
    SkillType.PADDLE_WIDE: "larger safety window",
    SkillType.HEAL: "restore another life now",
    SkillType.CONTROL: "wider aiming range",
    SkillType.GIANT_BALL: "larger ball hit box",
    SkillType.EXPLOSIVE: "larger splash radius",
    SkillType.SHIELD: "add another block charge",
    SkillType.MAGNET: "stronger ball pull",
    SkillType.CHOICE: "more future draft control",
    SkillType.DRONES: "faster auto-fire rate",
    SkillType.SPLIT_CHARGE: "more split charges",
    SkillType.VOLLEY: "wider projectile spread",
    SkillType.FOCUS: "more damage tradeoff",
    SkillType.CANNON: "lower cooldown and side bolts",
    SkillType.GRAVITY_WELL: "stronger active bend",
    SkillType.RICOCHET: "more wall bounces",
    SkillType.SEEKER: "faster auto fire rate",
    SkillType.ECHO_PADDLES: "more hover coverage",
    SkillType.SCATTER_SHOT: "up to 4 fan bolts",
    SkillType.PIERCING_SHOTS: "more pierced targets",
    SkillType.CHAIN_SPARK: "more chained hits",
    SkillType.STASIS_FIELD: "stronger slow field",
    SkillType.PATROL_PADDLES: "wider moving coverage",
}

SKILL_GUIDE = {
    SkillType.DAMAGE: {
        "effect": "Each level adds one extra damage to every brick hit.",
        "use": "Passive. Best when tough bricks start appearing.",
        "scales": "More levels stack linearly with Focus damage.",
    },
    SkillType.VAMPIRE: {
        "effect": "Brick hits build energy; at 10+ energy, a missing life is restored up to the life cap. Energy gain caps at 2 per hit.",
        "use": "Passive. Keep pressure on bricks and prioritize Charge bricks.",
        "scales": "Higher levels raise the heal threshold slightly but also boost energy per hit.",
    },
    SkillType.MULTI_BALL: {
        "effect": "Adds extra active balls at the start of each level.",
        "use": "Passive. Strong for clearing, risky when the screen gets crowded.",
        "scales": "Each level adds another ball source.",
    },
    SkillType.LASER: {
        "effect": "Paddle bounces fire an upward projectile from the ball position.",
        "use": "Passive trigger. Aim paddle hits under dense brick clusters.",
        "scales": "Projectile damage is fixed; upgrades improve reliability.",
    },
    SkillType.SPEED_UP: {
        "effect": "Slows the ball slightly and offsets level-based speed growth.",
        "use": "Passive. Pick when the run is becoming too fast to read.",
        "scales": "Each level lowers base tempo and reduces more difficulty speed.",
    },
    SkillType.PADDLE_WIDE: {
        "effect": "Increases paddle width for a larger recovery window.",
        "use": "Passive. Good defensive pick and strong with Echo.",
        "scales": "Each level adds more width, with Focus subtracting some width.",
    },
    SkillType.HEAL: {
        "effect": "Immediately restores life, up to the life cap; overflow becomes shield charges.",
        "use": "Instant passive. Pick when survival matters more than power.",
        "scales": "Each level restores another life or converts excess healing into shields.",
    },
    SkillType.CONTROL: {
        "effect": "Widened paddle aiming range and stronger anti-vertical nudge.",
        "use": "Passive. Hit different paddle zones to choose sharper outgoing angles.",
        "scales": "Each level increases max bounce angle and center nudge.",
    },
    SkillType.GIANT_BALL: {
        "effect": "Increases ball size for easier brick and paddle contact.",
        "use": "Passive. Pairs well with splash and multiball clearing.",
        "scales": "Each level grows the ball until the size cap.",
    },
    SkillType.EXPLOSIVE: {
        "effect": "Destroyed bricks splash damage to nearby bricks.",
        "use": "Passive. Target packed clusters and high-value special bricks.",
        "scales": "Higher levels increase splash radius.",
    },
    SkillType.SHIELD: {
        "effect": "Adds a charge that blocks incoming damage from enemy shots.",
        "use": "Passive charge. It does not prevent missed balls; keep the ball in play.",
        "scales": "Each level adds another shield charge and strengthens the paddle aura.",
    },
    SkillType.MAGNET: {
        "effect": "Falling balls are gently pulled toward the paddle.",
        "use": "Passive. Works only while the ball is falling.",
        "scales": "Each level increases pull strength.",
    },
    SkillType.CHOICE: {
        "effect": "Adds extra options to future upgrade drafts.",
        "use": "Passive. Pick early when building around specific combos.",
        "scales": "First level adds a fourth card; second level adds a fifth card.",
    },
    SkillType.DRONES: {
        "effect": "Auto-fires projectiles upward from both sides of the paddle.",
        "use": "Passive. Provides steady offensive pressure above the paddle.",
        "scales": "Higher levels reduce the cooldown between volleys.",
    },
    SkillType.SPLIT_CHARGE: {
        "effect": "Grants charges that split a ball after paddle contact.",
        "use": "Passive charge. Bounces consume charges automatically while under the ball cap.",
        "scales": "Upgrades grant more charges.",
    },
    SkillType.VOLLEY: {
        "effect": "Paddle bounces fire two angled spread projectiles.",
        "use": "Passive trigger. Best when enemies or side brick clusters are active.",
        "scales": "Higher levels widen the spread.",
    },
    SkillType.FOCUS: {
        "effect": "Shrinks the paddle but adds extra brick damage.",
        "use": "Passive tradeoff. Take it when Wide, Echo, or Shield offset the risk.",
        "scales": "More levels add damage while the width penalty stays capped and moderate.",
    },
    SkillType.CANNON: {
        "effect": "Fires an upward charged bolt on command.",
        "use": "Active. Press Up or W when the cooldown is ready.",
        "scales": "Upgrades lower cooldown and add side bolts. Damage is fixed.",
    },
    SkillType.GRAVITY_WELL: {
        "effect": "Bends and slows falling balls while held.",
        "use": "Active. Hold Down or S to pull falling balls toward the paddle.",
        "scales": "Upgrades strengthen the pull and slow effect.",
    },
    SkillType.RICOCHET: {
        "effect": "Paddle hits fire diagonal projectiles that bounce off side walls.",
        "use": "Passive trigger. Use angled rebounds to spray side lanes and corner bricks.",
        "scales": "Upgrades add wall bounces. Damage is fixed.",
    },
    SkillType.SEEKER: {
        "effect": "Automatically fires an aimed bolt at the nearest enemy or active brick.",
        "use": "Automatic. Keep the paddle alive while it picks off pressure targets.",
        "scales": "Upgrades reduce cooldown. Damage is fixed.",
    },
    SkillType.ECHO_PADDLES: {
        "effect": "Adds small hover paddles above the main paddle for extra rebound saves.",
        "use": "Passive. These feel like defensive drones and help catch awkward angles.",
        "scales": "Upgrades add wider and additional echo paddles.",
    },
    SkillType.SCATTER_SHOT: {
        "effect": "Paddle hits fire a fan of several light projectiles.",
        "use": "Passive trigger. Good for cleaning weak bricks across a wide lane.",
        "scales": "Upgrades add more fan projectiles up to a controlled cap.",
    },
    SkillType.PIERCING_SHOTS: {
        "effect": "Projectiles continue through a limited number of brick hits.",
        "use": "Passive. Works best with Cannon, Scatter, Ricochet, and Seeker shots.",
        "scales": "Each level lets shots pierce one more target.",
    },
    SkillType.CHAIN_SPARK: {
        "effect": "Ball hits arc damage into nearby active bricks.",
        "use": "Passive. Strong into clustered formations without requiring brick destruction.",
        "scales": "Upgrades add more chained targets.",
    },
    SkillType.STASIS_FIELD: {
        "effect": "Falling balls slow slightly near the paddle.",
        "use": "Passive. Gives more time to read dangerous returns without stopping the game.",
        "scales": "Upgrades strengthen the slow while keeping a minimum speed.",
    },
    SkillType.PATROL_PADDLES: {
        "effect": "Adds moving helper paddles that sweep above the main paddle.",
        "use": "Passive. They create active drone-like saves at changing positions.",
        "scales": "Upgrades widen the patrol and add a second mirrored helper.",
    },
    SkillType.TIME_WARP: {
        "effect": "Slows the ball when it approaches the paddle, giving more reaction time.",
        "use": "Passive. Automatically slows the ball in the danger zone near the paddle.",
        "scales": "Stronger slow effect and larger activation zone per level.",
    },
    SkillType.CRITICAL_HIT: {
        "effect": "Ball hits have a chance to deal double damage to bricks.",
        "use": "Passive. Procs randomly on each brick hit.",
        "scales": "Higher crit chance per level.",
    },
    SkillType.GHOST_BALL: {
        "effect": "Ball passes through the first brick it hits without bouncing.",
        "use": "Passive. First brick each volley is pierced (no damage bonus).",
        "scales": "More bricks pierced per volley at higher levels.",
    },
}


def skill_rarity(skill_type, level):
    level = max(1, level)
    if level >= 4:
        return "epic"
    if level >= 3:
        return "rare"
    if level >= 2 or skill_type in (SkillType.CANNON, SkillType.GRAVITY_WELL, SkillType.SPLIT_CHARGE, SkillType.DRONES, SkillType.RICOCHET, SkillType.SEEKER, SkillType.ECHO_PADDLES, SkillType.SCATTER_SHOT, SkillType.PIERCING_SHOTS, SkillType.CHAIN_SPARK, SkillType.STASIS_FIELD, SkillType.PATROL_PADDLES):
        return "uncommon"
    return "common"


def skill_synergy(skill_type):
    return SYNERGY_HINTS.get(skill_type, "Flexible build option")


def skill_upgrade_hint(skill_type):
    return UPGRADE_HINTS.get(skill_type, "improves this upgrade")


class SkillCard:
    def __init__(self, skill: Skill, x: int, y: int, width=200, height=150):
        self.skill = skill
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.selected = False

    def visual_rect(self, hovered=False):
        return self.rect.move(0, -6 if hovered else (-2 if self.selected else 0))

    def content_layout(self, visual_rect):
        progress = pygame.Rect(visual_rect.x + 18, visual_rect.bottom - 22, visual_rect.width - 36, 6)
        synergy = pygame.Rect(visual_rect.x + 18, progress.y - 18, visual_rect.width - 36, 14)
        hint = pygame.Rect(visual_rect.x + 18, synergy.y - 28, visual_rect.width - 36, 24)
        desc_top = visual_rect.y + 78
        desc_bottom = max(desc_top + 18, hint.y - 4)
        desc = pygame.Rect(visual_rect.x + 18, desc_top, visual_rect.width - 36, desc_bottom - desc_top)
        return desc, hint, synergy, progress

    def draw(self, screen, mouse_pos=None):
        mouse_pos = mouse_pos or (-1, -1)
        hovered = self.rect.collidepoint(mouse_pos)
        code, accent, tagline = SKILL_META.get(self.skill.type, ("UP", RETRO_PALETTE["accent_alt"], "Upgrade"))
        rarity = skill_rarity(self.skill.type, self.skill.level)
        rarity_color = RARITY_COLORS[rarity]
        fill = (24, 31, 38) if hovered or self.selected else RETRO_PALETTE["panel"]
        border = RETRO_PALETTE["paddle"] if self.selected else rarity_color
        visual_rect = self.visual_rect(hovered)

        if hovered or self.selected:
            draw_soft_glow(screen, visual_rect, border, alpha=44 if hovered else 30, spread=11, radius=8)

        draw_panel(screen, visual_rect, accent=border, fill=fill)

        badge = pygame.Rect(visual_rect.x + 18, visual_rect.y + 22, 44, 44)
        draw_skill_icon(screen, badge, code, accent)

        level_label = pygame.Rect(visual_rect.right - 70, visual_rect.y + 18, 50, 22)
        pygame.draw.rect(screen, shade(rarity_color, -8), level_label, border_radius=4)
        pygame.draw.rect(screen, shade(rarity_color, 55), level_label, 1, border_radius=4)
        draw_text(screen, f"LV{self.skill.level}", (8, 10, 14), level_label.centerx, level_label.centery, 10, True, center=True, shadow=False)
        draw_text(screen, rarity.upper(), rarity_color, level_label.centerx, visual_rect.y + 52, 9, True, center=True, shadow=False)

        title_x = visual_rect.x + 74
        title = self.skill.type.value.upper()
        title_font_size = 18
        title_font = _font(title_font_size, True)
        max_title_width = max(40, level_label.x - title_x - 8)
        while title_font.size(title)[0] > max_title_width and len(title) > 3:
            title = title[:-1]
        if hovered or self.selected:
            draw_glow_text(screen, title, RETRO_PALETTE["text_white"], title_x, visual_rect.y + 24, title_font_size, True, glow_color=accent)
        else:
            draw_text(screen, title, RETRO_PALETTE["text_white"], title_x, visual_rect.y + 24, title_font_size, True)

        tagline_rect = pygame.Rect(title_x, visual_rect.y + 46, max(40, level_label.x - title_x - 6), 24)
        draw_wrapped_text(screen, tagline, RETRO_PALETTE["text_muted"], tagline_rect, 12, 2)

        desc_rect, hint_rect, synergy_rect, progress_rect = self.content_layout(visual_rect)
        draw_wrapped_text(screen, self.skill.description, RETRO_PALETTE["text"], desc_rect, 14, 3)

        draw_wrapped_text(screen, f"Next: {skill_upgrade_hint(self.skill.type)}", RETRO_PALETTE["text_muted"], hint_rect, 12, 2)
        draw_wrapped_text(screen, skill_synergy(self.skill.type), rarity_color, synergy_rect, 11, 1)

        draw_bar(screen, progress_rect, min(self.skill.level, 5), 5, rarity_color)

        if hovered or self.selected:
            pygame.draw.rect(screen, border, visual_rect.inflate(6, 6), 2, border_radius=8)

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.selected = True
            return True
        return False
