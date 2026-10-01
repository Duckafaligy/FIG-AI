"""Builds public/journey-sound.wav for src/Journey.tsx: a 40 s, 120 BPM track
with an intro build, a drop, a breakdown behind the AI scene, a second drop
and a logo hit, plus effects on every tap, tick and card. Reuses the effect
generators from make_sound.py.

    python sound/make_journey.py
"""
import wave
from pathlib import Path

import numpy as np

from make_sound import (SR, env, filt, impact, note, ping, pop, riser, rng, shimmer, t, thud, tick, whoosh)

BEAT = 0.5
FRAME = 1 / 30
LENGTH = 40.0
BEATS = 80
# Scene starts in beats, the same as SCENES in Journey.tsx.
SC = {"intro": 0, "url": 6, "scan": 12, "score": 19, "findings": 26, "connect": 34, "ai": 42, "approve": 50, "improve": 58, "end": 66}
sec = lambda beats: beats * BEAT
CHORDS = [[45, 57, 64, 69], [41, 57, 65, 69], [48, 55, 64, 67], [43, 55, 62, 67]]   # Am F C G, upbeat minor pop


def chime(level=0.35):
    out = np.zeros(int(0.7 * SR))
    for i, f in enumerate((1318.5, 1975.5)):          # E6 then B6
        n = 0.5
        x = t(n)
        tone = (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(2 * np.pi * 2 * f * x)) * env(n, 0.002, 0.25, 4)
        s = int(i * 0.08 * SR)
        out[s:s + len(tone)] += tone
    return level * out


def _click(level):
    """A tap: a tick on top of a short low pop."""
    a, b = tick(level), pop(420, 0.07, level * 0.7)
    out = np.zeros(max(len(a), len(b)))
    out[: len(a)] += a
    out[: len(b)] += b
    return out


def music():
    total = int((LENGTH + 1) * SR)
    kick, hats, claps, bass, plucks, pad, lead = (np.zeros(total) for _ in range(7))
    kick_env = np.zeros(total)

    def put(buf, at, sig):
        i = int(at * SR)
        if i >= total:
            return
        j = min(total, i + len(sig))
        buf[i:j] += sig[: j - i]

    breakdown = range(SC["ai"], SC["approve"])
    for b in range(BEATS):
        at = sec(b)
        drums = SC["url"] <= b < BEATS - 2 and b not in breakdown
        chord = CHORDS[(b // 4) % 4]
        if drums:
            k = thud(1.0)
            put(kick, at, k); put(kick_env, at, np.abs(k))
            for s16 in (1, 2, 3):                                      # sixteenth hats, the offbeat louder
                put(hats, at + s16 * BEAT / 4, tick(0.26 if s16 == 2 else 0.12))
            if b % 2 == 1:
                n = 0.2
                c = filt(rng.standard_normal(int(n * SR)), "bandpass", [900, 2800]) * env(n, 0.001, 0.08, 4)
                put(claps, at, 0.55 * c / (np.abs(c).max() + 1e-9))
            for half in (0, 1):                                        # driving eighth-note bass
                n = BEAT / 2
                x = t(n)
                f = note(chord[0] - 12 + (12 if half else 0))
                saw = sum(np.sin(2 * np.pi * f * h * x) / h for h in range(1, 8))
                put(bass, at + half * n, 0.26 * filt(saw, "lowpass", 900) * env(n, 0.003, 0.18, 2))
        for s in range(4):                                             # pluck arpeggio all the way through
            n = 0.2
            x = t(n)
            f = note(chord[(s * 2 + b) % 4] + 12)
            y = (np.sin(2 * np.pi * f * x) + 0.35 * np.sin(2 * np.pi * 2 * f * x)) * env(n, 0.002, 0.07, 5)
            put(plucks, at + s * BEAT / 4, 0.12 * y)
        # a bright lead hook in the second half, one note a beat
        if SC["approve"] <= b < SC["end"] + 8:
            n = 0.45
            x = t(n)
            f = note(chord[(b % 2) + 2] + 24)
            y = np.sign(np.sin(2 * np.pi * f * x)) * 0.25 + np.sin(2 * np.pi * f * x)
            put(lead, at, 0.07 * filt(y, "lowpass", 5000) * env(n, 0.005, 0.2, 3))
    for bar in range(BEATS // 4):
        n = 4 * BEAT + 0.3
        x = t(n)
        y = sum(np.sin(2 * np.pi * note(m) * d * x) for m in CHORDS[bar % 4] for d in (0.996, 1.004))
        shape = np.minimum(1, x / 0.25) * np.minimum(1, (n - x) / 0.25)
        put(pad, sec(bar * 4), 0.05 * filt(y, "lowpass", 1800) * shape)

    duck = 1 - 0.6 * np.clip(filt(kick_env, "lowpass", 12) * 3, 0, 1)
    # The intro and the breakdown sound muffled, so each drop opens up.
    open_up = np.ones(total)
    open_up[: int(sec(SC["url"]) * SR)] = np.linspace(0.3, 1, int(sec(SC["url"]) * SR))
    a, b = int(sec(SC["ai"]) * SR), int(sec(SC["approve"]) * SR)
    open_up[a:b] = np.linspace(0.5, 1, b - a)
    melodic = filt(plucks + pad, "lowpass", 2500) * (1 - open_up) + (plucks + pad) * open_up
    return kick * 0.9 + hats + claps + bass * duck + melodic * duck + lead


def effects():
    total = int((LENGTH + 1) * SR)
    out = np.zeros(total)

    def at(s, sig, gain=1.0):
        i = int(s * SR)
        j = min(total, i + len(sig))
        if 0 <= i < total:
            out[i:j] += gain * sig[: j - i]

    S = {k: sec(v) for k, v in SC.items()}
    for name in ("url", "scan", "score", "findings", "connect", "ai", "approve", "improve", "end"):
        at(S[name] - 0.3, whoosh(0.55, level=0.45))
    # intro: the phone rises, FIG. lands, a riser into the first drop
    at(0.2, whoosh(0.8, 150, 1500, 0.4))
    at(20 * FRAME, shimmer(0.25))
    at(S["url"] - 1.5, riser(1.5, 0.4))
    at(S["url"], impact(0.7))
    # url: one tick per typed character, then the Scan tap
    for k in range(20):
        at(S["url"] + (10 + 1.6 * k) * FRAME, tick(0.22))
    at(S["url"] + 66 * FRAME, _click(0.5))
    # scan: a rising pop as each page is read
    for i in range(6):
        at(S["scan"] + (12 + i * 12) * FRAME, pop(660 + i * 90, level=0.32))
    # score: the ring fills, then four bars
    at(S["score"] + 4 * FRAME, riser(1.0, 0.25))
    for i in range(4):
        at(S["score"] + (30 + i * 6) * FRAME, tick(0.3))
    # findings: five cards fly in, one comes forward
    for i in range(5):
        at(S["findings"] + i * 4 * FRAME, whoosh(0.3, 1200, 6000, 0.25))
    at(S["findings"] + 64 * FRAME, whoosh(0.5, 200, 2000, 0.4))
    at(S["findings"] + 74 * FRAME, thud(0.5))
    # connect: tiles pop in, WordPress is tapped, connected
    for i in range(5):
        at(S["connect"] + (6 + i * 3) * FRAME, pop(900 + i * 70, 0.08, 0.2))
    at(S["connect"] + 36 * FRAME, _click(0.5))
    at(S["connect"] + 40 * FRAME, chime(0.4))
    # ai: the rings come up in the breakdown, each check pings higher, riser into drop two
    at(S["ai"], whoosh(0.9, 100, 800, 0.35))
    for i in range(5):
        at(S["ai"] + (14 + i * 7) * FRAME, ping(1046 + i * 130, 0.2))
    at(S["approve"] - 2.0, riser(2.0, 0.45))
    at(S["approve"], impact(0.8))
    # approve: tap, it goes live, undo appears
    at(S["approve"] + 20 * FRAME, _click(0.5))
    at(S["approve"] + 36 * FRAME, chime(0.45))
    at(S["approve"] + 48 * FRAME, pop(520, 0.12, 0.3))
    # improve: the score climbs, +39 lands
    at(S["improve"] + 8 * FRAME, riser(1.2, 0.35))
    at(S["improve"] + 44 * FRAME, chime(0.5))
    at(S["improve"] + 44 * FRAME, thud(0.4))
    # end: the logo hit, the tagline, the pill
    at(S["end"], impact(1.0))
    at(S["end"] + 12 * FRAME, shimmer(0.35))
    at(S["end"] + 32 * FRAME, pop(700, 0.12, 0.35))
    at(sec(BEATS - 2), impact(0.6))
    return out


def main():
    mix = 0.55 * music() + 0.75 * effects()
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)
    end = int(LENGTH * SR)
    mix = mix[:end]
    fade = int(1.2 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    mix *= 0.89 / (np.abs(mix).max() + 1e-9)
    highs = filt(mix, "highpass", 3000)
    shift = int(0.012 * SR)
    right = mix - highs + np.concatenate([np.zeros(shift), highs[:-shift]])
    pcm = (np.clip(np.stack([mix, right], axis=1), -1, 1) * 32767).astype("<i2")
    out = Path(__file__).resolve().parent.parent / "public" / "journey-sound.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print(f"wrote {out} ({len(mix) / SR:.2f}s)")


if __name__ == "__main__":
    main()
