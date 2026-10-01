"""Builds public/hook-sound.wav for src/Hook.tsx: 12.8 s at 150 BPM (12 frames
a beat) in F minor. Hard and dark rather than bright: 808 hits under each
cold-open word, a distorted four-on-the-floor, a sliding 808 bassline, minor
stabs, trap hat rolls, a stutter on the red flash, and a gap before the logo.

    python sound/make_hook.py
"""
import wave
from pathlib import Path

import numpy as np

from make_sound import SR, env, filt, note, pop, rng, shimmer, t, tick, whoosh

FRAME = 1 / 30
BEAT = 12 * FRAME                                   # 0.4 s = 150 BPM
S = {"slam": 0, "type": 4, "scan": 8, "metrics": 12, "score": 16, "problem": 19, "fix": 22, "meet": 26, "tour": 29,
     "brand": 54, "end": 64}
HIT = 0                                              # the logo arrives on the first beat of the ending
# The tour (Hook.tsx TOUR / CLICKS): clicks, then the page changes a few frames later.
TOUR_CLICKS = [46, 118, 178, 238]
TOUR_PAGES = [54, 126, 186, 246]
LENGTH = S["end"] * BEAT
at_beat = lambda beats: beats * BEAT
F = lambda frames: frames * FRAME

# Fm - Db - Eb - C (the C major chord is the dark, tense turn back to F minor).
CHORDS = [[53, 56, 60], [49, 53, 56], [51, 55, 58], [48, 52, 55]]
ROOTS = [29, 25, 27, 24]                             # 808 roots: F1, Db1, Eb1, C1
# 808 rhythm inside each bar of four beats, in beats: syncopated, trap-style.
BASS_HITS = [0, 0.75, 1.5, 2.5, 3.25]


def sat(x, drive=3.0):
    return np.tanh(drive * x) / np.tanh(drive)


def kick(level=1.0):
    n = 0.32
    x = t(n)
    f = 50 + 160 * np.exp(-x * 40)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.14, 3)
    click = filt(rng.standard_normal(len(x)), "highpass", 2500) * env(n, 0.0005, 0.006, 6) * 0.4
    return level * sat(body + click, 4)


def e808(midi, n=0.9, glide_from=None, level=0.8):
    x = t(n)
    f = note(midi)
    if glide_from is not None:
        f = f + (note(glide_from) - f) * np.exp(-x * 14)
    y = np.sin(2 * np.pi * np.cumsum(np.full_like(x, 1) * f) / SR)
    return level * sat(y * env(n, 0.002, n * 0.6, 2), 2.2)


def clap(level=0.6):
    n = 0.25
    noise = filt(rng.standard_normal(int(n * SR)), "bandpass", [1100, 5000])
    # three quick bursts, the way a real clap smears
    shape = sum(env(n, 0.0005, 0.012, 5) * (t(n) >= d) for d in (0, 0.012, 0.024)) + env(n, 0.03, 0.12, 4)
    return level * noise / (np.abs(noise).max() + 1e-9) * shape / 2


def hat(level=0.2, open_=False):
    n = 0.18 if open_ else 0.05
    x = filt(rng.standard_normal(int(n * SR)), "highpass", 7000)
    return level * x / (np.abs(x).max() + 1e-9) * env(n, 0.0005, 0.07 if open_ else 0.015, 5)


def stab(chord, level=0.12):
    n = 0.22
    x = t(n)
    y = sum(np.sign(np.sin(2 * np.pi * note(m) * d * x)) for m in chord for d in (0.994, 1.006))
    return level * filt(y, "lowpass", 2400) * env(n, 0.002, 0.08, 4) / len(chord)


def boom(midi=29, level=1.0):
    """The cold-open hit: an 808 drop with a distorted kick and a noise burst on top."""
    a = e808(midi, 0.7, glide_from=midi + 12, level=0.9)
    k = kick(0.9)
    nz = filt(rng.standard_normal(int(0.3 * SR)), "lowpass", 4000) * env(0.3, 0.001, 0.08, 4) * 0.4
    out = np.zeros(len(a))
    out[: len(k)] += k
    out[: len(nz)] += nz
    return level * sat(out + a, 1.8)


def zap(level=0.3, up=True):
    n = 0.16
    x = t(n)
    f = (400 + 3600 * x / n) if up else (4000 - 3600 * x / n)
    return level * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(n, 0.001, 0.06, 4) * 0.5


def scratch(level=0.25):
    """One stroke of a marker: a short, rough band of noise."""
    n = 0.03
    x = filt(rng.standard_normal(int(n * SR)), "bandpass", [1500, 6000])
    return level * x / (np.abs(x).max() + 1e-9) * env(n, 0.002, 0.015, 3)


def keyclick(level=0.3):
    n = 0.03
    x = filt(rng.standard_normal(int(n * SR)), "bandpass", [2500, 9000])
    return level * x / (np.abs(x).max() + 1e-9) * env(n, 0.0003, 0.006, 6)


def glitch(level=0.6):
    n = 0.5
    x = t(n)
    buzz = np.sign(np.sin(2 * np.pi * 55 * x)) + 0.6 * np.sign(np.sin(2 * np.pi * 111 * x + np.sin(x * 90)))
    gate = (np.floor(x * 48) % 3 != 0)
    return level * sat(filt(buzz * gate, "lowpass", 2600), 2) * env(n, 0.001, 0.3, 2)


def impact(level=1.0, midi=29):
    n = 2.2
    x = t(n)
    sub = e808(midi, n, glide_from=midi + 19, level=1.0)
    nz = filt(rng.standard_normal(len(x)), "lowpass", 3000) * env(n, 0.001, 0.3, 4)
    tail = filt(rng.standard_normal(len(x)), "bandpass", [300, 1800]) * env(n, 0.01, 1.2, 2) * 0.15
    return level * sat(sub + 0.4 * nz / (np.abs(nz).max() + 1e-9) + tail, 1.5)


def riser(n, level=0.4):
    x = t(n)
    noise = filt(rng.standard_normal(len(x)), "highpass", 1500) * (x / n) ** 2.5
    tone = np.sign(np.sin(2 * np.pi * np.cumsum(120 * (16 ** (x / n))) / SR)) * (x / n) ** 3 * 0.3
    return level * (noise / (np.abs(noise).max() + 1e-9) + tone)


def music():
    total = int((LENGTH + 3) * SR)
    kick_bus, perc, bass, stabs, pad = (np.zeros(total) for _ in range(5))
    kick_env = np.zeros(total)

    def put(buf, at, sig):
        i = int(at * SR)
        j = min(total, i + len(sig))
        if 0 <= i < total:
            buf[i:j] += sig[: j - i]

    stutter = range(S["problem"], S["fix"])                  # the red flash: the beat chokes
    for bt in range(S["type"], S["brand"] + HIT):
        at = at_beat(bt)
        bar, pos = (bt - S["type"]) // 4, (bt - S["type"]) % 4
        chord, root = CHORDS[bar % 4], ROOTS[bar % 4]
        if bt in stutter:
            for k in range(4):                               # a gated 16th stutter of kick + stab
                put(kick_bus, at + k * BEAT / 4, kick(0.5 if k else 0.9))
            put(stabs, at, stab(chord, 0.18))
            continue
        halftime = S["meet"] <= bt < S["tour"]              # a breather on "Meet FIG."
        build = S["brand"] - 2 <= bt < S["brand"]           # a clap roll into the logo
        if halftime and pos % 2 == 1:
            put(perc, at + BEAT / 2, hat(0.14))
            continue
        k = kick(1.0)
        put(kick_bus, at, k); put(kick_env, at, np.abs(k))
        if build:
            for s16 in range(4):
                put(perc, at + s16 * BEAT / 4, clap(0.25 + 0.08 * s16 + 0.15 * (bt - S["brand"] + 2)))
        elif (halftime and pos == 2) or (not halftime and pos in (1, 3)):
            put(perc, at, clap(0.6))
        # 16th hats; the last beat of each bar rolls in 32nds, trap-style
        steps = 8 if pos == 3 and bar % 2 == 1 else 4
        for s16 in range(steps):
            put(perc, at + s16 * BEAT / steps, hat(0.22 if s16 % 2 else 0.12))
        if pos == 2:
            put(perc, at + BEAT / 2, hat(0.18, open_=True))
        put(stabs, at + BEAT / 2, stab(chord))                # offbeat minor stabs
        if pos == 0:
            for h in BASS_HITS:
                glide = root + 5 if h == 2.5 else None
                put(bass, at + h * BEAT, e808(root, 0.45 if h < 3 else 0.3, glide_from=glide, level=0.75))
        # a dark filtered arp, rising through each bar
        for s16 in range(4):
            n = 0.1
            f = note(chord[(s16 + pos) % 3] + 12)
            y = np.sign(np.sin(2 * np.pi * f * t(n))) * env(n, 0.001, 0.04, 5)
            put(pad, at + s16 * BEAT / 4, 0.05 * filt(y, "lowpass", 1200 + 800 * pos))
    # the ending: one dark chord that rings under the logo
    n = 4.5
    y = sum(np.sign(np.sin(2 * np.pi * note(m) * d * t(n))) for m in (41, 53, 56, 60) for d in (0.995, 1.005))
    put(pad, at_beat(S["brand"] + HIT), 0.06 * filt(y, "lowpass", 1600) * env(n, 0.01, 2.2, 2))
    duck = 1 - 0.65 * np.clip(filt(kick_env, "lowpass", 14) * 3, 0, 1)
    return kick_bus * 0.95 + perc + bass * 0.95 + (stabs + pad) * duck


def effects():
    total = int((LENGTH + 3) * SR)
    out = np.zeros(total)

    def at(s, sig):
        i = int(s * SR)
        j = min(total, i + len(sig))
        if 0 <= i < total:
            out[i:j] += sig[: j - i]

    # cold open: an 808 boom on every word, the last one lower and glitched
    for i, m in enumerate((29, 29, 32, 24)):
        at(at_beat(S["slam"] + i), boom(m, 0.95 if i < 3 else 1.1))
    at(at_beat(3) + F(2), glitch(0.35))
    at(at_beat(S["type"]) - 0.35, riser(0.35, 0.35))
    # the phone flies in, keys click, Scan is pressed
    at(at_beat(S["type"]), whoosh(0.4, 200, 3000, 0.45))
    for k in range(12):
        at(at_beat(S["type"]) + F(8 + 1.7 * k), keyclick(0.4))
    at(at_beat(S["type"]) + F(36), keyclick(0.6)); at(at_beat(S["type"]) + F(36), zap(0.3))
    # six pages read: a laser zap each
    for i in range(6):
        at(at_beat(S["scan"]) + F(6 + i * 6), zap(0.22, up=i % 2 == 0))
    # the chart: each row slides in from a side
    for i in range(4):
        at(at_beat(S["metrics"]) + F(3 + i * 4), whoosh(0.28, 500, 5000, 0.28))
        at(at_beat(S["metrics"]) + F(9 + i * 4), zap(0.18, up=True))
    # the score drops in from the top and lands
    at(at_beat(S["score"]), whoosh(0.3, 5000, 400, 0.4))
    at(at_beat(S["score"]) + F(8), boom(27, 0.95))
    # three cliches, one a beat: it flies in, a marker scratches it out, the stamp thuds
    for i in range(3):
        t0 = at_beat(S["problem"]) + F(i * 12)
        at(t0, whoosh(0.2, 3000, 800, 0.3))
        for k in range(8):
            at(t0 + F(3) + k * 0.02, scratch(0.22))
        at(t0 + F(6), boom(29 if i < 2 else 24, 0.6 if i < 2 else 0.85))
    at(at_beat(S["problem"]) + F(30), glitch(0.45))
    # the fix on the laptop: the new title types in, approve, the pull request opens
    at(at_beat(S["fix"]) - 0.6, riser(0.6, 0.4))
    at(at_beat(S["fix"]), boom(29, 0.85))
    for k in range(0, 43, 3):
        at(at_beat(S["fix"]) + F(4 + 0.6 * k), keyclick(0.3))
    at(at_beat(S["fix"]) + F(32), keyclick(0.6))
    at(at_beat(S["fix"]) + F(35), boom(29, 0.9))
    at(at_beat(S["fix"]) + F(35), zap(0.35))
    # Meet FIG., then the tour: a soft click on each click, a light swish as the page changes
    at(at_beat(S["meet"]), boom(29, 0.6))
    at(at_beat(S["tour"]), whoosh(0.4, 300, 3000, 0.25))
    for f in TOUR_CLICKS:
        at(at_beat(S["tour"]) + F(f), keyclick(0.55))
    for f in TOUR_PAGES:
        at(at_beat(S["tour"]) + F(f) - 0.05, whoosh(0.25, 1500, 5000, 0.16))
    # the ending: one deep hit as the logo rises, a shimmer under the tagline
    at(at_beat(S["brand"]) - 0.4, riser(0.4, 0.3))
    at(at_beat(S["brand"]), impact(0.8))
    at(at_beat(S["brand"]) + F(20), shimmer(0.2))
    return out


def main():
    mix = 0.5 * music() + 0.7 * effects()
    # the gap: pull the music down for the half beat before the logo
    g0, g1 = int((at_beat(S["brand"] + HIT) - 0.2) * SR), int(at_beat(S["brand"] + HIT) * SR)
    mix[g0:g1] *= np.linspace(1, 0.15, g1 - g0)
    mix = np.tanh(mix * 1.15) / np.tanh(1.15)
    end = int(LENGTH * SR)
    mix = mix[:end]
    fade = int(1.0 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    mix *= 0.9 / (np.abs(mix).max() + 1e-9)
    highs = filt(mix, "highpass", 3000)
    shift = int(0.012 * SR)
    right = mix - highs + np.concatenate([np.zeros(shift), highs[:-shift]])
    pcm = (np.clip(np.stack([mix, right], axis=1), -1, 1) * 32767).astype("<i2")
    out = Path(__file__).resolve().parent.parent / "public" / "hook-sound.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print(f"wrote {out} ({len(mix) / SR:.2f}s)")


if __name__ == "__main__":
    main()
