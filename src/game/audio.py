import os
import random
import time

import pygame

SOUND_NAMES = [
    "menu", "select", "paddle", "brick", "break", "bomb",
    "pulse", "charge", "level", "life", "gameover",
    "cannon", "projectile", "well", "shield", "split",
    "skill", "highscore", "save",
]

SOUND_THROTTLES = {
    "cannon": 0.035,
    "projectile": 0.040,
}


class SoundManager:
    def __init__(self, enabled=True, volume=0.45, muted=False):
        self.enabled = False
        self.volume = max(0.0, min(1.0, volume))
        self.muted = muted
        self.rng = random.Random()
        self.sounds = {}
        self._last_played_at = {}
        self._sound_volumes = {}
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
        self._sound_volumes.clear()
        sound_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "sounds")
        sounds = {}
        for name in SOUND_NAMES:
            variants = []
            for variant in (0, 1, 2):
                # Try .ogg first (pygbag auto-converts WAV→OGG), then .wav
                for ext in (".ogg", ".wav"):
                    path = os.path.join(sound_dir, f"{name}_{variant}{ext}")
                    try:
                        variants.append(pygame.mixer.Sound(path))
                        break
                    except (pygame.error, FileNotFoundError):
                        continue
            if variants:
                sounds[name] = variants
        return sounds

    def play(self, name, volume=1.0):
        if not self.enabled or self.muted:
            return
        cooldown = SOUND_THROTTLES.get(name, 0.0)
        now = time.monotonic() if cooldown > 0.0 else 0.0
        last_played = self._last_played_at.get(name)
        if cooldown > 0.0 and last_played is not None and now - last_played < cooldown:
            return
        sounds = self.sounds.get(name)
        if isinstance(sounds, list):
            sound = self.rng.choice(sounds)
        else:
            sound = sounds
        if sound is None:
            return
        effective_volume = max(0.0, min(1.0, self.volume * volume))
        sound_key = id(sound)
        try:
            if self._sound_volumes.get(sound_key) != effective_volume:
                sound.set_volume(effective_volume)
                self._sound_volumes[sound_key] = effective_volume
            sound.play()
            if cooldown > 0.0:
                self._last_played_at[name] = now
        except pygame.error:
            return

    def set_volume(self, volume):
        next_volume = max(0.0, min(1.0, volume))
        if next_volume == self.volume:
            return
        self.volume = next_volume
        self._sound_volumes.clear()

    def set_muted(self, muted):
        self.muted = bool(muted)

    @staticmethod
    def pitch_notes(notes, factor):
        """Scale frequencies by factor, preserving timing. Used by pre-generator."""
        return [(frequency * factor, start, duration) for frequency, start, duration in notes]
