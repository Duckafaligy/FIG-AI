import type { CSSProperties, ReactNode } from "react";
import { AbsoluteFill, Easing, Sequence, interpolate, interpolateColors, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";
import { siGithub, siShopify, siWebflow, siWix, siWordpress } from "simple-icons";

export const { fontFamily: SANS } = loadInter("normal", { weights: ["500", "600", "700", "800"], subsets: ["latin"] });
export const { fontFamily: MONO } = loadMono("normal", { weights: ["500", "700"], subsets: ["latin"] });

export const FPS = 30;
export const BEAT = 15;               // 120 BPM: a beat every 15 frames, so cuts land on music
export const DURATION = 30 * BEAT;   // 15 seconds

// The app's own palette (frontend/app/dashboard-dark.css).
const C = {
  bg: "#090A09", panel: "#111310", rail: "#0C0D0B", line: "#2A2F24", soft: "#1D2119",
  ink: "#F3F5EF", copy: "#AEB6A7", muted: "#8F968A", faint: "#6F7869",
  green: "#14C86B", amber: "#D9A441", red: "#E0674F",
};

// Scene starts, in beats.
const S = { hook: 0, generic: 4, score: 10, finding: 16, publish: 21, close: 26 };

/* ---------------------------------------------------------------- helpers */

export function useUnit() {
  const { width, height } = useVideoConfig();
  const vertical = height > width;
  // A phone screen is tall, so everything sits a size up there.
  return { u: (Math.min(width, height) / 1080) * (vertical ? 1.14 : 1), vertical };
}

/** A springy 0→1 that starts at `at` frames. */
export function usePop(at: number, stiffness = 220) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - at, fps, config: { damping: 15, stiffness, mass: 0.6 } });
}

/** Each scene fades up fast and leaves by sliding away, keynote style. */
function Scene({ length, children }: { length: number; children: ReactNode }) {
  const frame = useCurrentFrame();
  const out = interpolate(frame, [length - 6, length], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic) });
  const inn = interpolate(frame, [0, 5], [0, 1], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ opacity: inn * (1 - out), transform: `translateY(${-out * 80}px) scale(${1 - out * 0.04})` }}>{children}</AbsoluteFill>;
}

function Word({ at, children, size, color = C.ink, weight = 800, style }: { at: number; children: ReactNode; size: number; color?: string; weight?: number; style?: CSSProperties }) {
  const p = usePop(at);
  return <span style={{ display: "inline-block", fontFamily: SANS, fontSize: size, fontWeight: weight, color, letterSpacing: "-0.045em", lineHeight: 1.02,
    opacity: Math.min(1, p * 1.4), transform: `translateY(${(1 - p) * size * 0.45}px) scale(${0.9 + p * 0.1})`, ...style }}>{children}</span>;
}

export function Mark({ icon, size, fill }: { icon: { path: string; hex: string }; size: number; fill?: string }) {
  return <svg width={size} height={size} viewBox="0 0 24 24"><path d={icon.path} fill={fill ?? `#${icon.hex}`} /></svg>;
}

function Background() {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const x = interpolate(frame, [0, DURATION], [20, 80]);
  return <AbsoluteFill style={{ background: C.bg }}>
    <AbsoluteFill style={{ backgroundImage: `linear-gradient(${C.soft} 1px, transparent 1px), linear-gradient(90deg, ${C.soft} 1px, transparent 1px)`, backgroundSize: `${width / 12}px ${width / 12}px`, opacity: 0.35 }} />
    <AbsoluteFill style={{ background: `radial-gradient(circle at ${x}% ${height > width ? 35 : 45}%, #14C86B22, transparent 55%)` }} />
  </AbsoluteFill>;
}

/* ----------------------------------------------------------------- scenes */

function Hook() {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  const swap = frame >= 2 * BEAT;
  return <Scene length={4 * BEAT}>
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: 80 * u, textAlign: "center" }}>
      {!swap ? <div style={{ display: "flex", gap: 28 * u, flexWrap: "wrap", justifyContent: "center" }}>
        <Word at={0} size={150 * u}>Your</Word><Word at={6} size={150 * u}>site</Word><Word at={12} size={150 * u} color={C.green}>works.</Word>
      </div> : <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 * u }}>
        <Word at={2 * BEAT} size={96 * u} color={C.copy} weight={700}>But does it look like</Word>
        <Word at={2 * BEAT + 8} size={132 * u}>everyone else’s?</Word>
      </div>}
    </AbsoluteFill>
  </Scene>;
}

const GENERIC_LABELS = ["default gradient", "overused icon", "same card ×6"];

function Generic() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const cols = vertical ? 2 : 3;
  const cardW = (vertical ? 380 : 400) * u, cardH = 300 * u;
  const scan = interpolate(frame, [2 * BEAT, 3.6 * BEAT], [-0.05, 1.05], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const scanning = frame >= 2 * BEAT && frame <= 3.7 * BEAT;
  const gridW = cols * cardW + (cols - 1) * 28 * u, gridH = (6 / cols) * cardH + (6 / cols - 1) * 28 * u;
  return <Scene length={6 * BEAT}>
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ position: "relative", width: gridW, height: gridH }}>
        <div style={{ display: "grid", gridTemplateColumns: `repeat(${cols}, ${cardW}px)`, gap: 28 * u }}>
          {Array.from({ length: 6 }, (_, i) => <GenericCard key={i} i={i} w={cardW} h={cardH} />)}
        </div>
        {/* the scan line */}
        {scanning && <div style={{ position: "absolute", left: -40 * u, right: -40 * u, top: `${scan * 100}%`, height: 4 * u, background: C.green, boxShadow: `0 0 ${40 * u}px ${10 * u}px #14C86B66` }} />}
        {/* what it found */}
        {GENERIC_LABELS.map((label, i) => <Flag key={label} at={Math.round(2.6 * BEAT + i * 6)} label={label} i={i} u={u} vertical={vertical} />)}
      </div>
    </AbsoluteFill>
  </Scene>;
}

function GenericCard({ i, w, h }: { i: number; w: number; h: number }) {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  const p = usePop(i * 3);
  const jitter = frame > 2 * BEAT ? Math.sin((frame + i * 7) * 1.7) * 1.5 * u : 0;
  return <div style={{ width: w, height: h, borderRadius: 26 * u, background: "#15161f", boxShadow: "0 18px 40px #0008", overflow: "hidden", padding: 26 * u, boxSizing: "border-box",
    display: "flex", flexDirection: "column", gap: 16 * u, opacity: p, transform: `translate(${jitter}px, ${(1 - p) * 60 * u}px) scale(${0.85 + p * 0.15})` }}>
    <div style={{ width: 64 * u, height: 64 * u, borderRadius: 18 * u, background: "linear-gradient(135deg,#7c5cff,#3ba7ff)", display: "grid", placeItems: "center" }}>
      <svg width={34 * u} height={34 * u} viewBox="0 0 24 24"><path d="M12 2l2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4z" fill="#fff" /></svg>
    </div>
    <div style={{ height: 22 * u, width: "70%", borderRadius: 6 * u, background: "#2b2d3d" }} />
    <div style={{ height: 14 * u, width: "90%", borderRadius: 6 * u, background: "#222433" }} />
    <div style={{ height: 14 * u, width: "60%", borderRadius: 6 * u, background: "#222433" }} />
    <div style={{ marginTop: "auto", height: 44 * u, width: "55%", borderRadius: 999, background: "linear-gradient(90deg,#7c5cff,#3ba7ff)" }} />
  </div>;
}

function Flag({ at, label, i, u, vertical }: { at: number; label: string; i: number; u: number; vertical: boolean }) {
  const p = usePop(at, 260);
  // A box around the icon, the gradient button and the whole grid.
  const boxes: CSSProperties[] = [
    { left: 14 * u, top: 14 * u, width: 90 * u, height: 90 * u },
    { left: 14 * u, top: 222 * u, width: (vertical ? 250 : 240) * u, height: 64 * u },
    { left: -16 * u, top: -16 * u, right: -16 * u, bottom: -16 * u },
  ];
  const tagPos: CSSProperties[] = [{ left: 116 * u, top: 40 * u }, { left: 14 * u, top: 294 * u }, { right: -16 * u, bottom: -70 * u }];
  return <>
    <div style={{ position: "absolute", ...boxes[i], border: `${3 * u}px solid ${C.green}`, opacity: p, transform: `scale(${1.15 - p * 0.15})`, boxShadow: `0 0 ${24 * u}px #14C86B55` }} />
    <div style={{ position: "absolute", ...tagPos[i], padding: `${8 * u}px ${14 * u}px`, background: C.green, color: C.bg, fontFamily: MONO, fontSize: 26 * u, fontWeight: 700,
      whiteSpace: "nowrap", opacity: p, transform: `translateY(${(1 - p) * 20 * u}px)` }}>{label}</div>
  </>;
}

const LAYERS: [string, number][] = [["Craft", 86], ["Structure", 81], ["Search", 84], ["Answers", 76]];

function Score() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const fill = interpolate(frame, [4, 2.4 * BEAT], [0, 83], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const colour = interpolateColors(fill, [0, 45, 70, 83], [C.red, C.red, C.amber, C.green]);
  const r = (vertical ? 210 : 190) * u, circ = 2 * Math.PI * r, size = r * 2 + 60 * u;
  return <Scene length={6 * BEAT}>
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: vertical ? "column" : "row", gap: (vertical ? 70 : 120) * u }}>
      <div style={{ position: "relative", width: size, height: size }}>
        <svg width={size} height={size}>
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={C.soft} strokeWidth={34 * u} />
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={colour} strokeWidth={34 * u} strokeDasharray={`${(fill / 100) * circ} ${circ}`} transform={`rotate(-90 ${size / 2} ${size / 2})`} />
        </svg>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
          <span style={{ fontFamily: MONO, fontSize: 150 * u, fontWeight: 700, color: C.ink, lineHeight: 1 }}>{Math.round(fill)}</span>
          <span style={{ fontFamily: SANS, fontSize: 30 * u, color: C.muted, fontWeight: 600 }}>site score</span>
        </AbsoluteFill>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 26 * u, width: (vertical ? 820 : 620) * u }}>
        <div style={{ display: "flex", gap: 22 * u, flexWrap: "wrap" }}>
          <Word at={BEAT} size={92 * u}>21 checks.</Word>
          <Word at={2 * BEAT} size={92 * u} color={C.green}>4 layers.</Word>
        </div>
        {LAYERS.map(([name, v], i) => <Bar key={name} name={name} value={v} at={Math.round(2.5 * BEAT + i * 7)} u={u} />)}
      </div>
    </AbsoluteFill>
  </Scene>;
}

function Bar({ name, value, at, u }: { name: string; value: number; at: number; u: number }) {
  const p = usePop(at, 160);
  return <div style={{ display: "flex", alignItems: "center", gap: 20 * u, opacity: Math.min(1, p * 2) }}>
    <span style={{ width: 190 * u, fontFamily: SANS, fontSize: 36 * u, fontWeight: 600, color: C.copy }}>{name}</span>
    <div style={{ flex: 1, height: 14 * u, background: C.soft }}><div style={{ height: "100%", width: `${value * p}%`, background: value >= 80 ? C.green : C.amber }} /></div>
    <span style={{ width: 60 * u, fontFamily: MONO, fontSize: 32 * u, color: C.ink, textAlign: "right" }}>{Math.round(value * p)}</span>
  </div>;
}

const FINDING: [string, string][] = [
  ["Where", "/pricing"],
  ["Why", "The price shows up before the reason to pay it."],
  ["Fix", "Move the features section above pricing."],
];

function Finding() {
  const { u } = useUnit();
  const card = usePop(BEAT / 2);
  return <Scene length={5 * BEAT}>
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 56 * u, padding: 70 * u }}>
      <div style={{ textAlign: "center" }}><Word at={0} size={104 * u}>Every finding,</Word><br /><Word at={6} size={104 * u} color={C.green}>explained.</Word></div>
      <div style={{ width: 900 * u, background: C.panel, border: `${2 * u}px solid ${C.line}`, borderLeft: `${8 * u}px solid ${C.red}`, padding: 44 * u,
        display: "flex", flexDirection: "column", gap: 30 * u, opacity: card, transform: `translateY(${(1 - card) * 120 * u}px)` }}>
        <div style={{ display: "flex", gap: 14 * u }}>
          {["Structure", "High"].map((t, i) => <span key={t} style={{ fontFamily: MONO, fontSize: 24 * u, fontWeight: 700, padding: `${6 * u}px ${14 * u}px`, color: i ? C.red : C.copy, border: `${2 * u}px solid ${i ? C.red : C.line}` }}>{t}</span>)}
        </div>
        <div style={{ fontFamily: SANS, fontSize: 46 * u, fontWeight: 700, color: C.ink, letterSpacing: "-0.02em", lineHeight: 1.15 }}>Pricing sits above the section that justifies it</div>
        {FINDING.map(([k, v], i) => <Row key={k} k={k} v={v} at={Math.round(1.6 * BEAT + i * 8)} u={u} />)}
      </div>
    </AbsoluteFill>
  </Scene>;
}

function Row({ k, v, at, u }: { k: string; v: string; at: number; u: number }) {
  const p = usePop(at, 260);
  return <div style={{ display: "flex", gap: 26 * u, alignItems: "baseline", opacity: p, transform: `translateX(${(1 - p) * -40 * u}px)`, borderTop: `${2 * u}px solid ${C.soft}`, paddingTop: 22 * u }}>
    <span style={{ width: 120 * u, flexShrink: 0, fontFamily: MONO, fontSize: 26 * u, fontWeight: 700, color: C.green, textTransform: "uppercase", letterSpacing: "0.08em" }}>{k}</span>
    <span style={{ fontFamily: k === "Where" ? MONO : SANS, fontSize: 36 * u, color: C.ink, lineHeight: 1.3 }}>{v}</span>
  </div>;
}

const PLATFORMS = [siWordpress, siShopify, siWebflow, siWix, siGithub];
const VERBS = ["Connect.", "Approve.", "Publish.", "Undo."];

function Publish() {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  const verb = Math.min(VERBS.length - 1, Math.floor(frame / BEAT));
  const verbStart = verb * BEAT;
  const approved = frame >= 1.3 * BEAT, published = frame >= 2.3 * BEAT, undone = frame >= 3.3 * BEAT;
  const swapIn = usePop(Math.round(2.3 * BEAT), 240), swapBack = usePop(Math.round(3.3 * BEAT), 240);
  const swap = swapIn - swapBack;
  return <Scene length={5 * BEAT}>
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 60 * u, padding: 70 * u }}>
      <div style={{ display: "flex", gap: 22 * u }}>
        {PLATFORMS.map((icon, i) => <Tile key={icon.slug} icon={icon} at={i * 3} u={u} />)}
      </div>
      <div style={{ height: 150 * u, display: "flex", alignItems: "center" }}>
        <Word key={verb} at={verbStart} size={150 * u} color={verb === 3 ? C.amber : verb === 2 ? C.green : C.ink}>{VERBS[verb]}</Word>
      </div>
      <div style={{ width: 880 * u, background: C.panel, border: `${2 * u}px solid ${published && !undone ? C.green : C.line}`, padding: 38 * u, display: "flex", flexDirection: "column", gap: 18 * u }}>
        <span style={{ fontFamily: MONO, fontSize: 24 * u, color: C.muted, letterSpacing: "0.08em" }}>PAGE TITLE · /</span>
        <div style={{ position: "relative", height: 64 * u, overflow: "hidden" }}>
          <div style={{ position: "absolute", fontFamily: SANS, fontSize: 48 * u, fontWeight: 700, color: C.faint, transform: `translateY(${-swap * 70 * u}px)`, textDecoration: approved ? "line-through" : "none" }}>Home</div>
          <div style={{ position: "absolute", fontFamily: SANS, fontSize: 48 * u, fontWeight: 700, color: C.ink, transform: `translateY(${(1 - swap) * 70 * u}px)` }}>Harborline Dental · Halifax</div>
        </div>
        <span style={{ fontFamily: SANS, fontSize: 28 * u, fontWeight: 600, color: undone ? C.amber : published ? C.green : approved ? C.copy : C.muted }}>
          {undone ? "↶ Reverted. The old title is back." : published ? "✓ Live on the site" : approved ? "✓ Approved by you" : "Proposed. Nothing changes until you approve."}
        </span>
      </div>
    </AbsoluteFill>
  </Scene>;
}

function Tile({ icon, at, u }: { icon: { path: string; hex: string; slug: string }; at: number; u: number }) {
  const p = usePop(at, 260);
  const mono = icon.slug === "github" || icon.slug === "wix";
  return <div style={{ width: 118 * u, height: 118 * u, display: "grid", placeItems: "center", background: C.rail, border: `${2 * u}px solid ${C.line}`, opacity: p, transform: `translateY(${(1 - p) * 50 * u}px) scale(${0.7 + p * 0.3})` }}>
    <Mark icon={icon} size={58 * u} fill={mono ? C.ink : undefined} />
  </div>;
}

function Close() {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  const logo = usePop(Math.round(1.6 * BEAT), 170);
  const showLogo = frame >= 1.6 * BEAT;
  const url = usePop(Math.round(2.4 * BEAT));
  return <Scene length={4 * BEAT + 1}>
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 30 * u, textAlign: "center" }}>
      {!showLogo ? <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
        <Word at={0} size={140 * u}>Free scan.</Word>
        <Word at={8} size={140 * u} color={C.green}>No account.</Word>
      </div> : <>
        <div style={{ fontFamily: SANS, fontSize: 300 * u, fontWeight: 800, letterSpacing: "-0.06em", color: C.ink, lineHeight: 1, opacity: logo, transform: `scale(${0.7 + logo * 0.3})` }}>
          FIG<span style={{ color: C.green }}>.</span>
        </div>
        <div style={{ fontFamily: SANS, fontSize: 46 * u, fontWeight: 600, color: C.copy, opacity: logo }}>See what makes your site read as generic.</div>
        <div style={{ marginTop: 20 * u, padding: `${16 * u}px ${30 * u}px`, background: C.green, color: C.bg, fontFamily: MONO, fontSize: 36 * u, fontWeight: 700, opacity: url }}>fig-ai-seven.vercel.app</div>
      </>}
    </AbsoluteFill>
  </Scene>;
}

/* ------------------------------------------------------------------ video */

export const Promo = () => {
  const seq = (start: number, end: number, node: ReactNode) => <Sequence from={start * BEAT} durationInFrames={(end - start) * BEAT}>{node}</Sequence>;
  return <AbsoluteFill>
    <Background />
    {seq(S.hook, S.generic, <Hook />)}
    {seq(S.generic, S.score, <Generic />)}
    {seq(S.score, S.finding, <Score />)}
    {seq(S.finding, S.publish, <Finding />)}
    {seq(S.publish, S.close, <Publish />)}
    {seq(S.close, 30, <Close />)}
  </AbsoluteFill>;
};
