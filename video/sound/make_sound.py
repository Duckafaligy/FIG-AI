"""Builds public/reel-sound.wav: a 120 BPM track plus sound effects timed to
src/Reel.tsx. Everything is synthesized here, so there is nothing to license.

    python sound/make_sound.py

Times are in seconds (a beat is 0.5 s, a frame is 1/30 s). If a scene moves in
Reel.tsx, move its start in SCENES below to match."""
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

SR = 48_000
BEAT = 0.5
LENGTH = 13.5 + 1.0          # one second of tail after the last frame is cut by the video
FRAME = 1 / 30
rng = np.random.default_rng(7)

# Scene starts from Reel.tsx, in seconds.
SCENES = {"hard": 0.0, "generic": 1.5, "hidden": 3.0, "fig": 5.5, "report": 7.5, "kinds": 9.0, "close": 11.0, "end": 13.5}


def t(n):
    return np.arange(int(n * SR)) / SR


def env(n, attack=0.005, decay=0.2, curve=4.0):
    x = t(n)
    a = np.clip(x / max(attack, 1e-4), 0, 1)
    d = np.exp(-curve * np.clip(x - attack, 0, None) / max(decay, 1e-4))
    return a * d


def filt(x, kind, freq, order=2):
    sos = butter(order, freq, btype=kind, fs=SR, output="sos")
    return sosfilt(sos, x)


def sweep_filter(x, f0, f1, kind="bandpass", width=0.6, steps=48):
    """A filter whose centre moves from f0 to f1 over the sound, done in chunks."""
    out = np.zeros_like(x)
    edges = np.linspace(0, len(x), steps + 1).astype(int)
    for i in range(steps):
        a, b = edges[i], edges[i + 1]
        f = f0 * (f1 / f0) ** (i / steps)
        lo, hi = max(40, f * (1 - width / 2)), min(SR / 2 - 100, f * (1 + width / 2))
        seg = x[max(0, a - 512):b]
        y = sosfilt(butter(2, [lo, hi], btype="bandpass", fs=SR, output="sos"), seg)
        out[a:b] = y[-(b - a):]
    return out


# --------------------------------------------------------------- sound effects

def whoosh(n=0.55, f0=300, f1=4000, level=0.5):
    x = rng.standard_normal(int(n * SR))
    y = sweep_filter(x, f0, f1)
    shape = np.sin(np.linspace(0, np.pi, len(y))) ** 1.5
    return level * y * shape / (np.abs(y).max() + 1e-9)


def pop(freq=900, n=0.12, level=0.45):
    x = t(n)
    f = freq * (1 + 1.5 * np.exp(-x * 60))
    return level * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.05, 5)


def tick(level=0.35):
    n = 0.04
    x = filt(rng.standard_normal(int(n * SR)), "highpass", 3500)
    return level * x * env(n, 0.0005, 0.01, 6) / (np.abs(x).max() + 1e-9)


def thud(level=0.8):
    n = 0.45
    x = t(n)
    f = 45 + 110 * np.exp(-x * 25)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.18, 3)
    return level * body


def impact(level=1.0):
    n = 1.6
    x = t(n)
    f = 38 + 140 * np.exp(-x * 18)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.7, 2.5)
    noise = filt(rng.standard_normal(len(x)), "lowpass", 2500) * env(n, 0.001, 0.25, 4)
    return level * (0.9 * sub + 0.35 * noise / (np.abs(noise).max() + 1e-9))


def riser(n=1.0, level=0.45):
    x = t(n)
    noise = sweep_filter(rng.standard_normal(len(x)), 400, 9000, width=0.9)
    tone = np.sin(2 * np.pi * np.cumsum(200 * (8 ** (x / n))) / SR)
    shape = (x / n) ** 2.2
    y = noise / (np.abs(noise).max() + 1e-9) * 0.8 + tone * 0.25
    return level * y * shape


def ping(freq=1760, level=0.3):
    n = 0.6
    x = t(n)
    y = np.sin(2 * np.pi * freq * x) + 0.4 * np.sin(2 * np.pi * freq * 2.01 * x)
    return level * y * env(n, 0.002, 0.25, 4)


def shimmer(level=0.35):
    n = 1.4
    x = t(n)
    y = sum(np.sin(2 * np.pi * f * x + p) for f, p in [(1046.5, 0), (1318.5, 1), (1568, 2), (2093, 3), (2637, 4)])
    trem = 0.75 + 0.25 * np.sin(2 * np.pi * 9 * x)
    return level * y / 5 * trem * env(n, 0.03, 0.6, 3)


# ---------------------------------------------------------------------- music

def note(midi):
    return 440 * 2 ** ((midi - 69) / 12)


CHORDS = [[48, 55, 64, 67], [43, 55, 62, 67], [45, 57, 64, 69], [41, 57, 65, 69]]   # C  G  Am  F


def music():
    total = int(LENGTH * SR)
    kick_bus, hats, claps, bass, plucks, pad = (np.zeros(total) for _ in range(6))
    beats = int(13.5 / BEAT)
    kick_env = np.zeros(total)

    def put(buf, at, sig):
        i = int(at * SR)
        if i >= total:
            return
        j = min(total, i + len(sig))
        buf[i:j] += sig[: j - i]

    for b in range(beats):
        at = b * BEAT
        drums_on = 3 <= b < 15 or 18 <= b < 26      # intro, a breath at the flip to white, then the end hit
        if drums_on:
            k = thud(1.0)
            put(kick_bus, at, k)
            put(kick_env, at, np.abs(k))
            put(hats, at + BEAT / 2, tick(0.22))
            if b % 2 == 1:
                n = 0.18
                c = filt(rng.standard_normal(int(n * SR)), "bandpass", [900, 2600]) * env(n, 0.001, 0.07, 4)
                put(claps, at, 0.5 * c / (np.abs(c).max() + 1e-9))
        chord = CHORDS[(b // 4) % 4]
        # bass on eighths, root an octave down
        for half in (0, 1):
            n = BEAT / 2
            x = t(n)
            f = note(chord[0] - 12)
            saw = sum(np.sin(2 * np.pi * f * h * x) / h for h in range(1, 7))
            put(bass, at + half * n, 0.28 * filt(saw, "lowpass", 700) * env(n, 0.004, 0.2, 2))
        # plucked sixteenth arpeggio
        for s in range(4):
            n = 0.22
            x = t(n)
            f = note(chord[(s + b) % 4] + 12)
            y = (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(2 * np.pi * 2 * f * x)) * env(n, 0.002, 0.08, 5)
            put(plucks, at + s * BEAT / 4, 0.14 * y)
    # a soft pad under everything, one chord a bar
    for bar in range(int(np.ceil(beats / 4))):
        n = 4 * BEAT + 0.3
        x = t(n)
        y = sum(np.sin(2 * np.pi * note(m) * d * x) for m in CHORDS[bar % 4] for d in (0.997, 1.003))
        shape = np.minimum(1, x / 0.3) * np.minimum(1, (n - x) / 0.3)
        put(pad, bar * 4 * BEAT, 0.05 * filt(y, "lowpass", 1600) * shape)

    # Duck the bass and pad under each kick, the pumping feel of the genre.
    duck = 1 - 0.6 * np.clip(filt(kick_env, "lowpass", 12) * 3, 0, 1)
    # The intro opens up: filter the first scene so the drop at "Generic design" lands.
    intro = np.ones(total)
    intro[: int(1.5 * SR)] = np.linspace(0.35, 1, int(1.5 * SR))
    mix = kick_bus * 0.9 + hats + claps + (bass + pad) * duck + plucks * intro
    return mix


# ----------------------------------------------------------------- the cue list

def effects():
    total = int(LENGTH * SR)
    out = np.zeros(total)
    S = SCENES

    def at(sec, sig, gain=1.0):
        i = int(sec * SR)
        j = min(total, i + len(sig))
        if 0 <= i < total:
            out[i:j] += gain * sig[: j - i]

    # A whoosh into every cut, peaking on the cut itself.
    for name in ("generic", "hidden", "report", "kinds", "close"):
        at(S[name] - 0.3, whoosh(0.55))
    # 0-1.5  "Standing out is" -> "Hard." and six pills
    at(0.0, shimmer(0.18))
    at(16 * FRAME, thud(0.7))
    for i in range(6):
        at((18 + i * 2) * FRAME, pop(700 + i * 110, level=0.35))
    # 1.5-3  pedestals rise
    for i in range(3):
        at(S["generic"] + (4 + i * 4) * FRAME, whoosh(0.3, 120, 900, 0.35))
        at(S["generic"] + (4 + i * 4) * FRAME + 0.18, thud(0.45))
    # 3-5.5  map markers ping, headline swaps
    for i in range(6):
        at(S["hidden"] + (6 + i * 3) * FRAME, ping(1320 + (i % 3) * 220, 0.18))
    at(S["hidden"] + 2.5 * BEAT - 0.2, whoosh(0.4, 800, 5000, 0.35))
    # 5.5-7.5  riser into the FIG hit, panels swipe in
    at(S["fig"] - 1.0, riser(1.0))
    at(S["fig"], impact(1.0))
    for i, f in enumerate((10, 14, 18)):
        at(S["fig"] + f * FRAME, whoosh(0.28, 1500, 7000, 0.28))
    # 7.5-9  palette flips to white
    at(S["report"], shimmer(0.4))
    for f in (6, 10):
        at(S["report"] + f * FRAME, whoosh(0.35, 250, 2000, 0.3))
    # 9-11  cards cascade
    for i in range(5):
        at(S["kinds"] + (4 + i * 5) * FRAME, tick(0.4))
        at(S["kinds"] + (4 + i * 5) * FRAME, pop(1200 + i * 90, n=0.08, level=0.18))
    at(S["kinds"] + 2.6 * BEAT, pop(520, 0.15, 0.4))
    # 11-13.5  phone rises, ring fills, logo lands
    at(S["close"] + 8 * FRAME, riser(0.7, 0.3))
    at(S["close"] + 6 * FRAME, impact(0.8))
    at(S["close"] + 26 * FRAME, shimmer(0.25))
    return out


def main():
    m, fx = music(), effects()
    mix = 0.55 * m + 0.75 * fx
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)                 # gentle glue, no hard clipping
    fade = int(0.35 * SR)
    end = int(13.5 * SR)
    mix = mix[:end]
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix *= 0.89 / (np.abs(mix).max() + 1e-9)                 # about -1 dBFS
    # A touch of width: the right channel is the same mix, 12 ms late on the highs.
    highs = filt(mix, "highpass", 3000)
    shift = int(0.012 * SR)
    right = mix - highs + np.concatenate([np.zeros(shift), highs[:-shift]])
    stereo = np.stack([mix, right], axis=1)
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    out = Path(__file__).resolve().parent.parent / "public" / "reel-sound.wav"
    out.parent.mkdir(exist_ok=True)
    import wave
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print(f"wrote {out} ({len(mix) / SR:.2f}s)")


if __name__ == "__main__":
    main()
