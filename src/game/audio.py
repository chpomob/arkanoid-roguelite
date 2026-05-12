import array
import math
import random

import pygame


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
            self.sounds = self.build_sounds()
        except (pygame.error, OSError, ValueError):
            self.enabled = False
            self.sounds = {}

    def build_sounds(self):
        return {
            "menu": self.make_variants([(440, 0.00, 0.05), (660, 0.04, 0.06)], 0.12, 0.28),
            "select": self.make_variants([(520, 0.00, 0.06), (780, 0.05, 0.08)], 0.16, 0.36),
            "paddle": self.make_variants([(180, 0.00, 0.05), (260, 0.02, 0.06)], 0.10, 0.24),
            "brick": self.make_variants([(620, 0.00, 0.045)], 0.08, 0.24),
            "break": self.make_variants([(360, 0.00, 0.05), (920, 0.025, 0.045)], 0.11, 0.32, noise=0.10),
            "bomb": self.make_variants([(110, 0.00, 0.06), (90, 0.04, 0.14), (540, 0.02, 0.04)], 0.18, 0.42, noise=0.18),
            "pulse": self.make_variants([(720, 0.00, 0.06), (360, 0.04, 0.07)], 0.13, 0.28),
            "charge": self.make_variants([(520, 0.00, 0.05), (900, 0.04, 0.09)], 0.16, 0.34),
            "level": self.make_variants([(440, 0.00, 0.08), (660, 0.08, 0.08), (880, 0.16, 0.14)], 0.32, 0.34),
            "life": self.make_variants([(220, 0.00, 0.12), (145, 0.08, 0.16)], 0.25, 0.38, noise=0.05),
            "gameover": self.make_variants([(330, 0.00, 0.12), (240, 0.10, 0.16), (160, 0.24, 0.20)], 0.48, 0.34),
            "cannon": self.make_variants([(130, 0.00, 0.04), (760, 0.02, 0.08)], 0.14, 0.34, noise=0.08),
            "projectile": self.make_variants([(820, 0.00, 0.04), (1140, 0.025, 0.035)], 0.09, 0.22),
            "well": self.make_variants([(110, 0.00, 0.16), (155, 0.05, 0.14)], 0.22, 0.22),
            "shield": self.make_variants([(280, 0.00, 0.08), (560, 0.03, 0.10)], 0.18, 0.32),
            "split": self.make_variants([(480, 0.00, 0.05), (640, 0.03, 0.05), (800, 0.06, 0.05)], 0.16, 0.30),
            "skill": self.make_variants([(620, 0.00, 0.06), (860, 0.05, 0.10), (1040, 0.11, 0.08)], 0.22, 0.34),
            "highscore": self.make_variants([(660, 0.00, 0.08), (880, 0.08, 0.08), (1180, 0.16, 0.16)], 0.36, 0.36),
            "save": self.make_variants([(700, 0.00, 0.05), (520, 0.05, 0.08)], 0.16, 0.26),
        }

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

    def make_variants(self, notes, duration, volume, noise=0.0):
        return [self.make_tone(self.pitch_notes(notes, factor), duration, volume, noise=noise) for factor in (0.96, 1.0, 1.04)]

    @staticmethod
    def pitch_notes(notes, factor):
        return [(frequency * factor, start, duration) for frequency, start, duration in notes]

    def make_tone(self, notes, duration, volume, noise=0.0):
        frequency, _fmt, channels = pygame.mixer.get_init() or (44100, -16, 1)
        sample_count = max(1, int(frequency * duration))
        samples = array.array("h")
        rng = random.Random(42)

        for index in range(sample_count):
            t = index / frequency
            mixed = 0.0
            for note_frequency, start, note_duration in notes:
                if t < start or t >= start + note_duration:
                    continue
                note_t = (t - start) / max(0.001, note_duration)
                note_t = max(0.0, min(1.0, note_t))
                envelope = (1.0 - note_t) ** 1.8
                mixed += math.sin(2 * math.pi * note_frequency * (t - start)) * envelope
            if noise:
                mixed += rng.uniform(-1, 1) * noise * (1 - t / duration)
            mixed = max(-1.0, min(1.0, mixed * volume))
            value = int(mixed * 32767)
            for _ in range(channels):
                samples.append(value)

        return pygame.mixer.Sound(buffer=samples.tobytes())
