import math
import pygame


def clamp_color(value):
    return max(0, min(255, int(value)))


def shade(color, amount):
    return tuple(clamp_color(channel + amount) for channel in color)


def mix(color_a, color_b, t):
    return tuple(clamp_color(color_a[i] * (1 - t) + color_b[i] * t) for i in range(3))


def draw_paddle_sprite(surface, rect, color, active=True):
    glow_color = (*color, 55 if active else 30)
    glow = pygame.Surface((rect.width + 22, rect.height + 22), pygame.SRCALPHA)
    pygame.draw.rect(glow, glow_color, glow.get_rect(), border_radius=10)
    surface.blit(glow, (rect.x - 11, rect.y - 9))

    shadow = rect.move(5, 6)
    pygame.draw.rect(surface, (0, 0, 0), shadow, border_radius=5)
    pygame.draw.rect(surface, shade(color, -62), rect.move(0, 2), border_radius=5)
    pygame.draw.rect(surface, color, rect, border_radius=5)
    pygame.draw.rect(surface, shade(color, 55), (rect.x + 8, rect.y + 3, max(0, rect.width - 16), 3), border_radius=2)
    pygame.draw.rect(surface, shade(color, -95), (rect.x + 7, rect.bottom - 5, max(0, rect.width - 14), 3), border_radius=2)
    pygame.draw.rect(surface, (235, 255, 247), rect, 1, border_radius=5)

    core_width = max(10, min(34, rect.width // 3))
    core = pygame.Rect(0, 0, core_width, max(4, rect.height - 6))
    core.center = rect.center
    pygame.draw.rect(surface, shade(color, 30), core, border_radius=3)
    pygame.draw.rect(surface, shade(color, -55), core, 1, border_radius=3)


def draw_ball_sprite(surface, rect, color, trail=None):
    """Draw an energy ball with glowing trail and specular highlight."""
    now = pygame.time.get_ticks() / 1000.0
    trail = trail or []
    n = len(trail)

    # Energy trail — fading circles growing larger
    for index, (tx, ty) in enumerate(trail):
        t = index / max(1, n)
        alpha = int(15 + t * 80)
        size = max(3, int(rect.width * (0.35 + t * 0.65)))
        ghost = pygame.Surface((size + 6, size + 6), pygame.SRCALPHA)
        # Soft trail halo
        for r_off in (3, 1, 0):
            r = size // 2 + r_off
            a = alpha // (r_off + 1)
            pygame.draw.circle(ghost, (*color, max(0, a)),
                               (ghost.get_width() // 2, ghost.get_height() // 2), r)
        surface.blit(ghost, (int(tx) - ghost.get_width() // 2, int(ty) - ghost.get_height() // 2))

    # Outer energy aura (pulsing)
    pulse_r = 1.0 + abs(math.sin(now * 4.0)) * 0.3
    aura_w = int(rect.width + 22 + pulse_r * 4)
    aura_h = int(rect.height + 22 + pulse_r * 4)
    glow = pygame.Surface((aura_w, aura_h), pygame.SRCALPHA)
    for i in range(5, 0, -1):
        r = aura_w // 2 - i * 2
        a = 20 + i * 6
        pygame.draw.circle(glow, (*color, a), (aura_w // 2, aura_h // 2), max(1, r))
    surface.blit(glow, (rect.centerx - aura_w // 2, rect.centery - aura_h // 2))

    # Solid body with shading
    r = max(2, rect.width // 2)
    pygame.draw.circle(surface, shade(color, -80), (rect.centerx + 2, rect.centery + 2), r)
    pygame.draw.circle(surface, color, rect.center, r - 1)

    # Specular highlight
    hl_x = rect.centerx - r // 3
    hl_y = rect.centery - r // 3
    pygame.draw.circle(surface, shade(color, 80), (hl_x, hl_y), max(1, r // 3))
    pygame.draw.circle(surface, (255, 240, 255), (hl_x - 1, hl_y - 1), max(1, r // 6))


def draw_brick_sprite(surface, rect, color, marker=None, hp=1, max_hp=1):
    shadow = rect.move(4, 5)
    pygame.draw.rect(surface, (0, 0, 0), shadow, border_radius=4)

    top = shade(color, 38)
    bottom = shade(color, -56)
    pygame.draw.rect(surface, bottom, rect, border_radius=4)
    inner = rect.inflate(-3, -4)
    if inner.width > 0 and inner.height > 0:
        pygame.draw.rect(surface, color, inner, border_radius=3)
        shine = pygame.Rect(inner.x + 3, inner.y + 3, max(0, inner.width - 6), 4)
        pygame.draw.rect(surface, top, shine, border_radius=2)

    left_cap = pygame.Rect(rect.x, rect.y + 4, 4, max(0, rect.height - 8))
    pygame.draw.rect(surface, top, left_cap, border_radius=2)
    pygame.draw.line(surface, shade(color, 80), rect.topleft, rect.topright, 2)
    pygame.draw.line(surface, shade(color, -105), rect.bottomleft, rect.bottomright, 2)

    if marker:
        draw_special_brick_frame(surface, rect, color, marker)

    if max_hp > 1:
        pip_width = 5
        start_x = rect.right - 7 - ((max_hp - 1) * (pip_width + 2))
        for index in range(max_hp):
            pip = pygame.Rect(start_x + index * (pip_width + 2), rect.bottom - 8, pip_width, 3)
            pip_color = (255, 255, 255) if index < hp else shade(color, -90)
            pygame.draw.rect(surface, pip_color, pip, border_radius=1)

    if marker:
        draw_kind_marker(surface, rect, marker)


def draw_kind_marker(surface, rect, marker):
    color = marker_color(marker)
    badge = marker_badge_rect(rect)
    pygame.draw.rect(surface, (7, 10, 14), badge.move(2, 2), border_radius=3)
    pygame.draw.rect(surface, (18, 24, 30), badge, border_radius=3)
    pygame.draw.rect(surface, color, badge, 1, border_radius=3)

    if marker == "tough":
        inner = badge.inflate(-8, -7)
        pygame.draw.rect(surface, color, inner, 2, border_radius=2)
        pygame.draw.line(surface, color, (inner.x + 3, inner.centery), (inner.right - 3, inner.centery), 1)
    elif marker == "bomb":
        pygame.draw.circle(surface, color, badge.center, 5, 2)
        for angle in range(0, 360, 45):
            dx = int(math.cos(math.radians(angle)) * 8)
            dy = int(math.sin(math.radians(angle)) * 6)
            pygame.draw.line(surface, color, badge.center, (badge.centerx + dx, badge.centery + dy), 1)
    elif marker == "pulse":
        pygame.draw.arc(surface, color, badge.inflate(-8, -6), math.radians(205), math.radians(515), 2)
        pygame.draw.arc(surface, color, badge.inflate(-16, -12), math.radians(205), math.radians(515), 1)
        pygame.draw.circle(surface, color, badge.center, 2)
    elif marker == "charge":
        points = [
            (badge.centerx + 1, badge.y + 4),
            (badge.centerx - 7, badge.centery + 1),
            (badge.centerx + 1, badge.centery + 1),
            (badge.centerx - 2, badge.bottom - 4),
            (badge.centerx + 8, badge.centery - 2),
            (badge.centerx, badge.centery - 2),
        ]
        pygame.draw.lines(surface, color, False, points, 2)
    elif marker == "regen":
        pygame.draw.line(surface, color, (badge.centerx, badge.y + 5), (badge.centerx, badge.bottom - 5), 3)
        pygame.draw.line(surface, color, (badge.centerx - 8, badge.centery), (badge.centerx + 8, badge.centery), 3)
        pygame.draw.arc(surface, color, badge.inflate(-5, -5), math.radians(30), math.radians(285), 1)
    elif marker == "prism":
        pygame.draw.polygon(surface, color, [(badge.centerx, badge.y + 4), (badge.right - 7, badge.bottom - 5), (badge.x + 7, badge.bottom - 5)], 2)
        pygame.draw.line(surface, color, (badge.x + 4, badge.centery), (badge.right - 4, badge.centery), 1)
        pygame.draw.line(surface, color, (badge.centerx, badge.bottom - 5), (badge.centerx - 9, badge.bottom + 2), 1)
        pygame.draw.line(surface, color, (badge.centerx, badge.bottom - 5), (badge.centerx + 9, badge.bottom + 2), 1)
    elif marker == "sentry":
        body = badge.inflate(-9, -8)
        pygame.draw.rect(surface, color, body, 2, border_radius=2)
        pygame.draw.circle(surface, color, body.center, 3)
        pygame.draw.line(surface, color, (body.centerx, body.bottom), (body.centerx, body.bottom + 5), 2)


def marker_badge_rect(rect):
    width = min(34, max(24, rect.width - 18))
    height = min(23, max(18, rect.height - 5))
    badge = pygame.Rect(0, 0, width, height)
    badge.center = rect.center
    return badge


def marker_color(marker):
    colors = {
        "tough": (236, 244, 255),
        "bomb": (255, 238, 146),
        "pulse": (166, 244, 255),
        "charge": (255, 245, 120),
        "regen": (174, 255, 190),
        "prism": (242, 190, 255),
        "sentry": (255, 210, 164),
    }
    return colors.get(marker, (246, 250, 247))


def draw_special_brick_frame(surface, rect, color, marker):
    accent = marker_color(marker)
    pygame.draw.rect(surface, accent, rect.inflate(-2, -2), 1, border_radius=4)
    if marker == "bomb":
        for corner in (rect.topleft, rect.topright, rect.bottomleft, rect.bottomright):
            pygame.draw.circle(surface, accent, corner, 2)
    elif marker == "pulse":
        pygame.draw.line(surface, accent, (rect.x + 6, rect.centery), (rect.right - 6, rect.centery), 1)
    elif marker == "charge":
        pygame.draw.rect(surface, accent, (rect.x + 5, rect.y + 4, 4, rect.height - 8), border_radius=1)
    elif marker == "regen":
        pygame.draw.circle(surface, accent, (rect.x + 7, rect.y + 7), 3, 1)
        pygame.draw.circle(surface, accent, (rect.right - 7, rect.bottom - 7), 3, 1)
    elif marker == "prism":
        pygame.draw.line(surface, accent, (rect.x + 6, rect.bottom - 5), (rect.centerx, rect.y + 4), 1)
        pygame.draw.line(surface, accent, (rect.right - 6, rect.bottom - 5), (rect.centerx, rect.y + 4), 1)
    elif marker == "sentry":
        pygame.draw.rect(surface, accent, (rect.right - 10, rect.y + 5, 5, 5), 1)


def draw_projectile_sprite(surface, rect, color):
    """Draw an energy bolt projectile with glow and motion streak."""
    # Outer energy glow
    glow_w, glow_h = rect.width + 14, rect.height + 18
    glow = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
    # Diamond/capsule glow shape
    pts = [
        (glow_w // 2, 0),
        (glow_w, glow_h // 3),
        (glow_w, glow_h * 2 // 3),
        (glow_w // 2, glow_h),
        (0, glow_h * 2 // 3),
        (0, glow_h // 3),
    ]
    pygame.draw.polygon(glow, (*color, 50), pts)
    surface.blit(glow, (rect.x - 7, rect.y - 9))

    # Motion streak behind the bolt
    streak_h = rect.height + 8
    streak_w = max(2, rect.width // 2)
    streak = pygame.Surface((streak_w + 8, streak_h), pygame.SRCALPHA)
    for i in range(4):
        y_offs = i * 2
        a = 30 - i * 6
        if a > 0:
            pygame.draw.rect(streak, (*color, a),
                             (2, y_offs, streak_w, streak_h - i * 4), border_radius=2)
    surface.blit(streak, (rect.centerx - streak_w // 2 - 4, rect.y - 4))

    # Main bolt body — bright capsule
    body = rect.inflate(0, -2)
    pygame.draw.rect(surface, shade(color, -40), body.move(0, 1), border_radius=3)
    pygame.draw.rect(surface, color, body, border_radius=3)

    # Hot core line
    core_y = rect.centery
    core_h = max(1, rect.height // 3)
    pygame.draw.line(surface, (255, 245, 235),
                     (rect.x + 2, core_y),
                     (rect.right - 2, core_y), core_h)

    # Leading edge bright tip
    tip = pygame.Surface((rect.width + 4, 6), pygame.SRCALPHA)
    pygame.draw.ellipse(tip, (*shade(color, 100), 80), tip.get_rect())
    surface.blit(tip, (rect.x - 2, rect.y - 3))


def draw_enemy_sprite(surface, rect, color):
    """Draw a robotic enemy with body segments, antenna, and pulsing core."""
    now = pygame.time.get_ticks() / 1000.0
    pulse_a = abs(math.sin(now * 2.3)) * 0.5 + 0.5

    # Outer glow
    glow = pygame.Surface((rect.width + 18, rect.height + 18), pygame.SRCALPHA)
    glow_alpha = 45 + int(pulse_a * 25)
    pygame.draw.ellipse(glow, (*color, glow_alpha), glow.get_rect())
    surface.blit(glow, (rect.x - 9, rect.y - 9))

    # Shadow
    pygame.draw.ellipse(surface, (0, 0, 0), rect.move(3, 4))

    # Main body — three stacked segments
    seg_h = max(4, rect.height // 3)
    for i in range(3):
        sy = rect.y + i * seg_h
        seg = pygame.Rect(rect.x + 2, sy, rect.width - 4, seg_h - 1)
        seg_color = shade(color, -20 + i * 12)
        pygame.draw.ellipse(surface, seg_color, seg)

    # Outer shell
    pygame.draw.ellipse(surface, shade(color, -55), rect, 2)

    # Core glow (pulsing)
    core_w = max(6, rect.width // 3)
    core_h = max(4, rect.height // 4)
    core = pygame.Rect(0, 0, core_w, core_h)
    core.center = (rect.centerx, rect.centery + rect.height // 6)
    core_alpha = 70 + int(pulse_a * 80)
    core_surf = pygame.Surface((core_w + 6, core_h + 6), pygame.SRCALPHA)
    pygame.draw.ellipse(core_surf, (*color, core_alpha // 2), core_surf.get_rect())
    pygame.draw.ellipse(core_surf, (*shade(color, 80), core_alpha),
                        (3, 3, core_w, core_h))
    surface.blit(core_surf, (core.x - 3, core.y - 3))

    # Eyes — larger, with glowing pupils
    eye_y = rect.y + rect.height // 3
    eye_r = max(2, rect.width // 10)
    for ex in (rect.centerx - rect.width // 5, rect.centerx + rect.width // 5):
        pygame.draw.circle(surface, (2, 4, 8), (ex, eye_y), eye_r + 2)
        pygame.draw.circle(surface, (10, 14, 20), (ex, eye_y), eye_r)
        pupil_color = (220, 240, 255) if pulse_a > 0.6 else (140, 180, 220)
        pygame.draw.circle(surface, pupil_color, (ex, eye_y), max(1, eye_r // 2))

    # Antenna — thin stalk with glowing tip
    ant_x = rect.centerx
    ant_top = rect.y - 4
    ant_bot = rect.y + 2
    pygame.draw.line(surface, shade(color, -90), (ant_x, ant_bot), (ant_x + 2, ant_top), 1)
    ant_tip_a = 80 + int(pulse_a * 80)
    tip = pygame.Surface((6, 6), pygame.SRCALPHA)
    pygame.draw.circle(tip, (*color, ant_tip_a), (3, 3), 2)
    surface.blit(tip, (ant_x - 1, ant_top - 3))

    # Bottom ridge
    pygame.draw.line(surface, shade(color, -70),
                     (rect.x + rect.width // 4, rect.bottom - 2),
                     (rect.right - rect.width // 4, rect.bottom - 2), 1)


def draw_boss_sprite(surface, rect, color, accent, phase=0.0):
    glow = pygame.Surface((rect.width + 34, rect.height + 34), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (*accent, 52), glow.get_rect())
    surface.blit(glow, (rect.x - 17, rect.y - 17))

    shadow = rect.move(6, 8)
    pygame.draw.ellipse(surface, (0, 0, 0), shadow)
    pygame.draw.ellipse(surface, shade(color, -78), rect)
    core = rect.inflate(-10, -8)
    pygame.draw.ellipse(surface, color, core)
    pygame.draw.ellipse(surface, shade(color, 55), core.inflate(-16, -12))

    wing_y = rect.centery + 3
    left_wing = [
        (rect.left + 8, wing_y),
        (rect.left - 18, rect.centery - 10),
        (rect.left + 2, rect.bottom - 4),
    ]
    right_wing = [
        (rect.right - 8, wing_y),
        (rect.right + 18, rect.centery - 10),
        (rect.right - 2, rect.bottom - 4),
    ]
    pygame.draw.polygon(surface, shade(color, -34), left_wing)
    pygame.draw.polygon(surface, shade(color, -34), right_wing)
    pygame.draw.polygon(surface, accent, left_wing, 2)
    pygame.draw.polygon(surface, accent, right_wing, 2)

    eye_radius = 6 + int((math.sin(phase * 4.0) + 1) * 1.5)
    pygame.draw.circle(surface, (8, 10, 16), rect.center, eye_radius + 4)
    pygame.draw.circle(surface, accent, rect.center, eye_radius)
    pygame.draw.circle(surface, shade(accent, 72), (rect.centerx - 2, rect.centery - 2), max(2, eye_radius // 2))
    pygame.draw.arc(surface, shade(accent, 45), rect.inflate(-18, -14), math.radians(200), math.radians(340), 2)
    pygame.draw.arc(surface, shade(accent, -35), rect.inflate(-28, -22), math.radians(20), math.radians(160), 2)


def draw_skill_icon(surface, rect, code, color):
    pygame.draw.rect(surface, (8, 12, 18), rect, border_radius=7)
    pygame.draw.rect(surface, color, rect, 2, border_radius=7)
    center = rect.center
    if code in ("DMG", "FCS"):
        pygame.draw.polygon(surface, color, [(center[0], rect.y + 10), (rect.right - 12, rect.bottom - 10), (rect.x + 12, rect.bottom - 10)])
    elif code in ("VMP", "HP"):
        pygame.draw.circle(surface, color, (center[0] - 6, center[1] - 4), 7)
        pygame.draw.circle(surface, color, (center[0] + 6, center[1] - 4), 7)
        pygame.draw.polygon(surface, color, [(rect.x + 10, center[1]), (rect.right - 10, center[1]), center])
    elif code in ("MB", "SPL"):
        pygame.draw.circle(surface, color, (center[0] - 7, center[1]), 6)
        pygame.draw.circle(surface, color, (center[0] + 7, center[1]), 6)
    elif code in ("LZR", "VOL"):
        pygame.draw.line(surface, color, (center[0], rect.y + 9), (center[0], rect.bottom - 9), 4)
        pygame.draw.line(surface, color, (center[0] - 10, center[1] + 8), (center[0] + 10, center[1] - 8), 2)
    elif code in ("WID", "DRN"):
        pygame.draw.rect(surface, color, (rect.x + 10, center[1] - 4, rect.width - 20, 8), border_radius=4)
    elif code == "MAG":
        pygame.draw.arc(surface, color, rect.inflate(-16, -14), math.radians(50), math.radians(310), 4)
        pygame.draw.arc(surface, color, rect.inflate(-30, -24), math.radians(50), math.radians(310), 3)
    elif code == "SHD":
        pygame.draw.polygon(surface, color, [(center[0], rect.y + 8), (rect.right - 11, rect.y + 17), (rect.right - 15, rect.bottom - 12), (center[0], rect.bottom - 7), (rect.x + 15, rect.bottom - 12), (rect.x + 11, rect.y + 17)])
    else:
        font = pygame.font.SysFont("dejavusansmono,consolas,arial", 15, True)
        text = font.render(code[:3], True, color)
        surface.blit(text, text.get_rect(center=center))


def draw_life(surface, center, color, radius=6):
    pygame.draw.circle(surface, shade(color, -70), (center[0] + 2, center[1] + 2), radius)
    pygame.draw.circle(surface, color, center, radius)
    pygame.draw.circle(surface, shade(color, 70), (center[0] - 2, center[1] - 2), max(2, radius // 3))
