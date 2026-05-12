"""Extracted screen rendering functions to reduce engine.py size.

Each function receives (screen, engine) so it can access game state
without being a method on GameEngine.
"""
import pygame

from game.assets import draw_ball_sprite, draw_boss_sprite, draw_brick_sprite, draw_paddle_sprite, draw_skill_icon, mix, shade
from game.entities.brick import BRICK_KIND_INFO, BrickGrid
from game.input import ACTIONS
import game.roguelite.effects as effects_module
from game.skill_descriptions import get_description, HIGH_SCORE_LIMIT
from game.roguelite.skill import SkillType, SKILL_GUIDE, SKILL_META, skill_synergy, skill_upgrade_hint
from game.ui import (
    draw_arcade_button,
    draw_bar,
    draw_chip,
    draw_corner_brackets,
    draw_glow_text,
    draw_modal,
    draw_panel,
    draw_soft_glow,
    draw_text,
    draw_wrapped_text,
    pulse,
    RETRO_PALETTE,
)


def draw_game_over(screen, engine):
    skills_key = engine.keybindings.action_label("skills").split(" / ")[0]
    draw_modal(screen, "GAME OVER", f"ESC restart  |  H scores  |  {skills_key} skills", RETRO_PALETTE["danger"])
    center_x = engine.width // 2
    draw_glow_text(screen, f"BEST LEVEL {engine.max_level_reached}", RETRO_PALETTE["accent"], center_x, engine.height // 2 + 44, 18, True, center=True, glow_color=RETRO_PALETTE["accent"])
    draw_text(screen, f"SCORE {engine.score}", RETRO_PALETTE["text"], center_x, engine.height // 2 + 72, 16, True, center=True, shadow=False)


def draw_pause(screen, engine):
    skills_key = engine.keybindings.action_label("skills").split(" / ")[0]
    controls_key = engine.keybindings.action_label("controls").split(" / ")[0]
    settings_key = engine.keybindings.action_label("settings").split(" / ")[0]
    draw_modal(screen, "PAUSED",
               f"ESC resume  |  F5 save  |  {skills_key} skills",
               RETRO_PALETTE["accent_alt"],
               extra=f"{controls_key} controls  |  {settings_key} settings")


def draw_high_scores(screen, engine):
    panel = pygame.Rect(0, 0, min(620, engine.width - 90), min(520, engine.height - 120))
    panel.center = (engine.width // 2, engine.height // 2)
    draw_panel(screen, panel, accent=RETRO_PALETTE["accent"], fill=(15, 20, 27))
    draw_glow_text(screen, "HIGH SCORES", RETRO_PALETTE["text_white"], panel.centerx, panel.y + 44, 32, True, center=True, glow_color=RETRO_PALETTE["accent"])
    draw_text(screen, "Ranked by level first, score second", RETRO_PALETTE["text_muted"], panel.centerx, panel.y + 82, 14, False, center=True, shadow=False)
    stats_line = f"Runs {engine.stats.get('runs_finished', 0)}  |  Bricks {engine.stats.get('bricks_broken', 0)}  |  Best {engine.stats.get('best_level', 1)}"
    draw_text(screen, stats_line, RETRO_PALETTE["text"], panel.centerx, panel.y + 104, 13, True, center=True, shadow=False)

    y = panel.y + 136
    if not engine.high_scores:
        draw_text(screen, "No completed runs yet", RETRO_PALETTE["text"], panel.centerx, y + 44, 18, False, center=True)
    for index, entry in enumerate(engine.high_scores[:HIGH_SCORE_LIMIT], start=1):
        rank_rect = pygame.Rect(panel.x + 44, y, panel.width - 88, 34)
        row_fill = mix(RETRO_PALETTE["panel_soft"], RETRO_PALETTE["accent"], 0.08 if index == 1 else 0.0)
        pygame.draw.rect(screen, row_fill, rank_rect, border_radius=4)
        pygame.draw.rect(screen, RETRO_PALETTE["accent"] if index == 1 else RETRO_PALETTE["line"], rank_rect, 1, border_radius=4)
        if index == 1:
            pygame.draw.line(screen, shade(RETRO_PALETTE["accent"], 30), (rank_rect.x + 8, rank_rect.y + 3), (rank_rect.right - 8, rank_rect.y + 3), 1)
        draw_text(screen, f"{index:02}", RETRO_PALETTE["accent"], rank_rect.x + 12, rank_rect.y + 8, 14, True, shadow=False)
        draw_text(screen, f"Level {entry['level']}", RETRO_PALETTE["text_white"], rank_rect.x + 70, rank_rect.y + 8, 14, True, shadow=False)
        draw_text(screen, f"Score {entry['score']}", RETRO_PALETTE["text"], rank_rect.x + 190, rank_rect.y + 8, 14, True, shadow=False)
        draw_text(screen, f"Skills {entry['skills']}", RETRO_PALETTE["text_muted"], rank_rect.right - 112, rank_rect.y + 8, 14, True, shadow=False)
        y += 42

    footer_rect = pygame.Rect(panel.x + 120, panel.bottom - 72, panel.width - 240, 24)
    if footer_rect.width > 120:
        pygame.draw.rect(screen, RETRO_PALETTE["panel_soft"], footer_rect, border_radius=4)
        pygame.draw.rect(screen, RETRO_PALETTE["line"], footer_rect, 1, border_radius=4)
        draw_text(screen, "LEVEL DEPTH OUTRANKS RAW SCORE", RETRO_PALETTE["text_muted"], footer_rect.centerx, footer_rect.y + 13, 11, True, center=True, shadow=False)
    draw_text(screen, "ENTER or ESC returns", RETRO_PALETTE["text_muted"], panel.centerx, panel.bottom - 36, 14, False, center=True, shadow=False)


def draw_skill_guide(screen, engine):
    panel = engine.skill_guide_panel_rect()
    draw_panel(screen, panel, accent=RETRO_PALETTE["accent_alt"], fill=(15, 20, 27))
    draw_glow_text(screen, "SKILL GUIDE", RETRO_PALETTE["text_white"], panel.centerx, panel.y + 42, 32, True, center=True, glow_color=RETRO_PALETTE["accent_alt"])
    draw_text(screen, "Browse effects, upgrades, controls, and build pairings", RETRO_PALETTE["text_muted"], panel.centerx, panel.y + 78, 13, False, center=True, shadow=False)

    left = pygame.Rect(panel.x + 34, panel.y + 100, 226, panel.height - 152)
    detail = pygame.Rect(left.right + 24, left.y, panel.right - left.right - 58, left.height)
    pygame.draw.rect(screen, RETRO_PALETTE["panel_deep"], left, border_radius=5)
    pygame.draw.rect(screen, RETRO_PALETTE["line"], left, 1, border_radius=5)
    pygame.draw.rect(screen, RETRO_PALETTE["panel_deep"], detail, border_radius=5)
    pygame.draw.rect(screen, RETRO_PALETTE["line"], detail, 1, border_radius=5)

    for index, row in engine.skill_guide_rows():
        skill_type = engine.full_skill_pool[index]
        code, accent, _tagline = SKILL_META.get(skill_type, ("UP", RETRO_PALETTE["accent_alt"], "Upgrade"))
        selected = index == engine.skill_guide_index
        fill = mix(RETRO_PALETTE["panel_soft"], accent, 0.18 if selected else 0.04)
        pygame.draw.rect(screen, fill, row, border_radius=4)
        pygame.draw.rect(screen, accent if selected else RETRO_PALETTE["line"], row, 1, border_radius=4)
        draw_skill_icon(screen, pygame.Rect(row.x + 5, row.y + 4, 20, 20), code, accent)
        draw_text(screen, get_description(skill_type, 1).split(" (")[0], RETRO_PALETTE["text_white"] if selected else RETRO_PALETTE["text"], row.x + 34, row.y + 8, 12, True, shadow=False)

    if engine.skill_guide_scroll > 0:
        draw_text(screen, "^", RETRO_PALETTE["text_muted"], left.centerx, left.y - 12, 14, True, center=True, shadow=False)
    if engine.skill_guide_scroll + engine.skill_guide_visible_count() < len(engine.full_skill_pool):
        draw_text(screen, "v", RETRO_PALETTE["text_muted"], left.centerx, left.bottom + 4, 14, True, center=True, shadow=False)

    skill_type = engine.full_skill_pool[engine.skill_guide_index]
    code, accent, tagline = SKILL_META.get(skill_type, ("UP", RETRO_PALETTE["accent_alt"], "Upgrade"))
    guide = SKILL_GUIDE.get(skill_type, {})
    icon_rect = pygame.Rect(detail.x + 24, detail.y + 24, 58, 58)
    draw_skill_icon(screen, icon_rect, code, accent)
    draw_glow_text(screen, get_description(skill_type, 1).split(" (")[0].upper(), RETRO_PALETTE["text_white"], icon_rect.right + 18, detail.y + 24, 24, True, glow_color=accent)
    draw_text(screen, tagline, RETRO_PALETTE["text_muted"], icon_rect.right + 20, detail.y + 56, 14, False, shadow=False)

    sections = [
        ("EFFECT", guide.get("effect", "Improves this run.")),
        ("HOW TO USE", engine.skill_usage_text(skill_type, guide)),
        ("UPGRADES", guide.get("scales", skill_upgrade_hint(skill_type))),
        ("SYNERGY", skill_synergy(skill_type)),
    ]
    y = detail.y + 104
    for label, body in sections:
        section = pygame.Rect(detail.x + 24, y, detail.width - 48, 66)
        pygame.draw.rect(screen, mix(RETRO_PALETTE["panel_soft"], accent, 0.07), section, border_radius=4)
        pygame.draw.rect(screen, RETRO_PALETTE["line"], section, 1, border_radius=4)
        draw_text(screen, label, accent, section.x + 12, section.y + 9, 11, True, shadow=False)
        draw_wrapped_text(screen, body, RETRO_PALETTE["text"], pygame.Rect(section.x + 12, section.y + 28, section.width - 24, section.height - 34), 13, 2)
        y += 76

    up_key = engine.keybindings.action_label("up").split(" / ")[0]
    down_key = engine.keybindings.action_label("down").split(" / ")[0]
    back_key = engine.keybindings.action_label("back").split(" / ")[0]
    draw_text(screen, f"{up_key}/{down_key} browse  |  click skill  |  {back_key} returns", RETRO_PALETTE["text_muted"], panel.centerx, panel.bottom - 34, 13, False, center=True, shadow=False)


def draw_controls_screen(screen, engine):
    panel = pygame.Rect(0, 0, min(680, engine.width - 70), min(620, engine.height - 80))
    panel.center = (engine.width // 2, engine.height // 2)
    draw_panel(screen, panel, accent=RETRO_PALETTE["accent_alt"], fill=(15, 20, 27))
    draw_glow_text(screen, "CONTROLS", RETRO_PALETTE["text_white"], panel.centerx, panel.y + 42, 32, True, center=True, glow_color=RETRO_PALETTE["accent_alt"])
    draw_text(screen, "Click a key slot or select with arrows/WASD, ENTER to rebind", RETRO_PALETTE["text_muted"], panel.centerx, panel.y + 78, 13, False, center=True, shadow=False)

    for index, (action, label) in enumerate(ACTIONS):
        row = engine.controls_row_rect(index)
        selected = index == engine.controls_index
        accent = RETRO_PALETTE["accent"] if selected else RETRO_PALETTE["line"]
        fill = mix(RETRO_PALETTE["panel_soft"], RETRO_PALETTE["accent_alt"], 0.08 if selected else 0.0)
        if selected:
            draw_soft_glow(screen, row, RETRO_PALETTE["accent_alt"], alpha=22, spread=5, radius=5)
        pygame.draw.rect(screen, fill, row, border_radius=4)
        pygame.draw.rect(screen, accent, row, 1, border_radius=4)
        draw_text(screen, label.upper(), RETRO_PALETTE["text_white"] if selected else RETRO_PALETTE["text"], row.x + 12, row.y + 10, 13, True, shadow=False)

        keys = engine.keybindings.bindings.get(action, [])
        for slot in range(2):
            key_rect = pygame.Rect(row.right - 184 + slot * 88, row.y + 6, 76, 24)
            slot_selected = selected and slot == engine.controls_slot
            key_fill = RETRO_PALETTE["accent_alt"] if slot_selected else RETRO_PALETTE["panel_deep"]
            text_color = (8, 12, 16) if slot_selected else RETRO_PALETTE["text"]
            pygame.draw.rect(screen, key_fill, key_rect, border_radius=4)
            pygame.draw.rect(screen, RETRO_PALETTE["accent_alt"] if slot_selected else RETRO_PALETTE["line"], key_rect, 1, border_radius=4)
            key_name = engine.keybindings.key_name(keys[slot]) if slot < len(keys) else "-"
            draw_text(screen, key_name, text_color, key_rect.centerx, key_rect.centery, 11, True, center=True, shadow=False)

    footer_y = panel.bottom - 44
    if engine.binding_capture:
        action, slot = engine.binding_capture
        action_label = dict(ACTIONS)[action]
        draw_text(screen, f"Press a key for {action_label} slot {slot + 1}  |  ESC cancels", RETRO_PALETTE["accent"], panel.centerx, footer_y, 14, True, center=True, shadow=False)
    elif engine.last_binding_message:
        draw_text(screen, engine.last_binding_message, RETRO_PALETTE["accent"], panel.centerx, footer_y, 14, True, center=True, shadow=False)
    else:
        draw_text(screen, "R reset defaults  |  ESC returns", RETRO_PALETTE["text_muted"], panel.centerx, footer_y, 14, False, center=True, shadow=False)


def draw_settings_screen(screen, engine):
    panel = pygame.Rect(0, 0, min(560, engine.width - 90), min(380, engine.height - 120))
    panel.center = (engine.width // 2, engine.height // 2)
    draw_panel(screen, panel, accent=RETRO_PALETTE["accent"], fill=(15, 20, 27))
    draw_glow_text(screen, "SETTINGS", RETRO_PALETTE["text_white"], panel.centerx, panel.y + 48, 32, True, center=True, glow_color=RETRO_PALETTE["accent"])
    draw_text(screen, "Audio settings are saved locally", RETRO_PALETTE["text_muted"], panel.centerx, panel.y + 84, 13, False, center=True, shadow=False)

    mute_rect, volume_rect = engine.settings_option_rects()
    muted = bool(engine.settings.get("muted", False))
    volume = float(engine.settings.get("sound_volume", 0.45))
    options = [
        (mute_rect, "Mute", "ON" if muted else "OFF", 0),
        (volume_rect, "Sound Volume", f"{int(volume * 100)}%", 1),
    ]
    for rect, label, value, index in options:
        selected = index == engine.settings_index
        accent = RETRO_PALETTE["accent"] if selected else RETRO_PALETTE["line"]
        fill = mix(RETRO_PALETTE["panel_soft"], RETRO_PALETTE["accent"], 0.08 if selected else 0.0)
        if selected:
            draw_soft_glow(screen, rect, RETRO_PALETTE["accent"], alpha=20, spread=5, radius=5)
        pygame.draw.rect(screen, fill, rect, border_radius=5)
        pygame.draw.rect(screen, accent, rect, 1, border_radius=5)
        draw_text(screen, label.upper(), RETRO_PALETTE["text_white"], rect.x + 14, rect.y + 15, 13, True, shadow=False)
        draw_text(screen, value, RETRO_PALETTE["text"], rect.right - 86, rect.y + 14, 14, True, shadow=False)
        if index == 1:
            bar = pygame.Rect(rect.x + 170, rect.y + 18, max(80, rect.width - 270), 10)
            draw_bar(screen, bar, volume, 1, RETRO_PALETTE["accent"])

    draw_text(screen, "LEFT/RIGHT adjust  |  ENTER toggles  |  ESC returns", RETRO_PALETTE["text_muted"], panel.centerx, panel.bottom - 42, 13, False, center=True, shadow=False)


def draw_title(screen, engine):
    panel = pygame.Rect(0, 0, min(720, engine.width - 80), min(340, max(300, engine.height - 190)))
    panel.center = (engine.width // 2, int(engine.height * 0.45))
    draw_soft_glow(screen, panel, RETRO_PALETTE["accent"], alpha=18 + int(pulse(1.4) * 14), spread=16, radius=10)
    draw_panel(screen, panel, accent=RETRO_PALETTE["accent"], fill=(15, 20, 27))
    draw_title_preview(screen, engine, panel)
    draw_glow_text(screen, "ARKANOID", RETRO_PALETTE["text_white"], panel.centerx, panel.y + 74, 54, True, center=True, glow_color=RETRO_PALETTE["accent"])
    subtitle_rect = pygame.Rect(0, 0, 246, 36)
    subtitle_rect.center = (panel.centerx, panel.y + 126)
    pygame.draw.rect(screen, mix(RETRO_PALETTE["panel_deep"], RETRO_PALETTE["accent_alt"], 0.14), subtitle_rect, border_radius=4)
    pygame.draw.rect(screen, RETRO_PALETTE["accent_alt"], subtitle_rect, 1, border_radius=4)
    draw_text(screen, "ROGUELITE", RETRO_PALETTE["accent_alt"], panel.centerx, panel.y + 126, 30, True, center=True)
    draw_text(screen, "Break bricks. Choose upgrades. Survive the run.", RETRO_PALETTE["text"], panel.centerx, panel.y + 226, 17, False, center=True)

    start_rect = pygame.Rect(0, 0, 260, 52)
    start_rect.center = (panel.centerx, panel.y + 278)
    draw_arcade_button(screen, start_rect, "PRESS ENTER", RETRO_PALETTE["accent"], phase=0.4)

    resume_key = engine.keybindings.action_label("resume").split(" / ")[0]
    scores_key = engine.keybindings.action_label("scores").split(" / ")[0]
    skills_key = engine.keybindings.action_label("skills").split(" / ")[0]
    controls_key = engine.keybindings.action_label("controls").split(" / ")[0]
    settings_key = engine.keybindings.action_label("settings").split(" / ")[0]
    back_key = engine.keybindings.action_label("back").split(" / ")[0]
    continue_text = f"{resume_key} resume  |  " if engine.save_path.exists() else ""
    draw_text(screen, f"{continue_text}{scores_key} scores  |  {skills_key} skills  |  {controls_key} controls  |  {settings_key} settings  |  {back_key} quits", RETRO_PALETTE["text_muted"], panel.centerx, panel.bottom + 28, 14, False, center=True, shadow=False)
    if engine.last_save_message:
        draw_text(screen, engine.last_save_message, RETRO_PALETTE["text"], panel.centerx, panel.bottom + 54, 13, False, center=True, shadow=False)


def draw_title_preview(screen, engine, panel):
    brick_colors = [
        RETRO_PALETTE["brick1"],
        RETRO_PALETTE["brick2"],
        RETRO_PALETTE["brick3"],
        RETRO_PALETTE["brick4"],
        RETRO_PALETTE["accent_alt"],
    ]
    preview = pygame.Rect(0, 0, min(470, panel.width - 92), 72)
    preview.center = (panel.centerx, panel.y + 170)
    pygame.draw.rect(screen, mix(RETRO_PALETTE["panel_deep"], RETRO_PALETTE["accent_alt"], 0.08), preview, border_radius=5)
    pygame.draw.rect(screen, RETRO_PALETTE["line"], preview, 1, border_radius=5)
    draw_corner_brackets(screen, preview, RETRO_PALETTE["accent_alt"], length=12, width=1, inset=5)
    for row in range(2):
        for col in range(8):
            color = brick_colors[(col + row * 2) % len(brick_colors)]
            brick = pygame.Rect(preview.x + 24 + col * 52, preview.y + 12 + row * 18, 38, 10)
            pygame.draw.rect(screen, mix(color, RETRO_PALETTE["text_white"], 0.12), brick, border_radius=2)
            pygame.draw.line(screen, mix(color, RETRO_PALETTE["text_white"], 0.45), brick.topleft, brick.topright, 1)
            pygame.draw.line(screen, mix(color, (0, 0, 0), 0.55), brick.bottomleft, brick.bottomright, 1)

    motion = int((pulse(1.15, 0.7) - 0.5) * 44)
    ball = pygame.Rect(0, 0, 14, 14)
    ball.center = (preview.centerx - 12 + motion, preview.bottom - 20)
    draw_ball_sprite(screen, ball, RETRO_PALETTE["ball"])
    paddle = pygame.Rect(0, 0, 92, 11)
    paddle.center = (preview.centerx + 42 + motion // 3, preview.bottom - 13)
    draw_paddle_sprite(screen, paddle, RETRO_PALETTE["paddle"])


def draw_hud(screen, engine):
    top = pygame.Rect(18, 16, engine.width - 36, 74)
    draw_panel(screen, top, accent=RETRO_PALETTE["accent_alt"], fill=(16, 20, 26))

    logo_rect = pygame.Rect(top.x + 18, top.y + 14, 7, 42)
    pygame.draw.rect(screen, RETRO_PALETTE["accent"], logo_rect, border_radius=2)
    pygame.draw.rect(screen, RETRO_PALETTE["accent_alt"], logo_rect.move(10, 0), border_radius=2)
    draw_glow_text(screen, "ARKANOID ROGUELITE", RETRO_PALETTE["text_white"], top.x + 40, top.y + 14, 20, True, glow_color=RETRO_PALETTE["accent_alt"])
    theme = getattr(engine.brick_grid, "theme_name", "BREAKOUT RUN")
    draw_text(screen, theme.upper(), RETRO_PALETTE["text_muted"], top.x + 42, top.y + 42, 12, True, shadow=False)
    if engine.last_save_message:
        draw_text(screen, engine.last_save_message, RETRO_PALETTE["text_muted"], top.x + 250, top.y + 44, 12, True, shadow=False)

    chip_y = top.y + 12
    chip_w = 92
    right_x = top.right - 18 - (chip_w * 5) - 32
    draw_chip(screen, pygame.Rect(right_x, chip_y, chip_w, 48), "Level", str(engine.level), RETRO_PALETTE["accent"], active=True)
    draw_chip(screen, pygame.Rect(right_x + 100, chip_y, chip_w, 48), "Score", str(engine.score), RETRO_PALETTE["accent_alt"], active=engine.score > 0)
    draw_chip(screen, pygame.Rect(right_x + 200, chip_y, chip_w, 48), "Lives", str(engine.paddle.lives), RETRO_PALETTE["paddle"])
    draw_chip(screen, pygame.Rect(right_x + 300, chip_y, chip_w, 48), "Balls", str(len(engine.balls)), RETRO_PALETTE["ball"])
    draw_chip(screen, pygame.Rect(right_x + 400, chip_y, chip_w, 48), "Energy", str(engine.run_state.energy), RETRO_PALETTE["brick2"], active=engine.run_state.energy > 0)

    if engine.selected_skills:
        panel_width = max(360, min(engine.width - 274, 740))
        panel = pygame.Rect(18, 102, panel_width, 42)
        pygame.draw.rect(screen, (16, 20, 26), panel, border_radius=5)
        pygame.draw.rect(screen, RETRO_PALETTE["line"], panel, 1, border_radius=5)
        pygame.draw.line(screen, RETRO_PALETTE["accent_alt"], panel.topleft, panel.topright, 1)
        x = panel.x + 10
        for skill in engine.selected_skills[-4:]:
            label = f"{skill.type.value} {skill.level}"
            width = min(126, max(88, len(label) * 8 + 36))
            if x + width > panel.right - 10:
                break
            rect = pygame.Rect(x, panel.y + 7, width, 28)
            code, accent, _ = SKILL_META.get(skill.type, ("UP", RETRO_PALETTE["accent_alt"], "Upgrade"))
            pygame.draw.rect(screen, RETRO_PALETTE["panel_soft"], rect, border_radius=4)
            pygame.draw.rect(screen, accent, rect, 1, border_radius=4)
            draw_skill_icon(screen, pygame.Rect(rect.x + 5, rect.y + 4, 20, 20), code, accent)
            draw_text(screen, label, RETRO_PALETTE["text"], rect.x + 31, rect.y + 7, 11, True, shadow=False)
            x += width + 8

        active_prompts = []
        if effects_module.skill_count(engine.selected_skills, SkillType.CANNON):
            status = "READY" if engine.cannon_cooldown <= 0 else f"{engine.cannon_cooldown:.1f}s"
            active_prompts.append((f"{engine.keybindings.action_label('up').split(' / ')[0]} Cannon {status}", RETRO_PALETTE["brick1"]))
        if effects_module.skill_count(engine.selected_skills, SkillType.GRAVITY_WELL):
            active_prompts.append((f"{engine.keybindings.action_label('down').split(' / ')[0]} Well", RETRO_PALETTE["accent_alt"]))
        for label, accent in active_prompts:
            width = min(130, max(86, len(label) * 7))
            if x + width > panel.right - 10:
                break
            rect = pygame.Rect(x, panel.y + 7, width, 28)
            pygame.draw.rect(screen, mix(RETRO_PALETTE["panel_deep"], accent, 0.12), rect, border_radius=4)
            pygame.draw.rect(screen, accent, rect, 1, border_radius=4)
            draw_text(screen, label, RETRO_PALETTE["text"], rect.x + 8, rect.y + 7, 10, True, shadow=False)
            x += width + 8

    energy_rect = pygame.Rect(engine.width - 238, 104, 220, 13)
    if engine.run_state.energy > 0:
        draw_soft_glow(screen, energy_rect, RETRO_PALETTE["brick2"], alpha=16 + int(pulse(2.4) * 16), spread=4, radius=4)
    draw_bar(screen, energy_rect, min(engine.run_state.energy, 10), 10, RETRO_PALETTE["brick2"])
    draw_text(screen, "VAMPIRE CHARGE", RETRO_PALETTE["text_muted"], energy_rect.x, energy_rect.y + 17, 11, True, shadow=False)
    if engine.shield_charges:
        draw_text(screen, f"SHIELD x{engine.shield_charges}", RETRO_PALETTE["brick3"], energy_rect.x, energy_rect.y + 34, 12, True, shadow=False)
    if engine.split_charges:
        draw_text(screen, f"SPLIT x{engine.split_charges}", RETRO_PALETTE["brick2"], energy_rect.x + 100, energy_rect.y + 34, 12, True, shadow=False)


def draw_boss_hud(screen, engine):
    boss = engine.active_boss()
    if boss is None:
        return
    rect = pygame.Rect(engine.width // 2 - 190, engine.playfield_top - 36, 380, 22)
    draw_soft_glow(screen, rect, boss.accent, alpha=18 + int(pulse(2.0) * 14), spread=6, radius=5)
    pygame.draw.rect(screen, RETRO_PALETTE["panel_deep"], rect, border_radius=4)
    draw_bar(screen, rect.inflate(-4, -6), boss.hp, boss.max_hp, boss.accent)
    pygame.draw.rect(screen, boss.accent, rect, 1, border_radius=4)
    draw_text(screen, boss.name.upper(), RETRO_PALETTE["text_white"], rect.x + 10, rect.y - 18, 13, True, shadow=False)
    draw_text(screen, f"{boss.hp}/{boss.max_hp}", RETRO_PALETTE["text_muted"], rect.right - 58, rect.y - 17, 12, True, shadow=False)



def draw_level_summary(screen, engine):
    summary = engine.last_level_summary or {
        "level": engine.level - 1,
        "theme": "Run",
        "layout": "wall",
        "bricks": engine.level_bricks_destroyed,
        "bonus": 0,
        "score_gained": 0,
        "next_level": engine.level,
    }
    panel = pygame.Rect(0, 0, min(680, engine.width - 80), min(520, engine.height - 90))
    panel.center = (engine.width // 2, engine.height // 2)
    draw_panel(screen, panel, accent=RETRO_PALETTE["accent"], fill=(15, 20, 27))
    draw_glow_text(screen, f"LEVEL {summary['level']} CLEAR", RETRO_PALETTE["text_white"], panel.centerx, panel.y + 48, 32, True, center=True, glow_color=RETRO_PALETTE["accent"])
    detail = f"{summary['theme']} / {summary['layout']}"
    if summary.get("boss"):
        detail = f"{summary['boss']} defeated  |  {detail}"
    draw_text(screen, detail, RETRO_PALETTE["text_muted"], panel.centerx, panel.y + 88, 14, True, center=True, shadow=False)

    rows = [
        ("Bricks broken", summary["bricks"], RETRO_PALETTE["brick1"]),
        ("Level bonus", summary["bonus"], RETRO_PALETTE["accent"]),
        ("Score gained", summary["score_gained"], RETRO_PALETTE["accent_alt"]),
        ("Next level", summary["next_level"], RETRO_PALETTE["paddle"]),
    ]
    y = panel.y + 132
    for label, value, accent in rows:
        row = pygame.Rect(panel.x + 70, y, panel.width - 140, 38)
        pygame.draw.rect(screen, mix(RETRO_PALETTE["panel_soft"], accent, 0.08), row, border_radius=4)
        pygame.draw.rect(screen, accent, row, 1, border_radius=4)
        draw_text(screen, label.upper(), RETRO_PALETTE["text_muted"], row.x + 14, row.y + 11, 12, True, shadow=False)
        draw_text(screen, str(value), RETRO_PALETTE["text_white"], row.right - 84, row.y + 9, 16, True, shadow=False)
        y += 48
    confirm_key = engine.keybindings.action_label("confirm").split(" / ")[0]
    draw_arcade_button(screen, pygame.Rect(panel.centerx - 110, panel.bottom - 74, 220, 44), f"{confirm_key} CONTINUE", RETRO_PALETTE["accent"], phase=0.2)


def draw_brick_intro(screen, engine):
    panel = pygame.Rect(0, 0, min(700, engine.width - 80), min(420, engine.height - 120))
    panel.center = (engine.width // 2, engine.height // 2)
    draw_soft_glow(screen, panel, RETRO_PALETTE["accent_alt"], alpha=22 + int(pulse(1.8) * 12), spread=14, radius=10)
    draw_panel(screen, panel, accent=RETRO_PALETTE["accent_alt"], fill=(15, 20, 27))
    draw_glow_text(screen, f"LEVEL {engine.level} BRIEFING", RETRO_PALETTE["text_white"], panel.centerx, panel.y + 48, 32, True, center=True, glow_color=RETRO_PALETTE["accent_alt"])
    theme = getattr(engine.brick_grid, "theme_name", "Run")
    layout = getattr(engine.brick_grid, "layout_name", "wall")
    draw_text(screen, f"{theme} / {layout}", RETRO_PALETTE["text_muted"], panel.centerx, panel.y + 84, 14, True, center=True, shadow=False)
    draw_text(screen, "New brick effects appear in this level", RETRO_PALETTE["text"], panel.centerx, panel.y + 116, 16, False, center=True, shadow=False)
    draw_brick_codex(screen, engine, panel, panel.y + 148, engine.pending_brick_intro_kinds, "NEW BRICKS")
    confirm_key = engine.keybindings.action_label("confirm").split(" / ")[0]
    draw_arcade_button(screen, pygame.Rect(panel.centerx - 110, panel.bottom - 68, 220, 44), f"{confirm_key} START", RETRO_PALETTE["accent_alt"], phase=0.2)


def draw_boss_intro(screen, engine):
    boss = engine.current_boss_definition()
    if boss is None:
        return
    panel = pygame.Rect(0, 0, min(760, engine.width - 80), min(500, engine.height - 100))
    panel.center = (engine.width // 2, engine.height // 2)
    draw_soft_glow(screen, panel, boss.accent, alpha=24 + int(pulse(1.6) * 18), spread=18, radius=10)
    draw_panel(screen, panel, accent=boss.accent, fill=(14, 18, 25))
    draw_text(screen, f"BOSS LEVEL {engine.level}", boss.accent, panel.centerx, panel.y + 35, 14, True, center=True, shadow=False)
    draw_glow_text(screen, boss.name.upper(), RETRO_PALETTE["text_white"], panel.centerx, panel.y + 72, 34, True, center=True, glow_color=boss.accent)
    draw_text(screen, f"{boss.theme} / {boss.arena}", RETRO_PALETTE["text_muted"], panel.centerx, panel.y + 112, 14, True, center=True, shadow=False)

    portrait = pygame.Rect(panel.x + 54, panel.y + 150, 210, 116)
    pygame.draw.rect(screen, mix(RETRO_PALETTE["panel_deep"], boss.color, 0.14), portrait, border_radius=6)
    pygame.draw.rect(screen, boss.accent, portrait, 1, border_radius=6)
    preview_rect = pygame.Rect(0, 0, 122, 54)
    preview_rect.center = portrait.center
    draw_boss_sprite(screen, preview_rect, boss.color, boss.accent, pulse(2.0))

    info = pygame.Rect(portrait.right + 26, portrait.y, panel.right - portrait.right - 80, 116)
    pygame.draw.rect(screen, RETRO_PALETTE["panel_deep"], info, border_radius=5)
    pygame.draw.rect(screen, RETRO_PALETTE["line"], info, 1, border_radius=5)
    draw_text(screen, "ARENA STYLE", boss.accent, info.x + 14, info.y + 12, 11, True, shadow=False)
    draw_wrapped_text(screen, boss.style, RETRO_PALETTE["text"], pygame.Rect(info.x + 14, info.y + 32, info.width - 28, 34), 13, 2)
    draw_text(screen, "THREAT", boss.accent, info.x + 14, info.y + 72, 11, True, shadow=False)
    draw_wrapped_text(screen, boss.briefing, RETRO_PALETTE["text"], pygame.Rect(info.x + 14, info.y + 92, info.width - 28, 22), 12, 1)

    kinds = engine.pending_brick_intro_kinds or engine.level_special_kinds()
    draw_brick_codex(screen, engine, panel, panel.y + 290, kinds, "ARENA BRICKS")
    confirm_key = engine.keybindings.action_label("confirm").split(" / ")[0]
    draw_arcade_button(screen, pygame.Rect(panel.centerx - 118, panel.bottom - 66, 236, 44), f"{confirm_key} FACE BOSS", boss.accent, phase=0.2)


def draw_brick_codex(screen, engine, panel, y, kinds=None, title="BRICK EFFECTS"):
    kinds = engine.level_special_kinds() if kinds is None else kinds
    if not kinds:
        return
    codex = pygame.Rect(panel.x + 42, y, panel.width - 84, min(92, panel.bottom - y - 92))
    if codex.height < 54:
        return
    pygame.draw.rect(screen, mix(RETRO_PALETTE["panel_deep"], RETRO_PALETTE["accent_alt"], 0.08), codex, border_radius=5)
    pygame.draw.rect(screen, RETRO_PALETTE["line"], codex, 1, border_radius=5)
    draw_text(screen, title, RETRO_PALETTE["text_muted"], codex.x + 12, codex.y + 9, 11, True, shadow=False)

    visible = kinds[:min(4, len(kinds))]
    slot_width = max(116, (codex.width - 24) // max(1, len(visible)))
    for index, kind in enumerate(visible):
        label, effect = BRICK_KIND_INFO[kind]
        x = codex.x + 12 + index * slot_width
        brick_rect = pygame.Rect(x, codex.y + 32, 48, 22)
        draw_brick_sprite(screen, brick_rect, BrickGrid.color_for_kind(kind, RETRO_PALETTE["accent_alt"]), kind.value, 1, 1)
        draw_text(screen, label, RETRO_PALETTE["text_white"], x + 56, codex.y + 31, 11, True, shadow=False)
        draw_text(screen, effect, RETRO_PALETTE["text_muted"], x + 56, codex.y + 47, 10, False, shadow=False)


def draw_skill_selection(screen, engine):
    overlay = pygame.Surface((engine.width, engine.height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 80))
    screen.blit(overlay, (0, 0))

    header = pygame.Rect(0, 0, min(620, engine.width - 70), 128)
    header.centerx = engine.width // 2
    header.y = 70
    draw_panel(screen, header, accent=RETRO_PALETTE["accent"], fill=(17, 22, 28))
    title = "CHOOSE STARTING UPGRADE" if engine.is_starting_skill_draft() else "CHOOSE AN UPGRADE"
    draw_glow_text(screen, title, RETRO_PALETTE["text_white"], header.centerx, header.y + 42, 30, True, center=True, glow_color=RETRO_PALETTE["accent"])
    confirm_key = engine.keybindings.action_label("confirm").split(" / ")[0]
    draw_text(screen, f"Click a card or press {confirm_key} for the first option", RETRO_PALETTE["text"], header.centerx, header.y + 84, 16, False, center=True)

    mouse_pos = pygame.mouse.get_pos()
    for card in engine.skill_cards:
        card.draw(screen, mouse_pos)

    footer = pygame.Rect(0, engine.height - 78, min(620, engine.width - 70), 42)
    footer.centerx = engine.width // 2
    pygame.draw.rect(screen, (16, 20, 26), footer, border_radius=4)
    pygame.draw.rect(screen, RETRO_PALETTE["line"], footer, 1, border_radius=4)
    pygame.draw.line(screen, RETRO_PALETTE["accent_alt"], footer.topleft, footer.topright, 1)
    if engine.selected_skills:
        icon_x = footer.x + 14
        for skill in engine.selected_skills[-5:]:
            icon_rect = pygame.Rect(icon_x, footer.y + 7, 28, 28)
            code, accent, _ = SKILL_META.get(skill.type, ("UP", RETRO_PALETTE["accent_alt"], "Upgrade"))
            draw_skill_icon(screen, icon_rect, code, accent)
            icon_x += 34
    footer_label = f"Starting level {engine.level}" if engine.is_starting_skill_draft() else f"Entering level {engine.level}"
    draw_text(screen, footer_label, RETRO_PALETTE["text_muted"], footer.centerx, footer.y + 22, 14, True, center=True, shadow=False)
