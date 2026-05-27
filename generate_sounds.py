"""
Pre-generate all game sounds as WAV files.

Run this ONCE on desktop to create assets/sounds/*.wav.
The web build then loads these instead of expensive WASM PCM synthesis.

Usage: python3 generate_sounds.py
"""
import array
import math
import os
import random
import struct
import wave


# ── Copy of the synthesis code from audio.py ──────────────────────

def make_tone(notes, duration, volume, noise=0.0, sample_rate=44100):
    sample_count = max(1, int(sample_rate * duration))
    samples = array.array("h")
    rng = random.Random(42)
    for i in range(sample_count):
        t = i / sample_rate
        mixed = 0.0
        for freq, start, note_dur in notes:
            if t < start or t >= start + note_dur:
                continue
            note_t = (t - start) / max(0.001, note_dur)
            note_t = max(0.0, min(1.0, note_t))
            envelope = (1.0 - note_t) ** 1.8
            mixed += math.sin(2 * math.pi * freq * (t - start)) * envelope
        if noise:
            mixed += rng.uniform(-1, 1) * noise * (1 - t / duration)
        mixed = max(-1.0, min(1.0, mixed * volume))
        samples.append(int(mixed * 32767))
    return samples


def pitch_notes(notes, factor):
    return [(freq * factor, start, dur) for freq, start, dur in notes]


SOUNDS = {
    "menu": ([(440, 0.00, 0.05), (660, 0.04, 0.06)], 0.12, 0.28),
    "select": ([(520, 0.00, 0.06), (780, 0.05, 0.08)], 0.16, 0.36),
    "paddle": ([(180, 0.00, 0.05), (260, 0.02, 0.06)], 0.10, 0.24),
    "brick": ([(620, 0.00, 0.045)], 0.08, 0.24),
    "break": ([(360, 0.00, 0.05), (920, 0.025, 0.045)], 0.11, 0.32, 0.10),
    "bomb": ([(110, 0.00, 0.06), (90, 0.04, 0.14), (540, 0.02, 0.04)], 0.18, 0.42, 0.18),
    "pulse": ([(720, 0.00, 0.06), (360, 0.04, 0.07)], 0.13, 0.28),
    "charge": ([(520, 0.00, 0.05), (900, 0.04, 0.09)], 0.16, 0.34),
    "level": ([(440, 0.00, 0.08), (660, 0.08, 0.08), (880, 0.16, 0.14)], 0.32, 0.34),
    "life": ([(220, 0.00, 0.12), (145, 0.08, 0.16)], 0.25, 0.38, 0.05),
    "gameover": ([(330, 0.00, 0.12), (240, 0.10, 0.16), (160, 0.24, 0.20)], 0.48, 0.34),
    "cannon": ([(130, 0.00, 0.04), (760, 0.02, 0.08)], 0.14, 0.34, 0.08),
    "projectile": ([(820, 0.00, 0.04), (1140, 0.025, 0.035)], 0.09, 0.22),
    "well": ([(110, 0.00, 0.16), (155, 0.05, 0.14)], 0.22, 0.22),
    "shield": ([(280, 0.00, 0.08), (560, 0.03, 0.10)], 0.18, 0.32),
    "split": ([(480, 0.00, 0.05), (640, 0.03, 0.05), (800, 0.06, 0.05)], 0.16, 0.30),
    "skill": ([(620, 0.00, 0.06), (860, 0.05, 0.10), (1040, 0.11, 0.08)], 0.22, 0.34),
    "highscore": ([(660, 0.00, 0.08), (880, 0.08, 0.08), (1180, 0.16, 0.16)], 0.36, 0.36),
    "save": ([(700, 0.00, 0.05), (520, 0.05, 0.08)], 0.16, 0.26),
}


def main():
    out_dir = os.path.join(os.path.dirname(__file__), "src", "assets", "sounds")
    os.makedirs(out_dir, exist_ok=True)

    total = 0
    for name, params in SOUNDS.items():
        notes = params[0]
        duration = params[1]
        volume = params[2]
        noise = params[3] if len(params) > 3 else 0.0

        for variant, factor in enumerate((0.96, 1.0, 1.04)):
            pnotes = pitch_notes(notes, factor)
            samples = make_tone(pnotes, duration, volume, noise=noise)

            filename = f"{name}_{variant}.wav"
            filepath = os.path.join(out_dir, filename)
            with wave.open(filepath, "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(44100)
                wf.writeframes(samples.tobytes())

            size_kb = os.path.getsize(filepath) / 1024
            total += size_kb
            print(f"  {filename:30s} {size_kb:7.1f} KB")

    print(f"\nTotal: {total:.0f} KB ({total/1024:.1f} MB) in {len(SOUNDS) * 3} files")
    print(f"Output: {out_dir}")


if __name__ == "__main__":
    main()
