import json
from copy import deepcopy
from pathlib import Path

import pygame


ACTIONS = [
    ("left", "Move Left"),
    ("right", "Move Right"),
    ("up", "Menu Up / Cannon"),
    ("down", "Menu Down / Well"),
    ("confirm", "Confirm"),
    ("back", "Back / Pause"),
    ("save", "Save Run"),
    ("resume", "Resume Run"),
    ("scores", "High Scores"),
    ("skills", "Skill Guide"),
    ("controls", "Controls"),
    ("settings", "Settings"),
]

DEFAULT_BINDINGS = {
    "left": [pygame.K_LEFT, pygame.K_a],
    "right": [pygame.K_RIGHT, pygame.K_d],
    "up": [pygame.K_UP, pygame.K_w],
    "down": [pygame.K_DOWN, pygame.K_s],
    "confirm": [pygame.K_RETURN, pygame.K_SPACE],
    "back": [pygame.K_ESCAPE],
    "save": [pygame.K_F5],
    "resume": [pygame.K_c],
    "scores": [pygame.K_h],
    "skills": [pygame.K_g],
    "controls": [pygame.K_k],
    "settings": [pygame.K_m],
}


class KeyBindings:
    def __init__(self, path="arkanoid_keybindings.json"):
        self.path = Path(path)
        self.bindings = deepcopy(DEFAULT_BINDINGS)
        self.load()

    def load(self):
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        loaded = data.get("bindings", data)
        if not isinstance(loaded, dict):
            return

        for action, _label in ACTIONS:
            raw_keys = loaded.get(action)
            if not isinstance(raw_keys, list):
                continue
            clean_keys = []
            for key in raw_keys[:2]:
                try:
                    clean_keys.append(int(key))
                except (TypeError, ValueError):
                    continue
            if clean_keys:
                self.bindings[action] = clean_keys

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"version": 1, "bindings": self.bindings}
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def reset(self):
        self.bindings = deepcopy(DEFAULT_BINDINGS)
        self.save()

    def set_binding(self, action, slot, key):
        if action not in self.bindings:
            return []

        key = int(key)
        conflicts = []
        for other_action, keys in self.bindings.items():
            if other_action == action:
                continue
            if key in keys:
                conflicts.append(other_action)
            self.bindings[other_action] = [existing for existing in keys if existing != key]

        keys = list(self.bindings[action])
        while len(keys) <= slot:
            keys.append(None)
        keys[slot] = key
        self.bindings[action] = [existing for existing in keys if existing is not None]
        self.save()
        return conflicts

    def action_down(self, keys, action):
        return any(self.is_key_down(keys, key) for key in self.bindings.get(action, []))

    def event_matches(self, event, action):
        return getattr(event, "key", None) in self.bindings.get(action, [])

    def is_key_down(self, keys, key):
        if hasattr(keys, "get"):
            return bool(keys.get(key, False))
        try:
            return bool(keys[key])
        except (IndexError, KeyError):
            return False

    def key_name(self, key):
        return pygame.key.name(key).upper()

    def action_label(self, action):
        keys = self.bindings.get(action, [])
        return " / ".join(self.key_name(key) for key in keys) if keys else "UNBOUND"

    def key_for_action(self, action, slot=0):
        """Return the key code for an action's binding slot (default first slot)."""
        keys = self.bindings.get(action, [])
        if keys and slot < len(keys):
            return keys[slot]
        return pygame.K_RETURN
