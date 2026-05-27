import math
import random
import pygame
from game.assets import shade, mix

RETRO_PALETTE = {
    "bg_top": (9, 12, 18),
    "bg_bot": (18, 28, 34),
    "grid": (31, 82, 88),
    "panel": (19, 24, 31),
    "panel_soft": (28, 34, 42),
    "panel_deep": (10, 12, 16),
    "line": (75, 103, 116),
    "paddle": (0, 228, 138),
    "ball": (255, 64, 198),
    "brick1": (255, 214, 90),
    "brick2": (255, 113, 164),
    "brick3": (68, 214, 255),
    "brick4": (255, 86, 86),
    "accent": (255, 188, 66),
    "accent_alt": (111, 232, 214),
    "text": (183, 236, 222),
    "text_muted": (126, 152, 158),
    "text_white": (246, 250, 247),
    "danger": (255, 86, 86),
}


def _font(size, bold=False):
    try:
        return pygame.font.SysFont("dejavusansmono,consolas,arial", size, bold)
    except Exception:
        pass
    try:
        return pygame.font.Font(None, size)
    except Exception:
        pass
    return pygame.font.Font(None, size)


def ui_time():
    return pygame.time.get_ticks() / 1000.0


def pulse(speed=2.0, phase=0.0):
    return (math.sin(ui_time() * speed + phase) + 1) * 0.5


def draw_text(surface, text, color, x, y, font_size=18, bold=False, center=False, shadow=True):
    font = _font(font_size, bold)
    if shadow:
        shade = font.render(str(text), True, (0, 0, 0))
        shadow_rect = shade.get_rect()
        if center:
            shadow_rect.center = (x + 2, y + 2)
        else:
            shadow_rect.topleft = (x + 2, y + 2)
        surface.blit(shade, shadow_rect)

    text_surface = font.render(str(text), True, color)
    rect = text_surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(text_surface, rect)
    return rect


def draw_glow_text(surface, text, color, x, y, font_size=18, bold=False, center=False, glow_color=None):
    glow_color = glow_color or color
    font = _font(font_size, bold)
    text_surface = font.render(str(text), True, color)
    rect = text_surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    glow = pygame.Surface((rect.width + 24, rect.height + 24), pygame.SRCALPHA)
    glow_text = font.render(str(text), True, glow_color)
    glow_text.set_alpha(30)
    for dx, dy in ((-5, 0), (5, 0), (0, -5), (0, 5), (-3, -3), (3, -3), (-3, 3), (3, 3)):
        glow.blit(glow_text, (12 + dx, 12 + dy))
    surface.blit(glow, (rect.x - 12, rect.y - 12))
    surface.blit(text_surface, rect)
    return rect


def draw_corner_brackets(surface, rect, color, length=18, width=2, inset=6):
    corners = [
        ((rect.left + inset, rect.top + inset), 1, 1),
        ((rect.right - inset, rect.top + inset), -1, 1),
        ((rect.left + inset, rect.bottom - inset), 1, -1),
        ((rect.right - inset, rect.bottom - inset), -1, -1),
    ]
    for (x, y), sx, sy in corners:
        pygame.draw.line(surface, color, (x, y), (x + sx * length, y), width)
        pygame.draw.line(surface, color, (x, y), (x, y + sy * length), width)


def draw_soft_glow(surface, rect, color, alpha=34, spread=12, radius=8):
    glow = pygame.Surface((rect.width + spread * 2, rect.height + spread * 2), pygame.SRCALPHA)
    pygame.draw.rect(glow, (*color, alpha), glow.get_rect(), border_radius=radius + spread)
    surface.blit(glow, (rect.x - spread, rect.y - spread))


def draw_arcade_button(surface, rect, label, accent=None, active=True, phase=0.0):
    accent = accent or RETRO_PALETTE["accent"]
    beat = pulse(3.0, phase) if active else 0.15
    draw_soft_glow(surface, rect, accent, alpha=28 + int(beat * 40), spread=11, radius=8)
    pygame.draw.rect(surface, (0, 0, 0), rect.move(0, 7), border_radius=6)
    pygame.draw.rect(surface, shade(accent, -22), rect, border_radius=6)
    pygame.draw.rect(surface, accent, rect.inflate(-4, -4), border_radius=4)
    pygame.draw.line(surface, shade(accent, 72), (rect.x + 12, rect.y + 8), (rect.right - 12, rect.y + 8), 2)
    pygame.draw.line(surface, shade(accent, -72), (rect.x + 12, rect.bottom - 7), (rect.right - 12, rect.bottom - 7), 2)
    draw_corner_brackets(surface, rect, (255, 245, 180), length=14, width=1, inset=4)
    draw_text(surface, label, (10, 12, 16), rect.centerx, rect.centery, 20, True, center=True, shadow=False)


def wrap_text(text, font_size, max_width):
    font = _font(font_size)
    lines = []
    current = ""
    for word in str(text).split():
        candidate = word if not current else f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped_text(surface, text, color, rect, font_size=16, line_gap=4):
    y = rect.y
    for line in wrap_text(text, font_size, rect.width):
        if y + font_size > rect.bottom:
            break
        draw_text(surface, line, color, rect.x, y, font_size, False, shadow=False)
        y += font_size + line_gap
    return y


def _draw_gradient(surface, top_color, bot_color):
    """Draw vertical gradient efficiently using block fills instead of per-pixel lines."""
    width, height = surface.get_size()
    block_h = max(1, height // 64)  # 64 blocks instead of height lines
    for i in range(64):
        y_start = i * block_h
        y_end = min(height, (i + 1) * block_h)
        if y_start >= height:
            break
        t = (y_start + y_end) / (2 * height)
        color = tuple(int(top_color[j] * (1 - t) + bot_color[j] * t) for j in range(3))
        pygame.draw.rect(surface, color, (0, y_start, width, y_end - y_start))

def draw_background(surface, boss=None, seed=None, theme=""):
    """Draw the background with seeded variation for replay diversity."""
    if boss is not None:
        draw_boss_background(surface, boss, seed=seed)
        return

    width, height = surface.get_size()
    now = ui_time()
    rng = random.Random(seed if seed else 42)

    # Theme-tinted gradient
    tint = _theme_tint(theme, seed) if theme else (0, 0, 0)
    bg_top = tuple(max(0, min(255, RETRO_PALETTE["bg_top"][i] + tint[i])) for i in range(3))
    bg_bot = tuple(max(0, min(255, RETRO_PALETTE["bg_bot"][i] + tint[i])) for i in range(3))

    _draw_gradient(surface, bg_top, bg_bot)

    horizon = int(height * 0.62)

    # ── Celestial body (theme-specific large sky object) ──
    _draw_celestial_body(surface, theme, seed, now, bg_top, horizon)

    # Seeded star field
    for (x, y, size, color, phase) in background_stars(width, height, seed):
        twinkle = 0.25 + 0.55 * ((math.sin(now * 1.7 + phase) + 1) * 0.5)
        if y < horizon - 10:
            pygame.draw.rect(surface, mix(bg_top, color, twinkle), (x, y, size, size))

    # ── Horizon silhouette (distant structures) ──
    _draw_horizon_silhouette(surface, theme, seed, now, horizon)

    # Ambient rising particles
    _draw_ambient_particles(surface, width, height, seed, now, horizon)

    # ── Ground with gradient depth ──
    glow_color = RETRO_PALETTE["accent_alt"] if not theme else mix(
        RETRO_PALETTE["accent_alt"], _theme_accent(theme, seed), 0.35)
    _draw_ground(surface, horizon, glow_color, rng)

    # Perspective grid on the ground
    grid_color = mix(RETRO_PALETTE["grid"], glow_color, rng.uniform(0.0, 0.08))
    _draw_perspective_grid(surface, grid_color, horizon)

    # Distance fog — fades grid into horizon, then horizon glow on top
    _draw_ground_fog(surface, horizon, glow_color)

    glow_rect = pygame.Rect(0, horizon - 14, width, 28)
    glow = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
    glow.fill((*glow_color, 12 + int(pulse(1.2) * 12)))
    surface.blit(glow, glow_rect)


def draw_boss_background(surface, boss, seed=None):
    width, height = surface.get_size()
    rng = random.Random(seed if seed else 42)
    top = mix(RETRO_PALETTE["bg_top"], boss.color, 0.10)
    bottom = mix(RETRO_PALETTE["panel_deep"], boss.accent, 0.16)
    _draw_gradient(surface, top, bottom)

    now = ui_time()
    horizon = int(height * 0.64)

    # Boss-specific celestial body
    _draw_celestial_body(surface, boss.theme, seed, now, top, horizon)

    # Seeded stars above horizon
    for (x, y, size, color, phase) in background_stars(width, height, seed):
        twinkle = 0.25 + 0.55 * ((math.sin(now * 1.7 + phase) + 1) * 0.5)
        if y < horizon - 10:
            pygame.draw.rect(surface, mix(top, color, twinkle), (x, y, size, size))

    center = (width // 2, int(height * 0.34))
    # Boss rings — draw directly, cap count and radius
    ring_count = 0
    for radius in range(90, width // 2, 140):
        if ring_count >= 5:
            break
        ring_count += 1
        alpha = 12 + int(pulse(1.2, ring_count) * 18)
        pygame.draw.circle(surface, (*boss.accent, alpha), center,
                           radius - int((now * 16 + ring_count * 9) % 24), 2)

    beam_seed = rng.randint(0, 100)
    for index in range(10):
        x = (index * 97 + beam_seed + int(now * 18)) % max(1, width)
        y = 108 + (index * 53 + beam_seed) % max(1, int(height * 0.42))
        beam_color = mix(boss.color, boss.accent, 0.55 if index % 2 else 0.25)
        pygame.draw.line(surface, (*beam_color,), (x, y), ((x + 80 + index * 7) % width, y + 48), 1)

    # Horizon silhouette + ambient
    _draw_horizon_silhouette(surface, boss.theme, seed, now, horizon)
    _draw_ambient_particles(surface, width, height, seed, now, horizon)

    # Ground with gradient + fog + arena darkening
    _draw_ground(surface, horizon, boss.accent, rng)
    _draw_perspective_grid(surface, mix(RETRO_PALETTE["grid"], boss.accent, 0.45), horizon)
    _draw_ground_fog(surface, horizon, boss.accent)

    # Boss arena dark overlay
    arena = pygame.Rect(0, horizon - 18, width, height - horizon + 18)
    overlay = pygame.Surface(arena.size, pygame.SRCALPHA)
    overlay.fill((*mix(RETRO_PALETTE["panel_deep"], boss.color, 0.18), 165))
    surface.blit(overlay, arena)

    # Horizon glow
    glow_rect = pygame.Rect(0, horizon - 18, width, 36)
    glow = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
    glow.fill((*boss.accent, 24 + int(pulse(1.6) * 18)))
    surface.blit(glow, glow_rect)


def _draw_ground(surface, horizon, accent, rng):
    """Draw the ground plane with a vertical gradient for depth."""
    width, height = surface.get_size()
    ground_h = height - horizon
    top_color = (10, 14, 18)
    bot_color = (5, 7, 10)
    top_color = mix(top_color, accent, 0.04)
    bot_color = mix(bot_color, accent, 0.03)
    block_h = max(1, ground_h // 16)
    for i in range(16):
        y_start = horizon + i * block_h
        y_end = min(height, horizon + (i + 1) * block_h)
        if y_start >= height:
            break
        t = ((y_start + y_end) / 2 - horizon) / max(1, ground_h)
        c = tuple(int(top_color[j] * (1 - t) + bot_color[j] * t) for j in range(3))
        pygame.draw.rect(surface, c, (0, y_start, width, y_end - y_start))


# Cache for pre-rendered perspective grids
_grid_cache = {}

def _draw_perspective_grid(surface, color, horizon):
    """Draw a perspective grid on the ground using cached pre-rendered pattern."""
    width, height = surface.get_size()
    ground_h = height - horizon
    cache_key = (width, ground_h, color)

    if cache_key not in _grid_cache:
        grid = pygame.Surface((width, ground_h), pygame.SRCALPHA)
        vx = width // 2
        num_vert = 16  # fewer lines
        for i in range(num_vert + 1):
            t = (i / num_vert - 0.5) * 2
            horizon_x = int(vx + t * width * 0.58)
            if horizon_x < 0 or horizon_x > width:
                continue
            bottom_x = int(vx + t * width * 1.15)
            bottom_x = max(-20, min(width + 20, bottom_x))
            for seg_y in range(0, ground_h, 8):
                t_y = seg_y / max(1, ground_h)
                alpha = int(8 + t_y * t_y * 50)
                seg_x = int(horizon_x + (bottom_x - horizon_x) * t_y)
                pygame.draw.line(grid, (*color, alpha),
                                 (seg_x, seg_y), (seg_x, min(seg_y + 8, ground_h)), 1)
        depth = 4
        step = 10
        while depth < ground_h:
            t = depth / max(1, ground_h)
            alpha = int(6 + t * t * 45)
            pygame.draw.line(grid, (*color, alpha), (0, depth), (width, depth), 1)
            depth += step
            step = min(step + 4, 52)
        _grid_cache[cache_key] = grid

    surface.blit(_grid_cache[cache_key], (0, horizon))


def _draw_ground_fog(surface, horizon, accent):
    """Distance fog overlay — fades ground into the horizon. Uses block fills."""
    width, height = surface.get_size()
    ground_h = height - horizon
    fog_height = min(ground_h, int(height * 0.18))
    fog = pygame.Surface((width, fog_height), pygame.SRCALPHA)
    # Block-based instead of per-pixel
    block_h = max(1, fog_height // 8)
    for i in range(8):
        y_start = i * block_h
        y_end = min(fog_height, (i + 1) * block_h)
        if y_start >= fog_height:
            break
        t = 1.0 - ((y_start + y_end) / 2 / max(1, fog_height))
        alpha = int(t * t * 95)
        pygame.draw.rect(fog, (*accent, alpha // 3), (0, y_start, width, y_end - y_start))
    surface.blit(fog, (0, horizon))


def background_stars(width, height, seed=None):
    """Generate seeded star positions for the background sky.
    Returns list of (x, y, size, color, phase) tuples.
    """
    horizon = int(height * 0.62)
    rng = random.Random(seed if seed else 42)
    stars = []
    for i in range(46):
        x = rng.randint(0, width - 1)
        y = rng.randint(0, max(1, horizon - 18))
        size = 1 if rng.random() > 0.18 else 2
        color_variant = rng.random()
        color = mix(RETRO_PALETTE["text_muted"], RETRO_PALETTE["accent_alt"],
                    0.2 if color_variant < 0.7 else 0.55)
        phase = rng.uniform(0, 6.28)
        stars.append((x, y, size, color, phase))
    return stars


# ── Celestial body types ──────────────────────────────────────────

# Theme → celestial body style (deterministic from theme name)
_CELESTIAL_STYLES = ["ring", "sphere", "crystal", "twin", "monolith"]


def _celestial_style(theme_name):
    """Map a theme name to a celestial body style, stable across runs."""
    idx = hash(theme_name) % len(_CELESTIAL_STYLES)
    return _CELESTIAL_STYLES[idx]


def _draw_celestial_body(surface, theme, seed, now, sky_color, horizon):
    """Draw a large theme-specific celestial object in the upper sky."""
    width = surface.get_width()
    rng = random.Random(hash(theme) ^ (seed or 0) * 13)
    style = _celestial_style(theme)

    # Position: upper portion, horizontally varied per seed
    cx = int(width * (0.25 + rng.uniform(0, 0.50)))
    cy = int(horizon * (0.28 + rng.uniform(0, 0.12)))
    radius = int(min(width, horizon) * (0.10 + rng.uniform(0, 0.05)))
    accent = _theme_accent(theme, seed)

    if style == "ring":
        _draw_ring_portal(surface, cx, cy, radius, accent, now)
    elif style == "sphere":
        _draw_energy_sphere(surface, cx, cy, radius, accent, sky_color, now)
    elif style == "crystal":
        _draw_crystal_body(surface, cx, cy, radius, accent, now)
    elif style == "twin":
        _draw_twin_orbs(surface, cx, cy, radius, accent, sky_color, now)
    else:  # monolith
        _draw_monolith(surface, cx, cy, radius, accent, sky_color, now)


def _draw_ring_portal(surface, cx, cy, radius, accent, now):
    """Glowing ring/portal — Neon Gate, Data Vault themes."""
    # Outer glow
    glow = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
    for i in range(5, 0, -1):
        alpha = 5 + i * 3
        r = int(radius * (0.6 + i * 0.08))
        pygame.draw.circle(glow, (*accent, alpha), (glow.get_width() // 2, glow.get_height() // 2), r, 1)
    surface.blit(glow, (cx - glow.get_width() // 2, cy - glow.get_height() // 2))

    # Main ring with animated arc
    ring_alpha = 45 + int(pulse(2.0, now) * 40)
    inner_r = int(radius * 0.55)
    outer_r = int(radius * 0.70)
    ring_surf = pygame.Surface((outer_r * 2 + 4, outer_r * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(ring_surf, (*accent, ring_alpha), (outer_r + 2, outer_r + 2), outer_r, 3)
    pygame.draw.circle(ring_surf, (*accent, ring_alpha // 2), (outer_r + 2, outer_r + 2), inner_r, 1)
    surface.blit(ring_surf, (cx - outer_r - 2, cy - outer_r - 2))

    # Central bright core
    core_r = max(3, radius // 6)
    core_alpha = 80 + int(pulse(2.5, 0.5) * 60)
    core = pygame.Surface((core_r * 4, core_r * 4), pygame.SRCALPHA)
    for i in range(3):
        a = core_alpha - i * 25
        pygame.draw.circle(core, (*accent, max(0, a)), (core_r * 2, core_r * 2), core_r + i * 3)
    surface.blit(core, (cx - core_r * 2, cy - core_r * 2))


def _draw_energy_sphere(surface, cx, cy, radius, accent, sky_color, now):
    """Pulsating energy sphere — Pulse Yard, Forge Ring themes."""
    pulse_r = int(radius * (0.85 + pulse(1.8, now) * 0.15))
    rng = random.Random(int(now * 100))

    # Soft outer halo
    halo = pygame.Surface((pulse_r * 3, pulse_r * 3), pygame.SRCALPHA)
    for i in range(8, 0, -1):
        r = int(pulse_r * (0.5 + i * 0.06))
        a = 3 + i * 4
        pygame.draw.circle(halo, (*accent, a), (halo.get_width() // 2, halo.get_height() // 2), r)
    surface.blit(halo, (cx - halo.get_width() // 2, cy - halo.get_height() // 2))

    # Sphere body with gradient shading
    sphere = pygame.Surface((pulse_r * 2 + 2, pulse_r * 2 + 2), pygame.SRCALPHA)
    sphere_alpha = 90 + int(pulse(2.2, 0.7) * 50)
    for j in range(pulse_r * 2):
        for i in range(pulse_r * 2):
            d = math.hypot(i - pulse_r, j - pulse_r)
            if d <= pulse_r:
                shade_factor = 0.6 + 0.4 * (1 - d / pulse_r)
                c = tuple(int(accent[k] * shade_factor) for k in range(3))
                alpha = int(sphere_alpha * (1 - d / pulse_r) * 0.5)
                sphere.set_at((i, j), (*c, alpha))
    surface.blit(sphere, (cx - pulse_r, cy - pulse_r))

    # Energy veins (small arcs)
    for i in range(3):
        angle = now * 0.4 + i * 2.09
        vx = cx + int(math.cos(angle) * pulse_r * 0.6)
        vy = cy + int(math.sin(angle) * pulse_r * 0.6)
        arc_rect = pygame.Rect(vx - 8, vy - 8, 16, 16)
        a = 30 + int(pulse(3.0, i) * 30)
        pygame.draw.arc(surface, (*accent, a), arc_rect, 0, math.pi * 1.5, 1)


def _draw_crystal_body(surface, cx, cy, radius, accent, now):
    """Crystal/prism formation — Prism Court theme."""
    points = []
    sides = 6
    rot = now * 0.15
    for i in range(sides):
        angle = rot + i * (2 * math.pi / sides)
        r = radius * (0.7 + pulse(2.0, i * 0.5) * 0.30)
        points.append((cx + int(math.cos(angle) * r), cy + int(math.sin(angle) * r)))

    # Glow
    if len(points) >= 3:
        glow = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
        scaled = [(x - cx + glow.get_width() // 2, y - cy + glow.get_height() // 2) for x, y in points]
        pygame.draw.polygon(glow, (*accent, 25), scaled)
        pygame.draw.polygon(glow, (*accent, 50), scaled, 2)
        surface.blit(glow, (cx - glow.get_width() // 2, cy - glow.get_height() // 2))

    # Inner lines connecting vertices
    for i in range(sides):
        j = (i + sides // 2) % sides
        a = 40 + int(pulse(1.5, i) * 25)
        pygame.draw.line(surface, (*accent, a), points[i], points[j], 1)

    # Central spark
    spark_r = max(2, radius // 10)
    spark_a = 100 + int(pulse(3.5) * 80)
    core = pygame.Surface((spark_r * 4, spark_r * 4), pygame.SRCALPHA)
    pygame.draw.circle(core, (*accent, spark_a), (spark_r * 2, spark_r * 2), spark_r)
    surface.blit(core, (cx - spark_r * 2, cy - spark_r * 2))


def _draw_twin_orbs(surface, cx, cy, radius, accent, sky_color, now):
    """Twin orbiting bodies — Sentinel Gate theme."""
    orbit_r = int(radius * 1.05)
    orb_r = int(radius * 0.30)
    for i in range(2):
        angle = now * 0.3 + i * math.pi
        ox = cx + int(math.cos(angle) * orbit_r)
        oy = cy + int(math.sin(angle) * orbit_r * 0.5)

        # Orb glow
        g = pygame.Surface((orb_r * 4, orb_r * 4), pygame.SRCALPHA)
        for j in range(5, 0, -1):
            r_glow = orb_r + j * 2
            a = 8 + j * 5
            pygame.draw.circle(g, (*accent, a), (orb_r * 2, orb_r * 2), r_glow)
        surface.blit(g, (ox - orb_r * 2, oy - orb_r * 2))

        # Orb body
        body_color = accent if i == 0 else mix(accent, sky_color, 0.4)
        pygame.draw.circle(surface, shade(body_color, -20), (ox + 1, oy + 1), orb_r)
        pygame.draw.circle(surface, body_color, (ox, oy), orb_r)
        pygame.draw.circle(surface, shade(body_color, 60), (ox - orb_r // 3, oy - orb_r // 3), max(2, orb_r // 2))


def _draw_monolith(surface, cx, cy, radius, accent, sky_color, now):
    """Geometric monolith/obelisk — Foundry, Data Vault themes."""
    # Tilted rectangular structure
    angle = now * 0.08
    w = int(radius * 1.2)
    h = int(radius * 2.0)

    # Pre-render on a surface with rotation
    mono = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
    mx, my = mono.get_width() // 2, mono.get_height() // 2

    # Main body
    body = pygame.Rect(mx - w // 2, my - h // 2, w, h)
    body_alpha = 40 + int(pulse(1.3) * 25)
    pygame.draw.rect(mono, (*accent, body_alpha), body, border_radius=4)
    pygame.draw.rect(mono, (*accent, body_alpha + 20), body, 1, border_radius=4)

    # Horizontal bands
    for b in range(3):
        by = my - h // 2 + (b + 1) * h // 4
        ba = 25 + int(pulse(2.0, b) * 20)
        pygame.draw.line(mono, (*accent, ba), (mx - w // 2 + 6, by), (mx + w // 2 - 6, by), 1)

    # Central glyph
    glyph_r = max(3, w // 8)
    glyph_a = 60 + int(pulse(2.5) * 40)
    pygame.draw.circle(mono, (*accent, glyph_a), (mx, my), glyph_r)
    pygame.draw.line(mono, (*accent, glyph_a), (mx - glyph_r * 2, my), (mx + glyph_r * 2, my), 1)

    # Rotate and place — use static position (transform.rotate is expensive)
    surface.blit(mono, (cx - mono.get_width() // 2, cy - mono.get_height() // 2))


# ── Horizon silhouette ────────────────────────────────────────────

_SILHOUETTE_PRESETS = ["towers", "domes", "spires", "blocks", "antennae"]


def _silhouette_preset(theme_name):
    """Map theme to a silhouette preset, stable across runs."""
    idx = hash(theme_name * 2) % len(_SILHOUETTE_PRESETS)
    return _SILHOUETTE_PRESETS[idx]


def _draw_horizon_silhouette(surface, theme, seed, now, horizon):
    """Draw a distant cityscape/silhouette at the horizon line."""
    width = surface.get_width()
    rng = random.Random(hash(theme) ^ (seed or 0) * 7)
    preset = _silhouette_preset(theme)
    accent = _theme_accent(theme, seed)

    # Dark silhouette color
    sil_color = (8, 10, 14)
    edge_color = mix(sil_color, accent, 0.12)

    if preset == "towers":
        _sil_towers(surface, width, horizon, rng, sil_color, edge_color, accent, now)
    elif preset == "domes":
        _sil_domes(surface, width, horizon, rng, sil_color, edge_color, accent, now)
    elif preset == "spires":
        _sil_spires(surface, width, horizon, rng, sil_color, edge_color, accent, now)
    elif preset == "blocks":
        _sil_blocks(surface, width, horizon, rng, sil_color, edge_color, accent, now)
    else:  # antennae
        _sil_antennae(surface, width, horizon, rng, sil_color, edge_color, accent, now)


def _sil_towers(surface, width, horizon, rng, color, edge, accent, now):
    """Tall vertical towers with varied heights."""
    count = rng.randint(3, 6)
    for i in range(count):
        x = width * (i + 1) // (count + 1) + rng.randint(-20, 20)
        h = rng.randint(30, 90)
        w = rng.randint(14, 32)
        rect = pygame.Rect(x - w // 2, horizon - h, w, h)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.line(surface, edge, (rect.x, rect.y), (rect.right, rect.y), 1)
        # Window dots
        for wy in range(rect.y + 8, horizon - 4, 10):
            dot_alpha = 12 + int(pulse(1.5, i + wy * 0.01) * 16)
            dot = pygame.Surface((3, 3), pygame.SRCALPHA)
            dot.fill((*accent, dot_alpha))
            surface.blit(dot, (rect.x + rng.randint(4, w - 6), wy))


def _sil_domes(surface, width, horizon, rng, color, edge, accent, now):
    """Rounded domes and curved structures."""
    count = rng.randint(3, 5)
    for i in range(count):
        x = width * (i + 1) // (count + 1) + rng.randint(-30, 30)
        base_w = rng.randint(30, 70)
        base_h = rng.randint(10, 25)
        dome_r = base_w // 2

        # Base
        base = pygame.Rect(x - base_w // 2, horizon - base_h, base_w, base_h)
        pygame.draw.rect(surface, color, base)
        pygame.draw.line(surface, edge, (base.x, base.y), (base.right, base.y), 1)

        # Dome
        dome_y = horizon - base_h - dome_r + rng.randint(0, 8)
        pygame.draw.ellipse(surface, color, (x - dome_r, dome_y, dome_r * 2, dome_r * 2))
        a = 20 + int(pulse(1.6, i) * 15)
        pygame.draw.arc(surface, (*accent, a),
                        (x - dome_r + 2, dome_y + 2, dome_r * 2 - 4, dome_r * 2 - 4),
                        math.pi, 2 * math.pi, 1)


def _sil_spires(surface, width, horizon, rng, color, edge, accent, now):
    """Sharp triangular spires."""
    count = rng.randint(4, 7)
    for i in range(count):
        x = width * (i + 1) // (count + 1) + rng.randint(-25, 25)
        h = rng.randint(40, 100)
        half_w = rng.randint(8, 18)
        points = [(x, horizon - h), (x - half_w, horizon), (x + half_w, horizon)]
        pygame.draw.polygon(surface, color, points)
        # Edge highlight
        pygame.draw.line(surface, edge, (x, horizon - h), (x - half_w, horizon), 1)
        # Peak glow
        peak_a = 15 + int(pulse(2.0, i * 0.3) * 20)
        peak = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(peak, (*accent, peak_a), (4, 4), 3)
        surface.blit(peak, (x - 4, horizon - h - 4))


def _sil_blocks(surface, width, horizon, rng, color, edge, accent, now):
    """Heavy industrial block structures."""
    count = rng.randint(2, 4)
    for i in range(count):
        x = width * (i + 1) // (count + 1) + rng.randint(-40, 40)
        w = rng.randint(40, 100)
        h = rng.randint(20, 50)
        rect = pygame.Rect(x - w // 2, horizon - h, w, h)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.line(surface, edge, (rect.x, rect.y), (rect.right, rect.y), 1)
        # Stack smaller blocks on top
        for j in range(rng.randint(0, 2)):
            sw = rng.randint(w // 3, w // 2)
            sh = rng.randint(8, 18)
            sx = x + rng.randint(-w // 3, w // 3)
            srect = pygame.Rect(sx - sw // 2, horizon - h - sh - j * 14, sw, sh)
            pygame.draw.rect(surface, color, srect)
            pygame.draw.line(surface, edge, (srect.x, srect.y), (srect.right, srect.y), 1)


def _sil_antennae(surface, width, horizon, rng, color, edge, accent, now):
    """Thin antenna masts with signal lights."""
    count = rng.randint(5, 8)
    for i in range(count):
        x = width * (i + 1) // (count + 1) + rng.randint(-15, 15)
        h = rng.randint(25, 75)
        # Vertical mast
        pygame.draw.line(surface, color, (x, horizon), (x, horizon - h), 2)
        # Cross bars
        for j in range(rng.randint(1, 3)):
            bar_y = horizon - h + rng.randint(5, h - 5)
            bar_w = rng.randint(6, 14)
            pygame.draw.line(surface, color, (x - bar_w, bar_y), (x + bar_w, bar_y), 1)
            # Signal light
            light_a = 30 + int(pulse(2.0, i * 0.7) * 50)
            light = pygame.Surface((5, 5), pygame.SRCALPHA)
            light.fill((*accent, light_a))
            surface.blit(light, (x - bar_w - 3, bar_y - 2))
            surface.blit(light, (x + bar_w - 2, bar_y - 2))


def _theme_tint(theme_name, seed=None):
    """Derive a subtle RGB tint from the theme name, stable per run."""
    rng = random.Random(hash(theme_name) ^ (seed or 0))
    return (
        rng.randint(-12, 12),
        rng.randint(-12, 12),
        rng.randint(-8, 8),
    )


def _theme_accent(theme_name, seed=None):
    """Derive a subtle accent color from the theme name."""
    rng = random.Random(hash(theme_name) ^ (seed or 0) * 3)
    base = RETRO_PALETTE["accent_alt"]
    return tuple(max(0, min(255, base[i] + rng.randint(-20, 20))) for i in range(3))


def _draw_ambient_particles(surface, width, height, seed, now, horizon=None):
    """Draw subtle rising dust motes above and below the horizon."""
    rng = random.Random((seed or 42) * 7907)
    if horizon is None:
        horizon = int(height * 0.62)
    for i in range(22):
        x = (rng.randint(0, width) + int(now * 7 + i * 43)) % width
        # Particles both above and below horizon for depth
        zone = rng.randint(0, 2)
        if zone == 0:
            base_y = horizon - rng.randint(10, int(height * 0.25))
        else:
            base_y = horizon + rng.randint(5, int(height * 0.30))
        y = int(base_y - (now * 12 + i * 59) % (height * 0.40))
        alpha = 8 + int(16 * abs(math.sin(now * 0.6 + i * 1.3)))
        if alpha < 5:
            continue
        size = 1 if rng.random() > 0.25 else 2
        color = RETRO_PALETTE["text_muted"]
        s = pygame.Surface((size + 2, size + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, alpha), (size // 2 + 1, size // 2 + 1), size // 2)
        surface.blit(s, (x, y))


def draw_panel(surface, rect, title=None, accent=None, fill=None):
    accent = accent or RETRO_PALETTE["accent_alt"]
    fill = fill or RETRO_PALETTE["panel"]
    shadow = rect.move(5, 6)
    pygame.draw.rect(surface, (0, 0, 0), shadow, border_radius=6)
    pygame.draw.rect(surface, shade(fill, -8), rect, border_radius=6)
    inner = rect.inflate(-2, -2)
    if inner.width > 0 and inner.height > 0:
        pygame.draw.rect(surface, fill, inner, border_radius=5)
        shine = pygame.Rect(inner.x + 2, inner.y + 3, max(0, inner.width - 4), max(1, inner.height // 4))
        shine_surface = pygame.Surface(shine.size, pygame.SRCALPHA)
        shine_surface.fill((*shade(fill, 22), 28))
        surface.blit(shine_surface, shine)
    pygame.draw.rect(surface, RETRO_PALETTE["line"], rect, 1, border_radius=6)
    pygame.draw.line(surface, accent, rect.topleft, rect.topright, 3)
    pygame.draw.line(surface, shade(accent, -40), rect.bottomleft, rect.bottomright, 1)
    draw_corner_brackets(surface, rect, shade(accent, 18), length=16, width=2, inset=5)
    if title:
        draw_text(surface, title, RETRO_PALETTE["text_white"], rect.x + 18, rect.y + 14, 20, True)


def draw_chip(surface, rect, label, value=None, accent=None, active=False):
    accent = accent or RETRO_PALETTE["accent_alt"]
    if active:
        draw_soft_glow(surface, rect, accent, alpha=18 + int(pulse(2.6) * 16), spread=5, radius=5)
    pygame.draw.rect(surface, shade(RETRO_PALETTE["panel_soft"], -8), rect, border_radius=4)
    pygame.draw.rect(surface, RETRO_PALETTE["panel_soft"], rect.inflate(-2, -2), border_radius=3)
    pygame.draw.line(surface, shade(accent, 35), rect.topleft, rect.topright, 2)
    pygame.draw.rect(surface, accent, rect, 1, border_radius=4)
    draw_text(surface, label.upper(), RETRO_PALETTE["text_muted"], rect.x + 10, rect.y + 7, 12, True, shadow=False)
    if value is not None:
        draw_text(surface, value, RETRO_PALETTE["text_white"], rect.x + 10, rect.y + 24, 18, True, shadow=False)


def draw_bar(surface, rect, current, maximum, fill_color, back_color=None):
    back_color = back_color or RETRO_PALETTE["panel_deep"]
    pygame.draw.rect(surface, back_color, rect, border_radius=3)
    if maximum > 0:
        width = int(rect.width * max(0, min(1, current / maximum)))
        if width > 0:
            fill_rect = pygame.Rect(rect.x, rect.y, width, rect.height)
            pygame.draw.rect(surface, shade(fill_color, -20), fill_rect, border_radius=3)
            pygame.draw.rect(surface, fill_color, fill_rect.inflate(-1, -2), border_radius=2)
    pygame.draw.rect(surface, RETRO_PALETTE["line"], rect, 1, border_radius=3)


def draw_modal(surface, title, subtitle=None, accent=None, extra=None):
    width, height = surface.get_size()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 145))
    surface.blit(overlay, (0, 0))

    rect = pygame.Rect(0, 0, min(560, width - 80), 210)
    rect.center = (width // 2, height // 2)
    accent = accent or RETRO_PALETTE["accent"]
    for offset, alpha in ((18, 24), (10, 36)):
        glow = pygame.Surface((rect.width + offset * 2, rect.height + offset * 2), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*accent, alpha), glow.get_rect(), border_radius=10)
        surface.blit(glow, (rect.x - offset, rect.y - offset))
    draw_panel(surface, rect, accent=accent)
    draw_glow_text(surface, title, RETRO_PALETTE["text_white"], rect.centerx, rect.y + 58, 34, True, center=True, glow_color=accent)
    if subtitle:
        draw_text(surface, subtitle, RETRO_PALETTE["text"], rect.centerx, rect.y + 110, 16, False, center=True)
    if extra:
        draw_text(surface, extra, RETRO_PALETTE["text_muted"], rect.centerx, rect.y + 140, 14, False, center=True)
