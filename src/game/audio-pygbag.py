import os
import random

import pygame

SOUND_NAMES = [
    "menu", "select", "paddle", "brick", "break", "bomb",
    "pulse", "charge", "level", "life", "gameover",
    "cannon", "projectile", "well", "shield", "split",
    "skill", "highscore", "save",
]


class SoundManager:
    def __init__(self, enabled=True, volume=0.45, muted=False):
        self.enabled = False
        self.volume = max(0.0, min(1.0, volume))
        self.muted = muted
        self.rng = random.Random()
        self.sounds = {}
        if not enabled:
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(44100, -16, 1, 512)
                pygame.mixer.init()
            self.enabled = True
            self.sounds = self._load_sounds()
        except (pygame.error, OSError, ValueError):
            self.enabled = False
            self.sounds = {}

    def _load_sounds(self):
        sound_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "sounds")
        sounds = {}
        for name in SOUND_NAMES:
            variants = []
            for variant in (0, 1, 2):
                path = os.path.join(sound_dir, f"{name}_{variant}.ogg")
                try:
                    variants.append(pygame.mixer.Sound(path))
                except (pygame.error, FileNotFoundError):
                    pass
            if variants:
                sounds[name] = variants
        return sounds

    def play(self, name, volume=1.0):
        if not self.enabled or self.muted:
            return
        sounds = self.sounds.get(name)
        if isinstance(sounds, list):
            sound = self.rng.choice(sounds)
        else:
            sound = sounds
        if sound is None:
            return
        sound.set_volume(max(0, min(1, self.volume * volume)))
        sound.play()

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))

    def set_muted(self, muted):
        self.muted = bool(muted)

    @staticmethod
    def pitch_notes(notes, factor):
        """Scale frequencies by factor, preserving timing. Used by pre-generator."""
        return [(frequency * factor, start, duration) for frequency, start, duration in notes]
