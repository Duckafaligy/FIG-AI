import type { CSSProperties, ReactNode } from "react";
import { AbsoluteFill, Audio, Easing, Img, Sequence, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { siGithub } from "simple-icons";
import { MONO, Mark, SANS, useUnit } from "./Promo";

// A 26.4 s spot at 150 BPM (12 frames a beat). Cold-open word slams, then a
// laptop on FIG's real homepage: type launchvault.ca, scan, the layer scores,
// the generic copy caught, a real fix approved, then real FIG screens and the logo.
export const HB = 12;
const S = { slam: 0, type: 4, scan: 8, metrics: 12, score: 16, problem: 19, fix: 22, meet: 26, tour: 29, brand: 54, end: 64 };
export const HOOK_DURATION = S.end * HB;

const K = {
  bg: "#050508", ink: "#F4F5F8", copy: "#A9AEBD", muted: "#6E7385", line: "rgba(255,255,255,0.08)", card: "rgba(255,255,255,0.04)",
  craft: "#A18BFF", structure: "#38E1F0", search: "#FF9A3C", answers: "#FF4FA0", green: "#2BE38A", red: "#FF3B4E", blue: "#3D8BFF",
};
const LAYERS = [
  { name: "Craft", v: 75, c: K.craft, icon: "M4 20l4-1 11-11-3-3L5 16zM14 6l3 3" },
  { name: "Structure", v: 50, c: K.structure, icon: "M4 4h16v5H4zM4 13h7v7H4zM15 13h5v7h-5z" },
  { name: "Search", v: 81, c: K.search, icon: "M11 4a7 7 0 100 14 7 7 0 000-14zM20 20l-4-4" },
  { name: "Answers", v: 75, c: K.answers, icon: "M12 3l2 5 5 2-5 2-2 5-2-5-5-2 5-2z" },
];

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const soft = Easing.bezier(0.16, 1, 0.3, 1);
const r = (f: number, a: number, b: number, e = soft) => interpolate(f, [a, b], [0, 1], { ...clamp, easing: e });
const b = (beats: number) => beats * HB;

function useKick(at: number, stiffness = 320, damping = 12) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - at, fps, config: { damping, stiffness, mass: 0.45 } });
}

/** Tiny random camera shake that decays after each hit. */
function shake(frame: number, hits: number[], amount: number) {
  const last = hits.filter((h) => frame >= h).pop();
  if (last === undefined) return { x: 0, y: 0 };
  const k = Math.max(0, 1 - (frame - last) / 8);
  return { x: (random(`x${frame}`) - 0.5) * amount * k, y: (random(`y${frame}`) - 0.5) * amount * k };
}

/* ------------------------------------------------------------------ stage */

function Backdrop() {
  const frame = useCurrentFrame();
  const a = frame / 40;
  return <AbsoluteFill style={{ background: K.bg }}>
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at ${50 + Math.sin(a) * 12}% ${40 + Math.cos(a) * 6}%, ${K.craft}24, transparent 55%)` }} />
  </AbsoluteFill>;
}

/** Film grain and a vignette over everything: the difference between flat and filmed. */
function Grain() {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{ pointerEvents: "none" }}>
    <svg width="100%" height="100%" style={{ position: "absolute", opacity: 0.09, mixBlendMode: "overlay" }}>
      <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={frame % 12} /></filter>
      <rect width="100%" height="100%" filter="url(#grain)" />
    </svg>
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.65))" }} />
  </AbsoluteFill>;
}

/** Text with an RGB split that snaps together: the glitch look. */
function Split({ children, split, style }: { children: ReactNode; split: number; style: CSSProperties }) {
  const ghost = (color: string, dx: number): CSSProperties => ({ ...style, position: "absolute", inset: 0, color, transform: `translateX(${dx}px)`, mixBlendMode: "screen", opacity: split > 0.02 ? 1 : 0 });
  return <div style={{ position: "relative", ...style }}>
    <div style={ghost("#FF2D55", -split)}>{children}</div>
    <div style={ghost("#00E5FF", split)}>{children}</div>
    <div style={{ position: "relative" }}>{children}</div>
  </div>;
}

/* ------------------------------------------------------------------ phone */

/** Screen size of the laptop: wide on a landscape frame, narrower on a tall one. 16:10. */
function useScreen() {
  const { u, vertical } = useUnit();
  const sw = (vertical ? 860 : 1250) * u;
  return { sw, sh: sw * 0.625 };
}

/** A laptop: lid with a thin bezel and camera, and a keyboard deck. The screen sits at the frame's centre. */
function Laptop({ children, s = 1, rx = 0, ry = 0, x = 0, y = 0 }: { children: ReactNode; s?: number; rx?: number; ry?: number; x?: number; y?: number }) {
  const { u } = useUnit();
  const { sw, sh } = useScreen();
  const frame = useCurrentFrame();
  const bezel = 16 * u;
  const sheen = ((frame * 2) % 240) / 240;
  return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", perspective: 2600 * u }}>
    <div style={{ transform: `translate(${x}px, ${y}px) rotateX(${rx}deg) rotateY(${ry}deg) scale(${s})`, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div style={{ width: sw + bezel * 2, height: sh + bezel * 2, padding: bezel, boxSizing: "border-box", borderRadius: `${26 * u}px ${26 * u}px ${8 * u}px ${8 * u}px`,
        background: "linear-gradient(160deg, #3B3E47, #16171C 30%, #1C1E24)", boxShadow: `inset 0 0 0 ${1.5 * u}px rgba(255,255,255,0.18), 0 ${60 * u}px ${140 * u}px rgba(0,0,0,0.7), 0 0 ${120 * u}px ${K.craft}2A`,
        position: "relative", marginBottom: 0 }}>
        <span style={{ position: "absolute", top: 5 * u, left: "50%", width: 8 * u, height: 8 * u, marginLeft: -4 * u, borderRadius: "50%", background: "#2C2F38" }} />
        <div style={{ position: "relative", width: sw, height: sh, overflow: "hidden", borderRadius: 6 * u, background: "#07080B" }}>
          {children}
          <div style={{ position: "absolute", inset: 0, pointerEvents: "none", background: `linear-gradient(115deg, transparent ${sheen * 140 - 30}%, rgba(255,255,255,0.07) ${sheen * 140 - 15}%, transparent ${sheen * 140}%)` }} />
        </div>
      </div>
      {/* the keyboard deck, seen edge-on */}
      <div style={{ width: (sw + bezel * 2) * 1.16, height: 30 * u, borderRadius: `${4 * u}px ${4 * u}px ${22 * u}px ${22 * u}px`,
        background: "linear-gradient(180deg, #5A5E68, #2A2C33 45%, #15161B)", boxShadow: `0 ${30 * u}px ${60 * u}px rgba(0,0,0,0.6)`, position: "relative" }}>
        <span style={{ position: "absolute", top: 0, left: "50%", width: 180 * u, height: 12 * u, marginLeft: -90 * u, borderRadius: `0 0 ${10 * u}px ${10 * u}px`, background: "#1D1F25" }} />
      </div>
    </div>
  </AbsoluteFill>;
}

/** A 1440 x 900 design space that scales to fill the laptop screen: lay out in page pixels. */
function ScreenPage({ children }: { children: ReactNode }) {
  const { sw } = useScreen();
  return <div style={{ position: "absolute", left: 0, top: 0, width: 1440, height: 900, transform: `scale(${sw / 1440})`, transformOrigin: "0 0" }}>{children}</div>;
}

/** A macOS arrow that glides between points and clicks. Key points are fractions of the laptop
 *  screen (0,0 top-left) with the laptop scaled by `s` and shifted by x/y. */
function Cursor({ keys, clicks, s = 1, x = 0, y = 0 }: { keys: [number, number, number][]; clicks: number[]; s?: number; x?: number; y?: number }) {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  const { width: W, height: H } = useVideoConfig();
  const { sw, sh } = useScreen();
  let fx = keys[0][1], fy = keys[0][2];
  for (let i = 1; i < keys.length; i++) {
    const [f0, x0, y0] = keys[i - 1], [f1, x1, y1] = keys[i];
    if (frame >= f0) { const p = r(frame, f0, f1, Easing.bezier(0.6, 0, 0.15, 1)); fx = x0 + (x1 - x0) * p; fy = y0 + (y1 - y0) * p; }
  }
  const left = W / 2 + x + (fx - 0.5) * sw * s, top = H / 2 + y + (fy - 0.5) * sh * s;
  const press = clicks.some((c) => frame >= c && frame < c + 3);
  const ring = clicks.map((c) => r(frame, c, c + 10)).find((p) => p > 0 && p < 1) ?? 0;
  return <div style={{ position: "absolute", left, top, opacity: r(frame, keys[0][0] - 3, keys[0][0]), zIndex: 50 }}>
    {ring > 0 && <div style={{ position: "absolute", left: -34 * u, top: -34 * u, width: 68 * u, height: 68 * u, borderRadius: "50%", border: `${3 * u}px solid ${K.ink}`, transform: `scale(${0.3 + ring * 1.3})`, opacity: 1 - ring }} />}
    <svg width={48 * u} height={48 * u} viewBox="0 0 24 24" style={{ transform: `scale(${press ? 0.82 : 1})`, transformOrigin: "15% 10%", filter: "drop-shadow(0 6px 12px rgba(0,0,0,0.7))" }}>
      <path d="M5 2.5l13.5 11.2h-7.3l-4.1 7.8z" fill={K.ink} stroke="#000" strokeWidth="1.3" strokeLinejoin="round" />
    </svg>
  </div>;
}

const Label = ({ children, u, color = K.muted }: { children: ReactNode; u: number; color?: string }) =>
  <span style={{ fontFamily: MONO, fontSize: 15 * u, letterSpacing: "0.14em", color, textTransform: "uppercase" }}>{children}</span>;

/* ----------------------------------------------------------- screenshots */

// Full-page captures of FIG (Playwright, 2x, the app's sample workspace). Positions are page pixels.
const PAGE_W = 1425;
const SHOT = { projects: 6370, overview: 5346, seo: 3996, geo: 2394, analytics: 2230 } as const;

const SLAM = ["YOUR", "SITE", "LOOKS", "GENERIC."];
/** Four words, four different treatments, one per beat. */
function Slam() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const i = Math.min(SLAM.length - 1, Math.floor(frame / HB));
  const local = frame - i * HB;
  const pops = [useKick(0, 420, 11), useKick(HB, 420, 11), useKick(2 * HB, 420, 11), useKick(3 * HB, 420, 11)];
  const p = pops[i];
  const sh = shake(frame, [0, HB, 2 * HB, 3 * HB], 26 * u);
  const big: CSSProperties = { fontFamily: SANS, fontWeight: 900, letterSpacing: "-0.06em", lineHeight: 1 };
  let body: ReactNode = null;
  if (i === 0) {
    // Out of the dark: zooms from far too big down to size.
    body = <Split split={Math.max(0, 14 - local * 2.5) * u} style={{ ...big, fontSize: (vertical ? 250 : 300) * u, color: K.ink, transform: `scale(${3 - p * 2})`, opacity: Math.min(1, p * 3), filter: `blur(${(1 - p) * 10}px)` }}>YOUR</Split>;
  } else if (i === 1) {
    // A white flash with black type, knocked off-angle.
    body = <>
      <AbsoluteFill style={{ background: K.ink, opacity: 1 - local / (HB * 1.6) }} />
      <div style={{ ...big, fontSize: (vertical ? 270 : 330) * u, color: "#050508", transform: `rotate(${-6 + p * 3}deg) scale(${1.6 - p * 0.6})`, opacity: Math.min(1, p * 3) }}>SITE</div>
    </>;
  } else if (i === 2) {
    // An echo stack of outlines, the middle one filled.
    body = <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      {[-2, -1, 0, 1, 2].map((k) => <div key={k} style={{ ...big, fontSize: (vertical ? 190 : 220) * u, lineHeight: 0.92,
        color: k === 0 ? K.ink : "transparent", WebkitTextStroke: k === 0 ? undefined : `${2.5 * u}px ${Math.abs(k) === 1 ? K.craft : K.structure}`,
        transform: `translateY(${k * (1 - p) * 60 * u}px) scale(${1 - Math.abs(k) * 0.04})`, opacity: k === 0 ? Math.min(1, p * 3) : p * (1 - Math.abs(k) * 0.3) }}>LOOKS</div>)}
    </div>;
  } else {
    // Torn into horizontal red slices that snap back together.
    const slices = 6, h = (vertical ? 165 : 260) * u;
    body = <>
      <AbsoluteFill style={{ background: `radial-gradient(circle, ${K.red}66, transparent 62%)`, opacity: 1 - local / (HB * 1.4) }} />
      <div style={{ position: "relative", height: h }}>
        <div style={{ ...big, fontSize: h, color: "transparent" }}>GENERIC.</div>
        {Array.from({ length: slices }, (_, k) => {
          const off = (random(`s${k}${Math.floor(local / 2)}`) - 0.5) * 160 * u * Math.max(0, 1 - local / 9);
          return <div key={k} style={{ position: "absolute", inset: 0, ...big, fontSize: h, color: k % 2 ? K.red : "#FF6B78",
            clipPath: `inset(${(k / slices) * 100}% 0 ${(1 - (k + 1) / slices) * 100}% 0)`, transform: `translateX(${off}px) scale(${1.25 - p * 0.25})`, opacity: Math.min(1, p * 3) }}>GENERIC.</div>;
        })}
      </div>
    </>;
  }
  return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", transform: `translate(${sh.x}px, ${sh.y}px)` }}>{body}</AbsoluteFill>;
}

const URL = "launchvault.ca";
// FIG's homepage form, in page pixels (captured with Playwright).
const HOME_INPUT = [48, 596, 350, 52], HOME_BUTTON = [398, 596, 140, 52];
/** Starts close on FIG's real homepage form, types the URL, then pulls back to the whole laptop. */
function TypeScene() {
  const frame = useCurrentFrame();
  const { sw, sh } = useScreen();
  const typed = Math.max(0, Math.min(URL.length, Math.floor((frame - 4) / 1.6)));
  const clicked = frame >= 38;
  const pull = r(frame, 20, 32, Easing.inOut(Easing.cubic));
  const s = 2.5 - pull * 1.6;                                    // 2.5x on the form, then 0.9x the laptop
  const fx = (HOME_INPUT[0] + HOME_BUTTON[0] + HOME_BUTTON[2]) / 2 / 1440, fy = (HOME_INPUT[1] + 26) / 900;
  const tx = -(fx - 0.5) * sw * s * (1 - pull), ty = -(fy - 0.5) * sh * s * (1 - pull);
  const [ix, iy, iw, ih] = HOME_INPUT, [bx, by, bw, bh] = HOME_BUTTON;
  return <>
    <Laptop s={s} x={tx} y={ty} rx={pull * 6}>
      <Img src={staticFile("shots/home-top.png")} style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }} />
      <ScreenPage>
        <div style={{ position: "absolute", left: ix, top: iy, width: iw, height: ih, boxSizing: "border-box", display: "flex", alignItems: "center", padding: "0 16px",
          background: "#0A0C0A", border: `2px solid ${K.green}`, borderRadius: 8, boxShadow: `0 0 0 4px ${K.green}33`, fontFamily: SANS, fontSize: 18, color: K.ink }}>
          {URL.slice(0, typed)}<span style={{ width: 2, height: 22, marginLeft: 2, background: K.green, opacity: Math.floor(frame / 5) % 2 ? 1 : 0 }} />
        </div>
        <div style={{ position: "absolute", left: bx, top: by, width: bw, height: bh, borderRadius: 8, background: "#fff", opacity: clicked ? 0.35 * (1 - r(frame, 38, 46)) : 0 }} />
      </ScreenPage>
    </Laptop>
    <Cursor s={s} x={tx} y={ty} keys={[[26, 0.62, 0.95], [36, (bx + bw / 2) / 1440, (by + bh / 2) / 900]]} clicks={[38]} />
  </>;
}

const PAGES = ["/", "/how-it-works", "/features", "/about", "/learn-ai", "/blog"];
/** The laptop tips back and the pages fly up out of its screen into a floating grid. */
function ScanScene() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const tip = r(frame, 0, 10);
  const pops = PAGES.map((_, i) => useKick(4 + i * 4, 240, 14));
  const checks = PAGES.map((_, i) => useKick(14 + i * 5, 400, 12));
  const count = Math.round(40 * r(frame, 8, 40, Easing.out(Easing.quad)));
  const cols = vertical ? 2 : 3;
  const cw = (vertical ? 400 : 380) * u, ch = 240 * u, gap = 28 * u;
  const gridW = cols * cw + (cols - 1) * gap;
  const gx = (width - gridW) / 2, gy = height * (vertical ? 0.2 : 0.16);
  const laser = (frame * 6) % 100;
  return <>
    <Laptop rx={tip * 58} s={0.8} y={tip * (vertical ? 640 : 380) * u}>
      <div style={{ position: "absolute", inset: 0, background: `radial-gradient(circle at 50% 40%, ${K.structure}66, #07080B 70%)` }} />
    </Laptop>
    <div style={{ position: "absolute", left: 0, right: 0, top: height * (vertical ? 0.08 : 0.04), textAlign: "center", fontFamily: MONO, fontSize: 88 * u, fontWeight: 700, color: K.ink }}>
      {count}<span style={{ color: K.muted, fontSize: 44 * u }}> PAGES</span></div>
    {PAGES.map((p, i) => {
      const k = pops[i];
      const col = i % cols, row = Math.floor(i / cols);
      const tx = gx + col * (cw + gap), ty = gy + row * (ch + gap) + (vertical ? 60 : 70) * u;
      const fromX = width / 2 - cw / 2, fromY = height * (vertical ? 0.78 : 0.82);
      const done = frame >= 14 + i * 5;
      const c = LAYERS[i % 4].c;
      return <div key={p} style={{ position: "absolute", left: fromX + (tx - fromX) * k, top: fromY + (ty - fromY) * k, width: cw, height: ch, borderRadius: 20 * u, overflow: "hidden",
        background: "linear-gradient(160deg, rgba(30,32,44,0.95), rgba(12,13,20,0.95))", border: `${1.5 * u}px solid ${done ? K.green : c + "88"}`,
        boxShadow: `0 ${20 * u}px ${50 * u}px rgba(0,0,0,0.6), 0 0 ${30 * u}px ${done ? K.green + "55" : c + "33"}`, opacity: Math.min(1, k * 2),
        transform: `scale(${0.3 + k * 0.7}) rotate(${(1 - k) * (i % 2 ? 20 : -20)}deg)`, padding: 16 * u, boxSizing: "border-box" }}>
        <div style={{ height: 12 * u, width: "40%", background: "rgba(255,255,255,0.2)", borderRadius: 4 * u }} />
        <div style={{ height: 80 * u, marginTop: 12 * u, borderRadius: 10 * u, background: `linear-gradient(120deg, ${c}88, transparent)` }} />
        <div style={{ height: 10 * u, width: "80%", marginTop: 12 * u, background: "rgba(255,255,255,0.12)", borderRadius: 4 * u }} />
        <span style={{ position: "absolute", left: 16 * u, bottom: 14 * u, fontFamily: MONO, fontSize: 22 * u, color: K.copy }}>{p}</span>
        {!done && <div style={{ position: "absolute", left: 0, right: 0, top: `${laser}%`, height: 3 * u, background: K.structure, boxShadow: `0 0 ${18 * u}px ${K.structure}` }} />}
        {done && <span style={{ position: "absolute", right: 14 * u, bottom: 12 * u, width: 40 * u, height: 40 * u, borderRadius: "50%", background: K.green, display: "grid", placeItems: "center",
          transform: `scale(${checks[i]})`, color: "#05110A", fontSize: 24 * u, fontWeight: 900 }}>✓</span>}
      </div>;
    })}
  </>;
}

/** Slides in from one side with a motion blur, then settles. */
function useEnter(at: number, from: "left" | "right" | "top" | "bottom", dist = 260) {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  const p = r(frame, at, at + 9, Easing.bezier(0.2, 0.9, 0.25, 1));
  const d = (1 - p) * dist * u;
  const [x, y] = from === "left" ? [-d, 0] : from === "right" ? [d, 0] : from === "top" ? [0, -d] : [0, d];
  const blurX = from === "left" || from === "right";
  return { opacity: Math.min(1, p * 1.6), transform: `translate(${x}px, ${y}px)`, filter: `blur(${(1 - p) * (blurX ? 12 : 8)}px)` } as CSSProperties;
}

/** A clean horizontal bar chart: one row per layer, sliding in from alternating sides. */
function Levels() {
  const { u: base, vertical } = useUnit();
  const u = base * (vertical ? 1.22 : 1);             // a tall frame has room for a bigger chart
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const title = useEnter(0, "top", 120);
  const rows = LAYERS.map((_, i) => useEnter(3 + i * 4, i % 2 ? "right" : "left", 420));
  const pump = Math.exp(-((frame % HB) / 3));
  const chartW = Math.min(width * (vertical ? 0.9 : 0.62), 1300 * u);
  const labelW = (vertical ? 250 : 280) * u, valueW = 120 * u;
  const trackW = chartW - labelW - valueW;
  return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: (vertical ? 70 : 54) * u }}>
    <div style={{ ...title, textAlign: "center" }}>
      <div style={{ fontFamily: SANS, fontSize: (vertical ? 78 : 70) * u, fontWeight: 800, letterSpacing: "-0.04em", color: K.ink }}>launchvault.ca</div>
      <Label u={u * 1.7} color={K.copy}>Score by layer</Label>
    </div>
    <div style={{ position: "relative", width: chartW, display: "flex", flexDirection: "column", gap: (vertical ? 56 : 40) * u }}>
      {/* quiet gridlines at 25 / 50 / 75 */}
      {[25, 50, 75].map((g) => <div key={g} style={{ position: "absolute", left: labelW + (g / 100) * trackW, top: -20 * u, bottom: -20 * u, width: 1.5 * u, background: "rgba(255,255,255,0.07)" }} />)}
      {LAYERS.map((l, i) => {
        const grow = r(frame, 6 + i * 4, 20 + i * 4, Easing.out(Easing.cubic));
        const n = Math.round(l.v * grow);
        return <div key={l.name} style={{ ...rows[i], display: "flex", alignItems: "center" }}>
          <div style={{ width: labelW, display: "flex", alignItems: "center", gap: 14 * u }}>
            <span style={{ width: 52 * u, height: 52 * u, borderRadius: 14 * u, background: `${l.c}22`, border: `${1.5 * u}px solid ${l.c}66`, display: "grid", placeItems: "center" }}>
              <svg width={28 * u} height={28 * u} viewBox="0 0 24 24"><path d={l.icon} fill="none" stroke={l.c} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" /></svg></span>
            <span style={{ fontFamily: SANS, fontSize: 36 * u, fontWeight: 700, color: K.ink }}>{l.name}</span>
          </div>
          <div style={{ position: "relative", width: trackW, height: 34 * u, borderRadius: 999, background: "rgba(255,255,255,0.06)" }}>
            <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${l.v * grow}%`, borderRadius: 999,
              background: `linear-gradient(90deg, ${l.c}55, ${l.c})`, boxShadow: `0 0 ${(24 + pump * 20) * u}px ${l.c}${pump > 0.5 ? "AA" : "66"}` }}>
              <span style={{ position: "absolute", right: 5 * u, top: 5 * u, width: 24 * u, height: 24 * u, borderRadius: "50%", background: K.ink, boxShadow: `0 0 ${14 * u}px ${l.c}` }} />
            </div>
          </div>
          <span style={{ width: valueW, textAlign: "right", fontFamily: MONO, fontSize: 52 * u, fontWeight: 700, color: K.ink }}>{n}</span>
        </div>;
      })}
    </div>
  </AbsoluteFill>;
}

/** The overall score drops in from the top and lands with a shockwave. */
function ScoreBurst() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const num = useKick(2, 340, 12);
  const ring = r(frame, 8, 24);
  const sh = shake(frame, [8], 10 * u);
  const sub = useEnter(12, "bottom", 120);
  return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", transform: `translate(${sh.x}px, ${sh.y}px)` }}>
    <div style={{ position: "absolute", width: 1000 * u * ring, height: 1000 * u * ring, borderRadius: "50%", border: `${5 * u}px solid ${K.structure}`, opacity: (1 - ring) * 0.7 }} />
    <div style={{ fontFamily: SANS, fontSize: (vertical ? 440 : 460) * u, fontWeight: 900, letterSpacing: "-0.07em", lineHeight: 0.9, transform: `translateY(${(1 - num) * -700 * u}px)`,
      background: `linear-gradient(135deg, ${K.craft}, ${K.structure} 45%, ${K.search} 75%, ${K.answers})`, WebkitBackgroundClip: "text", color: "transparent",
      filter: `drop-shadow(0 0 ${40 * u}px ${K.structure}66)`, padding: "0 0.08em" }}>70</div>
    <div style={{ ...sub, display: "flex", flexDirection: "column", alignItems: "center", gap: 10 * u, marginTop: 10 * u }}>
      <Label u={u * 2} color={K.copy}>Site score · out of 100</Label>
      <span style={{ fontFamily: SANS, fontSize: 34 * u, fontWeight: 600, color: K.muted }}>40 pages read · 10 things to fix</span>
    </div>
  </AbsoluteFill>;
}

// Real phrases from app/rules/checks.py:GENERIC_COPY_PHRASES; the last is LaunchVault's own headline.
const CLICHES = ["Elevate your workflow", "Unlock the power of AI", "Supercharge your prompts"];
/** One cliche a beat: it lands, a marker scribbles it out, the words sag and grey, and a GENERIC stamp thuds on. */
function Cliches() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const i = Math.min(CLICHES.length - 1, Math.floor(frame / HB));
  const local = frame - i * HB;
  const enters = CLICHES.map((_, k) => useEnter(k * HB, k % 2 ? "right" : "left", 700));
  const stamps = CLICHES.map((_, k) => useKick(k * HB + 6, 520, 10));
  const scribble = r(local, 3, 8, Easing.inOut(Easing.quad));
  const dead = r(local, 6, 11);
  const sh = shake(frame, CLICHES.map((_, k) => k * HB + 6), 8 * u);
  const last = i === CLICHES.length - 1;
  const size = (vertical ? 118 : 132) * u;
  const words = CLICHES[i].split(" ");
  const chip = useEnter(2 * HB + 8, "bottom", 80);
  // A marker scribble: a tight zigzag across the words, drawn left to right.
  const W = 1000, H = 160;
  const zig = Array.from({ length: 9 }, (_, k) => {
    const x = 40 + (k / 8) * (W - 80), up = k % 2 === 0;
    const y = up ? H * (0.22 + random(`a${i}${k}`) * 0.12) : H * (0.7 + random(`b${i}${k}`) * 0.12);
    return k === 0 ? `M ${x} ${y}` : `Q ${x - (W / 16)} ${up ? y - 30 : y + 30} ${x} ${y}`;
  }).join(" ");
  return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", transform: `translate(${sh.x}px, ${sh.y}px)` }}>
    <AbsoluteFill style={{ background: `radial-gradient(circle, ${K.red}${last ? "44" : "26"}, transparent 65%)`, opacity: 0.4 + dead * 0.6 }} />
    <div style={{ ...enters[i], position: "relative", padding: `0 ${60 * u}px`, textAlign: "center" }}>
      <div style={{ fontFamily: SANS, fontSize: size, fontWeight: 900, letterSpacing: "-0.05em", lineHeight: 1.02 }}>
        {words.map((w, k) => <span key={k} style={{ display: "inline-block", marginRight: "0.25em",
          color: dead > 0.5 ? K.muted : K.ink, transform: `translateY(${dead * (10 + (k % 3) * 14) * u}px) rotate(${dead * (k % 2 ? 4 : -3)}deg)`, opacity: 1 - dead * 0.35 }}>{w}</span>)}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ position: "absolute", left: 90 * u, top: "16%", width: `calc(100% - ${180 * u}px)`, height: "68%", overflow: "visible" }}>
        <path d={zig} fill="none" stroke={K.red} strokeWidth={14} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={`${scribble} 1`}
          style={{ filter: `drop-shadow(0 0 10px ${K.red})` }} vectorEffect="non-scaling-stroke" />
      </svg>
      <div style={{ position: "absolute", right: 10 * u, top: -70 * u, padding: `${10 * u}px ${24 * u}px`, border: `${6 * u}px solid ${K.red}`, borderRadius: 14 * u,
        fontFamily: SANS, fontSize: 58 * u, fontWeight: 900, letterSpacing: "0.04em", color: K.red, background: "rgba(10,2,4,0.6)",
        transform: `rotate(-12deg) scale(${2.6 - stamps[i] * 1.6})`, opacity: Math.min(1, stamps[i] * 3) }}>GENERIC</div>
    </div>
    {last && <div style={{ ...chip, position: "absolute", bottom: vertical ? "24%" : "16%", display: "flex", alignItems: "center", gap: 12 * u,
      padding: `${14 * u}px ${28 * u}px`, borderRadius: 999, background: K.red }}>
      <span style={{ fontFamily: MONO, fontSize: 30 * u, fontWeight: 800, color: K.ink }}>FOUND ON LAUNCHVAULT.CA · 13 PAGES</span>
    </div>}
  </AbsoluteFill>;
}

// A real, mechanical LaunchVault finding: /features' title is 74 characters. FIG's suggested
// fix is from the scan (Test Runs.md, Test #1). On a GitHub-deployed site, approving opens a PR.
const OLD_TITLE = "AI Learning Platform Features — Prompts, Courses & AI Agents | LaunchVault";
const NEW_TITLE = "AI Learning Platform Features | LaunchVault";
const APPROVE_BOX = [1150, 640, 170, 52];                              // page pixels in the 1440 x 900 screen
const RAIL = ["Overview", "SEO", "GEO", "Analytics", "Publish", "History", "Settings"];
/** FIG's publish screen on the laptop: the fix types in, the cursor approves it, a pull request opens. */
function FixScene() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const inn = useKick(0, 220, 15);
  const typedN = Math.max(0, Math.min(NEW_TITLE.length, Math.floor((frame - 4) / 0.6)));
  const approveAt = 32, sent = frame >= approveAt + 2;
  const toast = useKick(approveAt + 3, 420, 12);
  const sh = { x: 0, y: 0 };
  const s = (vertical ? 1.12 : 1) * (0.86 + inn * 0.14);
  const [ax, ay, aw, ah] = APPROVE_BOX;
  return <AbsoluteFill style={{ transform: `translate(${sh.x}px, ${sh.y}px)` }}>
    <Laptop s={s} rx={(1 - inn) * 24} ry={-4}>
      <ScreenPage>
        <div style={{ position: "absolute", inset: 0, background: "#0A0B09", fontFamily: SANS }}>
          {/* the project rail */}
          <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 232, background: "#0C0D0B", borderRight: "1px solid #1D2119", padding: "26px 16px", boxSizing: "border-box" }}>
            <div style={{ fontSize: 26, fontWeight: 900, color: K.ink, letterSpacing: "-0.04em" }}>FIG</div>
            <div style={{ marginTop: 26, padding: 14, border: "1px solid #24301F", borderLeft: `3px solid ${K.green}`, background: "#111310" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 15, fontWeight: 700, color: K.ink }}>LaunchVault<span style={{ color: K.green, fontFamily: MONO }}>70</span></div>
              <div style={{ fontFamily: MONO, fontSize: 12, color: "#8F968A", marginTop: 4 }}>launchvault.ca</div>
            </div>
            <div style={{ marginTop: 22, display: "flex", flexDirection: "column", gap: 4 }}>
              {RAIL.map((n) => <div key={n} style={{ padding: "9px 12px", fontSize: 14, fontWeight: 600, color: n === "Publish" ? K.ink : "#8F968A",
                background: n === "Publish" ? "#12301F" : "transparent", borderLeft: n === "Publish" ? `3px solid ${K.green}` : "3px solid transparent", display: "flex", justifyContent: "space-between" }}>
                {n}{n === "Publish" && !sent && <span style={{ fontFamily: MONO, fontSize: 12, color: "#0A0B09", background: K.search, padding: "0 6px" }}>1</span>}</div>)}
            </div>
          </div>
          {/* the page */}
          <div style={{ position: "absolute", left: 264, top: 40, right: 48 }}>
            <div style={{ fontFamily: MONO, fontSize: 12, letterSpacing: "0.16em", color: K.green }}>● LAUNCHVAULT · PUBLISH</div>
            <div style={{ fontSize: 40, fontWeight: 800, letterSpacing: "-0.04em", color: K.ink, marginTop: 10 }}>{sent ? "Sent. Merge it when you're ready." : "One change is waiting for you."}</div>
            <div style={{ fontSize: 16, color: "#AEB6A7", marginTop: 8 }}>FIG proposes the change and keeps the old text. You approve it; it goes out as a GitHub pull request.</div>
          </div>
          <div style={{ position: "absolute", left: 264, top: 220, right: 48, height: 500, boxSizing: "border-box", padding: 28, background: "#111310",
            border: `1px solid ${sent ? K.green : "#4A3A14"}`, borderLeft: `3px solid ${sent ? K.green : K.search}` }}>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <span style={{ fontFamily: MONO, fontSize: 12, fontWeight: 700, padding: "3px 9px", background: sent ? "#12301F" : "#3A2A0C", color: sent ? K.green : K.search }}>{sent ? "PR OPENED" : "PROPOSED"}</span>
              <span style={{ fontFamily: MONO, fontSize: 12, fontWeight: 700, padding: "3px 9px", background: "#3A2A0C", color: K.search }}>SEARCH</span>
              <span style={{ fontSize: 20, fontWeight: 700, color: K.ink, marginLeft: 8 }}>Page title is 74 characters</span>
              <span style={{ fontFamily: MONO, fontSize: 14, color: "#8F968A", marginLeft: "auto" }}>/features</span>
            </div>
            <div style={{ marginTop: 22, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              <div style={{ padding: 18, background: "#1A1210", border: "1px solid #3A1F19" }}>
                <div style={{ fontFamily: MONO, fontSize: 12, letterSpacing: "0.1em", color: "#F0A08F" }}>NOW · 74 CHARACTERS</div>
                <div style={{ fontSize: 19, color: "#F3F5EF", marginTop: 10, lineHeight: 1.35 }}>{OLD_TITLE}</div>
              </div>
              <div style={{ padding: 18, background: "#0F1A12", border: "1px solid #1F6B40" }}>
                <div style={{ fontFamily: MONO, fontSize: 12, letterSpacing: "0.1em", color: "#6FE0A2" }}>AFTER · {typedN} CHARACTERS</div>
                <div style={{ fontSize: 19, color: "#F3F5EF", marginTop: 10, lineHeight: 1.35 }}>{NEW_TITLE.slice(0, typedN)}{typedN < NEW_TITLE.length && <span style={{ display: "inline-block", width: 2, height: 20, background: K.green, marginLeft: 2, verticalAlign: "middle" }} />}</div>
              </div>
            </div>
            <div style={{ marginTop: 20, fontSize: 15, color: "#AEB6A7" }}>Why: past 60 characters, search results cut the title off and hide “LaunchVault”.</div>
          </div>
          <div style={{ position: "absolute", left: ax - 130, top: ay, width: 116, height: ah, display: "grid", placeItems: "center", fontSize: 16, fontWeight: 700, color: "#AEB6A7", border: "1px solid #2A2F24" }}>Reject</div>
          <div style={{ position: "absolute", left: ax, top: ay, width: aw, height: ah, display: "grid", placeItems: "center", fontSize: 16, fontWeight: 800,
            color: "#06110A", background: sent ? K.ink : K.green, transform: `scale(${frame >= approveAt && frame < approveAt + 3 ? 0.94 : 1})` }}>{sent ? "✓ Sent" : "Approve"}</div>
        </div>
      </ScreenPage>
    </Laptop>
    {sent && <div style={{ position: "absolute", left: "50%", top: vertical ? "22%" : "9%", transform: `translate(-50%,-50%) scale(${(2 - toast) * (vertical ? 1 : 0.8)})`, opacity: Math.min(1, toast * 2),
      display: "flex", alignItems: "center", gap: 18 * u, padding: `${18 * u}px ${34 * u}px`, borderRadius: 999, background: K.green, boxShadow: `0 0 ${60 * u}px ${K.green}` }}>
      <Mark icon={siGithub} size={46 * u} fill="#05110A" />
      <span style={{ fontFamily: SANS, fontSize: 52 * u, fontWeight: 900, color: "#05110A", letterSpacing: "-0.03em", whiteSpace: "nowrap" }}>Pull request opened</span>
    </div>}
    <Cursor s={s} keys={[[10, 0.95, 0.95], [approveAt - 2, (ax + aw / 2) / 1440, (ay + ah / 2) / 900]]} clicks={[approveAt]} />
  </AbsoluteFill>;
}

/* ------------------------------------------------------- the product */

function Meet() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const p = r(frame, 0, 12, Easing.bezier(0.16, 1, 0.3, 1));
  return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
    <div style={{ fontFamily: SANS, fontSize: (vertical ? 190 : 220) * u, fontWeight: 900, letterSpacing: "-0.06em", lineHeight: 1, color: K.ink,
      opacity: p, transform: `translateY(${(1 - p) * 30 * u}px) scale(${0.97 + p * 0.03})` }}>Meet FIG<span style={{ color: K.green }}>.</span></div>
  </AbsoluteFill>;
}

/* ------------------------------------------------------ the product tour */

// One browser window stays on screen; the cursor uses FIG the way a person would.
// Page coordinates are from the Playwright captures (1425 px wide pages).
type Rect = [number, number, number, number];
const TOUR: { file: keyof typeof SHOT; path: string; from: number; focus: Rect[]; caption: [string, string]; c: string }[] = [
  { file: "projects", path: "projects", from: 0, focus: [[0, 0, 1425, 900]], caption: ["Every site.", "One place."], c: K.craft },
  { file: "overview", path: "projects/harborlinedental.com", from: 54, focus: [[0, 60, 1425, 820], [240, 520, 820, 560]], caption: ["Every finding,", "explained."], c: K.structure },
  { file: "seo", path: "projects/harborlinedental.com/seo", from: 126, focus: [[240, 90, 1170, 620]], caption: ["Search,", "tracked."], c: K.search },
  { file: "geo", path: "projects/harborlinedental.com/geo", from: 186, focus: [[240, 90, 1170, 560]], caption: ["Ready for", "AI answers."], c: K.answers },
  { file: "analytics", path: "projects/harborlinedental.com/analytics", from: 246, focus: [[240, 90, 1170, 620]], caption: ["See what's", "working."], c: K.green },
];
export const TOUR_LEN = 300;
// Where the cursor goes and clicks before each page change (page pixels on the page being left).
const CLICKS: { at: number; x: number; y: number }[] = [
  { at: 46, x: 700, y: 713 },            // the Harborline Dental row on the projects list
  { at: 118, x: 85, y: 313 },            // SEO in the project rail
  { at: 178, x: 85, y: 351 },            // GEO
  { at: 238, x: 85, y: 389 },            // Analytics
];

function Tour() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const fw = (vertical ? 880 : 1240) * u, fh = vertical ? fw * 1.15 : fw * 0.56;
  const capGap = (vertical ? 110 : 44) * u, capH = (vertical ? 180 : 80) * u;
  const top = (height - (fh + 50 * u + capGap + capH)) / 2;        // window and caption, centred together
  const left = (width - fw) / 2;
  let i = TOUR.length - 1;
  while (i > 0 && frame < TOUR[i].from) i--;
  const page = TOUR[i];
  const local = frame - page.from;
  const end = i + 1 < TOUR.length ? TOUR[i + 1].from : TOUR_LEN;
  // The camera: fit the focus rect (a tall frame crops in further), easing between rects within a page.
  const stops = page.focus.map(([x, y, w, h]): Rect => vertical ? [x + 20, y, w * 0.66, h] : [x, y, w, h]);
  const seg = stops.length > 1 ? r(local, (end - page.from) * 0.4, (end - page.from) * 0.7, Easing.inOut(Easing.cubic)) : 0;
  const [cx, cy, cw, ch] = stops.length > 1 ? stops[0].map((v, k) => v + (stops[1][k] - v) * seg) as Rect : stops[0];
  const k = Math.min(fw / cw, fh / ch);
  const camX = cx + cw / 2 - fw / 2 / k, camY = cy + ch / 2 - fh / 2 / k;
  const fade = r(local, 0, 8);                                  // a page change is a quick crossfade, like real navigation
  const prev = i > 0 ? TOUR[i - 1] : null;
  const win = r(frame, 0, 14);
  const capIn = r(local, 4, 16), capOut = r(frame, end - 8, end);
  // The cursor: glides to the next click target, presses, and the page changes.
  const next = CLICKS.find((c) => c.at > frame - 10 && c.at >= page.from && c.at < end) ?? null;
  const target = next ? { x: (next.x - camX) * k, y: (next.y - camY) * k } : null;
  const cur = target && target.x > 0 ? target : null;               // a cropped-in tall frame can't see the rail; no cursor then
  const arrive = next ? r(frame, next.at - 22, next.at - 2, Easing.bezier(0.45, 0, 0.2, 1)) : 0;
  const start = { x: fw * 0.72, y: fh * 0.85 };
  const pressed = next && frame >= next.at && frame < next.at + 4;
  const ring = next ? r(frame, next.at, next.at + 12) : 0;
  return <AbsoluteFill>
    <div style={{ position: "absolute", left, top, width: fw, borderRadius: 18 * u, overflow: "hidden", background: "#0A0B09",
      border: `${1.5 * u}px solid rgba(255,255,255,0.12)`, boxShadow: `0 ${40 * u}px ${110 * u}px rgba(0,0,0,0.6)`,
      opacity: win, transform: `translateY(${(1 - win) * 40 * u}px)` }}>
      <div style={{ height: 50 * u, display: "flex", alignItems: "center", gap: 9 * u, padding: `0 ${18 * u}px`, background: "#15161B", borderBottom: `${1.5 * u}px solid rgba(255,255,255,0.07)` }}>
        {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => <span key={c} style={{ width: 14 * u, height: 14 * u, borderRadius: "50%", background: c }} />)}
        <div style={{ flex: 1, marginLeft: 14 * u, height: 30 * u, borderRadius: 9 * u, background: "rgba(255,255,255,0.06)", display: "flex", alignItems: "center", padding: `0 ${14 * u}px`,
          fontFamily: MONO, fontSize: 17 * u, color: K.copy, whiteSpace: "nowrap", overflow: "hidden" }}>fig-ai-seven.vercel.app/{page.path}</div>
      </div>
      <div style={{ position: "relative", height: fh, overflow: "hidden" }}>
        {prev && local < 8 && <Img src={staticFile(`shots/${prev.file}.png`)} style={{ position: "absolute", left: -camX * k, top: -camY * k, width: PAGE_W * k, height: (SHOT[prev.file] / 2) * k }} />}
        <Img src={staticFile(`shots/${page.file}.png`)} style={{ position: "absolute", left: -camX * k, top: -camY * k, width: PAGE_W * k, height: (SHOT[page.file] / 2) * k,
          opacity: i === 0 ? 1 : fade, filter: "brightness(1.12)" }} />
        {cur && <div style={{ position: "absolute", left: start.x + (cur.x - start.x) * arrive, top: start.y + (cur.y - start.y) * arrive, zIndex: 5 }}>
          {ring > 0 && ring < 1 && <div style={{ position: "absolute", left: -28 * u, top: -28 * u, width: 56 * u, height: 56 * u, borderRadius: "50%", border: `${2.5 * u}px solid ${K.ink}`,
            transform: `scale(${0.4 + ring})`, opacity: 1 - ring }} />}
          <svg width={40 * u} height={40 * u} viewBox="0 0 24 24" style={{ transform: `scale(${pressed ? 0.85 : 1})`, transformOrigin: "15% 10%", filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.6))" }}>
            <path d="M5 2.5l13.5 11.2h-7.3l-4.1 7.8z" fill={K.ink} stroke="#000" strokeWidth="1.3" strokeLinejoin="round" /></svg>
        </div>}
      </div>
    </div>
    <div style={{ position: "absolute", left: 0, right: 0, top: top + fh + 50 * u + capGap, textAlign: "center", fontFamily: SANS, fontSize: (vertical ? 84 : 70) * u, fontWeight: 800,
      letterSpacing: "-0.045em", lineHeight: 1.05, padding: `0 ${50 * u}px`, opacity: capIn * (1 - capOut), transform: `translateY(${(1 - capIn) * 16 * u}px)` }}>
      <span style={{ color: K.ink }}>{page.caption[0]}</span> <span style={{ color: page.c }}>{page.caption[1]}</span>
    </div>
  </AbsoluteFill>;
}

/** The ending: one calm beat. The logo rises in, the line under it follows. */
function Brand() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const logo = r(frame, 4, 22, Easing.bezier(0.16, 1, 0.3, 1));
  const t1 = r(frame, 18, 32), t2 = r(frame, 26, 40), t3 = r(frame, 38, 52);
  const glow = r(frame, 0, 40);
  const rise = (p: number, d = 18): CSSProperties => ({ opacity: p, transform: `translateY(${(1 - p) * d * u}px)` });
  return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 24 * u }}>
    <div style={{ position: "absolute", width: 1100 * u, height: 420 * u, borderRadius: "50%", filter: "blur(120px)", opacity: glow * 0.35,
      background: `linear-gradient(90deg, ${K.craft}, ${K.structure}, ${K.green}, ${K.answers})` }} />
    <div style={{ ...rise(logo, 30), fontFamily: SANS, fontSize: (vertical ? 260 : 300) * u, fontWeight: 900, letterSpacing: "-0.065em", color: K.ink, lineHeight: 0.9,
      transform: `translateY(${(1 - logo) * 30 * u}px) scale(${0.96 + logo * 0.04})` }}>FIG<span style={{ color: K.green }}>.</span></div>
    <div style={{ textAlign: "center", fontFamily: SANS, fontSize: (vertical ? 54 : 58) * u, fontWeight: 700, letterSpacing: "-0.03em", lineHeight: 1.2, padding: `0 ${50 * u}px` }}>
      <div style={{ ...rise(t1), color: K.copy }}>See what makes your site generic.</div>
      <div style={{ ...rise(t2), color: K.green }}>Then fix it.</div>
    </div>
    <div style={{ ...rise(t3, 10), fontFamily: MONO, fontSize: 22 * u, letterSpacing: "0.16em", color: K.muted, textAlign: "center", padding: `0 ${50 * u}px` }}>CRAFT · STRUCTURE · SEARCH · AI ANSWERS</div>
  </AbsoluteFill>;
}

function Cut({ from, to, last = false, children }: { from: number; to: number; last?: boolean; children: ReactNode }) {
  return <Sequence from={b(from)} durationInFrames={b(to - from)}><CutInner len={b(to - from)} last={last}>{children}</CutInner></Sequence>;
}
/** A short crossfade between scenes. */
function CutInner({ len, last, children }: { len: number; last: boolean; children: ReactNode }) {
  const frame = useCurrentFrame();
  const inn = r(frame, 0, 6), out = last ? 0 : r(frame, len - 5, len, Easing.in(Easing.quad));
  return <AbsoluteFill style={{ opacity: inn * (1 - out), transform: `scale(${1.02 - inn * 0.02 + out * 0.02})` }}>{children}</AbsoluteFill>;
}

export const Hook = ({ sound = true }: { sound?: boolean }) => <AbsoluteFill>
  {sound && <Audio src={staticFile("hook-sound.wav")} />}
  <Backdrop />
  <Cut from={S.slam} to={S.type}><Slam /></Cut>
  <Cut from={S.type} to={S.scan}><TypeScene /></Cut>
  <Cut from={S.scan} to={S.metrics}><ScanScene /></Cut>
  <Cut from={S.metrics} to={S.score}><Levels /></Cut>
  <Cut from={S.score} to={S.problem}><ScoreBurst /></Cut>
  <Cut from={S.problem} to={S.fix}><Cliches /></Cut>
  <Cut from={S.fix} to={S.meet}><FixScene /></Cut>
  <Cut from={S.meet} to={S.tour}><Meet /></Cut>
  <Cut from={S.tour} to={S.brand}><Tour /></Cut>
  <Cut from={S.brand} to={S.end} last><Brand /></Cut>
  <Grain />
</AbsoluteFill>;
