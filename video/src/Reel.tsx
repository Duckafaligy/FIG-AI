import type { CSSProperties, ReactNode } from "react";
import { AbsoluteFill, Audio, Easing, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { BEAT, MONO, SANS, usePop, useUnit } from "./Promo";

// After the Stripe "Payments simplified" reel: crowded problem, FIG as the
// organising force, a calm light report, who it's for, a branded close.
const C = {
  ink: "#F3F5EF", copy: "#AEB6A7", muted: "#8F968A", faint: "#6F7869",
  green: "#14C86B", glow: "#14C86B", deep: "#06140C", panel: "#101410", line: "#24301F",
  paper: "#FFFFFF", paperBg: "#F3F5EF", paperInk: "#0E110D", paperCopy: "#4B5347", paperLine: "#E2E5DC",
  red: "#E0674F", amber: "#D9A441",
};

// Scene starts in beats (120 BPM). Ends at 27 beats = 13.5 s.
const S = { hard: 0, generic: 3, hidden: 6, fig: 11, report: 15, kinds: 18, close: 22, end: 27 };
export const REEL_DURATION = S.end * BEAT;

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const soft = Easing.bezier(0.16, 1, 0.3, 1);
const range = (f: number, a: number, b: number, e = soft) => interpolate(f, [a, b], [0, 1], { ...clamp, easing: e });

/** Headline that sharpens out of a glow, like the reel's type. */
function Glow({ at, children, size, color = C.ink, glow = true, weight = 600, style }: { at: number; children: ReactNode; size: number; color?: string; glow?: boolean; weight?: number; style?: CSSProperties }) {
  const frame = useCurrentFrame();
  const p = range(frame, at, at + 14);
  return <span style={{ display: "inline-block", fontFamily: SANS, fontSize: size, fontWeight: weight, color, letterSpacing: "-0.035em", lineHeight: 1.05,
    opacity: p, filter: `blur(${(1 - p) * 14}px)`, transform: `scale(${1.06 - p * 0.06})`,
    textShadow: glow ? `0 0 ${size * 0.35}px ${color === C.ink ? "rgba(243,245,239,0.35)" : "rgba(20,200,107,0.45)"}` : undefined, ...style }}>{children}</span>;
}

/** Every scene leaves with a quick push-in and blur, so the cut feels like a camera move. */
function Scene({ length, children, push = 0.06 }: { length: number; children: ReactNode; push?: number }) {
  const frame = useCurrentFrame();
  const inn = range(frame, 0, 6);
  const out = range(frame, length - 6, length, Easing.in(Easing.cubic));
  const drift = interpolate(frame, [0, length], [1, 1 + push]);
  return <AbsoluteFill style={{ opacity: inn * (1 - out), filter: `blur(${out * 12}px)`, transform: `scale(${drift + out * 0.12})` }}>{children}</AbsoluteFill>;
}

function DarkBg({ children }: { children?: ReactNode }) {
  return <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 42%, #0E2A19 0%, #07100A 45%, #040604 80%)` }}>{children}</AbsoluteFill>;
}

function Rings({ u, n = 5, pulse = 0, opacity = 0.35 }: { u: number; n?: number; pulse?: number; opacity?: number }) {
  return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
    {Array.from({ length: n }, (_, i) => {
      const s = (380 + i * 210) * u * (1 + pulse * 0.04 * (n - i));
      return <div key={i} style={{ position: "absolute", width: s, height: s, borderRadius: "50%", border: `${2 * u}px solid ${C.green}`, opacity: opacity * (1 - i / (n + 1)) }} />;
    })}
  </AbsoluteFill>;
}

/* ------------------------------------------------------------------ icons */
// Plain SVG glyphs for the pills and pedestals (the overused ones are the point).
const ICONS: Record<string, string> = {
  sparkles: "M12 2l2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4z",
  arrow: "M4 12h14M13 6l6 6-6 6",
  zap: "M13 2L4 14h7l-1 8 9-12h-7z",
  type: "M5 5h14M12 5v14M9 19h6",
  palette: "M12 3a9 9 0 100 18c1 0 1.5-.7 1.5-1.5 0-1.2-1-1.3-1-2.5 0-1 .8-1.5 2-1.5H17a4 4 0 004-4c0-4.4-4-8.5-9-8.5z",
  quote: "M7 7h4v4c0 3-2 5-4 5M15 7h4v4c0 3-2 5-4 5",
  heading: "M6 4v16M18 4v16M6 12h12",
  tag: "M3 12V4h8l10 10-8 8z",
  bot: "M5 9h14v10H5zM12 5v4M9 14h.01M15 14h.01",
};
function Glyph({ name, size, color, stroke = false }: { name: string; size: number; color: string; stroke?: boolean }) {
  const filled = name === "sparkles" || name === "zap" || name === "tag";
  return <svg width={size} height={size} viewBox="0 0 24 24"><path d={ICONS[name]} fill={filled && !stroke ? color : "none"} stroke={color} strokeWidth={filled && !stroke ? 0 : 2.2} strokeLinecap="round" strokeLinejoin="round" /></svg>;
}

/* ----------------------------------------------------------------- scenes */

const PILLS: [string, string, number, number][] = [
  // label, icon, x, y as fractions of the stage (centre = 0,0)
  ["Typography", "type", -0.33, -0.3], ["Colour", "palette", 0.3, -0.32], ["Copy", "quote", -0.4, 0.05],
  ["Headings", "heading", 0.38, 0.08], ["Meta tags", "tag", -0.22, 0.33], ["AI answers", "bot", 0.24, 0.34],
];
// On a tall screen they stack above and below the headline instead of beside it.
const PILLS_TALL: [number, number][] = [[-0.2, -0.4], [0.24, -0.29], [-0.24, -0.17], [0.24, 0.17], [-0.22, 0.29], [0.2, 0.4]];

function Hard() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const swap = frame >= 16;
  const { width, height } = useVideoConfig();
  const stageW = vertical ? width * 0.92 : width * 0.62, stageH = vertical ? height * 0.6 : height * 0.8;
  return <Scene length={3 * BEAT}>
    <DarkBg><Rings u={u} opacity={0.18 * range(frame, 10, 24)} /></DarkBg>
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      {!swap ? <Glow at={0} size={130 * u}>Standing out is</Glow> : <div style={{ position: "relative", width: stageW, height: stageH }}>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}><Glow at={16} size={170 * u} weight={700}>Hard.</Glow></AbsoluteFill>
        {PILLS.map(([label, icon, x, y], i) => <Pill key={label} label={label} icon={icon} x={vertical ? PILLS_TALL[i][0] : x} y={vertical ? PILLS_TALL[i][1] : y}
          at={18 + i * 2} u={vertical ? u * 0.72 : u} stageW={stageW} stageH={stageH} />)}
      </div>}
    </AbsoluteFill>
  </Scene>;
}

function Pill({ label, icon, x, y, at, u, stageW, stageH }: { label: string; icon: string; x: number; y: number; at: number; u: number; stageW: number; stageH: number }) {
  const frame = useCurrentFrame();
  const p = usePop(at, 200);
  const orbit = (frame - at) * 0.012;
  const ox = x * stageW + Math.cos(orbit + x * 9) * 10 * u, oy = y * stageH + Math.sin(orbit + y * 9) * 10 * u;
  return <div style={{ position: "absolute", left: "50%", top: "50%", transform: `translate(-50%,-50%) translate(${ox * (0.6 + p * 0.4)}px, ${oy * (0.6 + p * 0.4)}px) scale(${0.6 + p * 0.4})`, opacity: Math.min(1, p * 1.5),
    display: "flex", alignItems: "center", gap: 18 * u, padding: `${22 * u}px ${38 * u}px ${22 * u}px ${22 * u}px`, borderRadius: 999,
    background: "linear-gradient(180deg, rgba(38,64,46,0.85), rgba(16,28,20,0.85))", border: `${1.5 * u}px solid rgba(20,200,107,0.45)`,
    boxShadow: `0 0 ${40 * u}px rgba(20,200,107,0.25), inset 0 ${1 * u}px 0 rgba(255,255,255,0.12)` }}>
    <span style={{ width: 62 * u, height: 62 * u, borderRadius: 16 * u, background: C.green, display: "grid", placeItems: "center" }}><Glyph name={icon} size={36 * u} color="#062012" stroke /></span>
    <span style={{ fontFamily: SANS, fontSize: 54 * u, fontWeight: 600, color: C.ink, whiteSpace: "nowrap" }}>{label}</span>
  </div>;
}

function Generic() {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  const push = interpolate(frame, [0, 3 * BEAT], [1, 1.14]);
  return <Scene length={3 * BEAT} push={0}>
    <DarkBg />
    <AbsoluteFill style={{ alignItems: "center", paddingTop: 170 * u }}><Glow at={0} size={104 * u}>Generic design.</Glow></AbsoluteFill>
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end", transform: `scale(${push})`, transformOrigin: "50% 80%" }}>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 40 * u, marginBottom: -40 * u, perspective: 1400 * u }}>
        {[["sparkles", 360], ["arrow", 470], ["zap", 400]].map(([icon, h], i) => <Pedestal key={icon} icon={icon as string} h={(h as number) * u} at={4 + i * 4} u={u} />)}
      </div>
    </AbsoluteFill>
  </Scene>;
}

function Pedestal({ icon, h, at, u }: { icon: string; h: number; at: number; u: number }) {
  const p = usePop(at, 150);
  const w = 260 * u;
  return <div style={{ display: "flex", flexDirection: "column", alignItems: "center", transform: `translateY(${(1 - p) * 300 * u}px)`, opacity: Math.min(1, p * 1.4) }}>
    <div style={{ width: 170 * u, height: 170 * u, borderRadius: 30 * u, marginBottom: 30 * u, display: "grid", placeItems: "center",
      background: "linear-gradient(145deg, #1D3A27, #0B1A10)", border: `${2 * u}px solid rgba(20,200,107,0.5)`,
      boxShadow: `0 0 ${70 * u}px rgba(20,200,107,0.35), inset 0 ${2 * u}px 0 rgba(255,255,255,0.1)`, transform: "rotateX(12deg)" }}>
      <Glyph name={icon} size={92 * u} color={C.green} />
    </div>
    <div style={{ width: w, height: h, background: "linear-gradient(180deg, #16241A 0%, #0A120C 70%, #050805 100%)", border: `${1.5 * u}px solid ${C.line}`, borderBottom: 0,
      boxShadow: `inset 0 ${3 * u}px 0 rgba(20,200,107,0.35)` }} />
  </div>;
}

function Hidden() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const second = frame >= 2.5 * BEAT;
  const rot = interpolate(frame, [0, 5 * BEAT], [-8, 8]);
  const zoom = interpolate(frame, [0, 5 * BEAT], [1, 1.25]);
  const cols = 44, rows = 26, gap = (vertical ? height : width) / cols * 1.15;
  const markers = [[0.22, 0.3], [0.55, 0.22], [0.78, 0.42], [0.35, 0.62], [0.63, 0.7], [0.12, 0.55]];
  return <Scene length={5 * BEAT} push={0}>
    <DarkBg />
    <AbsoluteFill style={{ perspective: 1800 * u, alignItems: "center", justifyContent: "center" }}>
      <div style={{ position: "relative", width: cols * gap, height: rows * gap, transform: `translateY(8%) rotateX(56deg) rotateZ(${rot}deg) scale(${zoom})` }}>
        {Array.from({ length: cols * rows }, (_, k) => {
          const x = k % cols, y = Math.floor(k / cols);
          // A loose continent shape, so the dots read as a map rather than a grid.
          const nx = x / cols - 0.5, ny = y / rows - 0.5;
          const land = Math.sin(nx * 9) * 0.18 + Math.cos(ny * 7 + nx * 3) * 0.2 + 0.25 - Math.hypot(nx * 1.1, ny * 1.4);
          if (land < 0) return null;
          return <i key={k} style={{ position: "absolute", left: x * gap, top: y * gap, width: 9 * u, height: 9 * u, borderRadius: 9, background: C.green, opacity: Math.min(1, 0.45 + land * 1.6), boxShadow: `0 0 ${10 * u}px rgba(20,200,107,0.6)` }} />;
        })}
        {markers.map(([mx, my], i) => {
          const t = ((frame + i * 9) % 36) / 36;
          const on = usePop(6 + i * 3, 200);
          return <div key={i} style={{ position: "absolute", left: `${mx * 100}%`, top: `${my * 100}%`, transform: `translate(-50%,-50%) scale(${on})` }}>
            <div style={{ width: 28 * u, height: 28 * u, borderRadius: "50%", background: C.ink, boxShadow: `0 0 ${30 * u}px ${C.green}` }} />
            <div style={{ position: "absolute", left: "50%", top: "50%", width: 140 * u, height: 140 * u, borderRadius: "50%", border: `${3 * u}px solid ${C.green}`,
              transform: `translate(-50%,-50%) scale(${0.3 + t})`, opacity: 1 - t }} />
          </div>;
        })}
      </div>
    </AbsoluteFill>
    <AbsoluteFill style={{ alignItems: "center", paddingTop: (vertical ? 330 : 150) * u }}>
      {!second ? <Glow at={2} size={112 * u}>Hidden from search.</Glow> : <Glow at={2.5 * BEAT} size={112 * u}>Invisible to <span style={{ color: C.green }}>AI.</span></Glow>}
    </AbsoluteFill>
  </Scene>;
}

function Fig() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const pulse = Math.sin(frame * 0.25) * 0.5 + 0.5;
  const logo = usePop(0, 160);
  return <Scene length={4 * BEAT}>
    <DarkBg><Rings u={u * 1.3} n={6} pulse={pulse} opacity={0.5 * logo} /></DarkBg>
    <AbsoluteFill style={{ alignItems: "center", paddingTop: (vertical ? 380 : 90) * u }}>
      <div style={{ fontFamily: SANS, fontSize: 250 * u, fontWeight: 800, letterSpacing: "-0.06em", color: C.ink, lineHeight: 0.95, opacity: logo, transform: `scale(${0.8 + logo * 0.2})`,
        textShadow: `0 0 ${80 * u}px rgba(20,200,107,0.55)` }}>FIG<span style={{ color: C.green }}>.</span></div>
      <Glow at={8} size={62 * u} weight={500} color={C.copy} glow={false}>checks it all together.</Glow>
    </AbsoluteFill>
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end", perspective: 1600 * u, paddingBottom: (vertical ? 330 : 40) * u }}>
      <div style={{ display: "flex", gap: 30 * u, alignItems: "flex-end", transform: vertical ? "scale(0.64)" : undefined }}>
        <Panel at={14} tilt={22} u={u} w={400}><ScorePanel u={u} /></Panel>
        <Panel at={10} tilt={0} u={u} w={470} lift={40}><FindingsPanel u={u} /></Panel>
        <Panel at={18} tilt={-22} u={u} w={400}><PublishPanel u={u} /></Panel>
      </div>
    </AbsoluteFill>
  </Scene>;
}

function Panel({ at, tilt, u, w, lift = 0, children }: { at: number; tilt: number; u: number; w: number; lift?: number; children: ReactNode }) {
  const p = usePop(at, 140);
  return <div style={{ width: w * u, padding: 26 * u, boxSizing: "border-box", background: "linear-gradient(180deg, #121A14, #0B100C)", border: `${1.5 * u}px solid rgba(20,200,107,0.35)`, borderRadius: 20 * u,
    boxShadow: `0 ${30 * u}px ${80 * u}px rgba(0,0,0,0.6), 0 0 ${50 * u}px rgba(20,200,107,0.18)`, opacity: Math.min(1, p * 1.5),
    transform: `translateY(${(1 - p) * 260 * u - lift * u}px) rotateY(${tilt}deg) rotateX(10deg)` }}>{children}</div>;
}

const tiny = (u: number, c = C.muted): CSSProperties => ({ fontFamily: MONO, fontSize: 18 * u, color: c, letterSpacing: "0.06em" });

function ScorePanel({ u }: { u: number }) {
  const r = 70 * u, c = 2 * Math.PI * r;
  return <div style={{ display: "flex", flexDirection: "column", gap: 16 * u }}>
    <span style={tiny(u)}>SITE SCORE</span>
    <div style={{ display: "flex", alignItems: "center", gap: 22 * u }}>
      <svg width={r * 2 + 20 * u} height={r * 2 + 20 * u}><circle cx={r + 10 * u} cy={r + 10 * u} r={r} fill="none" stroke={C.line} strokeWidth={14 * u} />
        <circle cx={r + 10 * u} cy={r + 10 * u} r={r} fill="none" stroke={C.green} strokeWidth={14 * u} strokeDasharray={`${c * 0.83} ${c}`} transform={`rotate(-90 ${r + 10 * u} ${r + 10 * u})`} />
        <text x="50%" y="56%" textAnchor="middle" fill={C.ink} style={{ fontFamily: MONO, fontSize: 44 * u, fontWeight: 700 }}>83</text></svg>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 * u }}>{["Craft", "Structure", "Search", "Answers"].map((l, i) => <div key={l} style={{ display: "flex", gap: 8 * u, alignItems: "center" }}>
        <span style={{ ...tiny(u, C.copy), width: 100 * u, letterSpacing: 0 }}>{l}</span><i style={{ width: 60 * u, height: 5 * u, background: i === 3 ? C.amber : C.green }} /></div>)}</div>
    </div>
  </div>;
}

function FindingsPanel({ u }: { u: number }) {
  return <div style={{ display: "flex", flexDirection: "column", gap: 14 * u }}>
    <span style={tiny(u)}>FINDINGS</span>
    {[["Pricing above its reason", C.red], ["Overused sparkle icon", C.amber], ["No llms.txt", C.amber], ["Meta description too long", C.green]].map(([t, c]) =>
      <div key={t} style={{ display: "flex", alignItems: "center", gap: 12 * u, padding: `${12 * u}px ${14 * u}px`, background: "#0E1510", borderLeft: `${4 * u}px solid ${c}` }}>
        <span style={{ fontFamily: SANS, fontSize: 24 * u, fontWeight: 600, color: C.ink }}>{t}</span></div>)}
  </div>;
}

function PublishPanel({ u }: { u: number }) {
  return <div style={{ display: "flex", flexDirection: "column", gap: 14 * u }}>
    <span style={tiny(u)}>PUBLISH</span>
    <span style={{ fontFamily: SANS, fontSize: 26 * u, color: C.muted, textDecoration: "line-through" }}>Home</span>
    <span style={{ fontFamily: SANS, fontSize: 28 * u, fontWeight: 700, color: C.ink }}>Harborline Dental · Halifax</span>
    <div style={{ display: "flex", gap: 10 * u }}>
      <span style={{ padding: `${10 * u}px ${18 * u}px`, background: C.green, color: "#062012", fontFamily: SANS, fontSize: 22 * u, fontWeight: 700 }}>Approve</span>
      <span style={{ padding: `${10 * u}px ${18 * u}px`, border: `${1.5 * u}px solid ${C.line}`, color: C.copy, fontFamily: SANS, fontSize: 22 * u, fontWeight: 600 }}>Undo</span>
    </div>
  </div>;
}

function Report() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  // The palette flips: dark wash drains away into paper.
  const flip = range(frame, 0, 10);
  return <Scene length={3 * BEAT}>
    <AbsoluteFill style={{ background: C.paperBg }} />
    <AbsoluteFill style={{ background: "#040604", opacity: 1 - flip }} />
    <AbsoluteFill style={{ alignItems: "center", paddingTop: (vertical ? 300 : 110) * u }}>
      <div style={{ display: "flex", gap: 22 * u, flexWrap: "wrap", justifyContent: "center" }}>
        <Glow at={4} size={96 * u} color={C.paperInk} glow={false}>In one</Glow>
        <Glow at={10} size={96 * u} color={C.green} glow={false}>clear report.</Glow>
      </div>
    </AbsoluteFill>
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end", perspective: 1800 * u, paddingBottom: (vertical ? 280 : 0) * u }}>
      <div style={{ display: "flex", gap: 36 * u, marginBottom: (vertical ? 0 : 70) * u, transform: vertical ? "scale(0.62)" : undefined, transformOrigin: "50% 100%" }}>
        <PaperPanel at={6} tilt={16} u={u}>
          <span style={tiny(u, C.paperCopy)}>HARBORLINEDENTAL.COM · OVERVIEW</span>
          <div style={{ fontFamily: SANS, fontSize: 44 * u, fontWeight: 700, color: C.paperInk, letterSpacing: "-0.03em" }}>Thirteen findings across four layers.</div>
          {[["Craft", 52], ["Structure", 40], ["Search", 48], ["Answers", 32]].map(([l, v]) => <div key={l} style={{ display: "flex", alignItems: "center", gap: 14 * u }}>
            <span style={{ width: 150 * u, fontFamily: SANS, fontSize: 24 * u, color: C.paperCopy }}>{l}</span>
            <i style={{ flex: 1, height: 10 * u, background: C.paperLine }}><b style={{ display: "block", height: "100%", width: `${v}%`, background: (v as number) >= 50 ? C.amber : C.red }} /></i>
            <span style={{ fontFamily: MONO, fontSize: 24 * u, color: C.paperInk }}>{v}</span></div>)}
        </PaperPanel>
        <PaperPanel at={10} tilt={-16} u={u}>
          <span style={tiny(u, C.paperCopy)}>STRUCTURE · HIGH</span>
          <div style={{ fontFamily: SANS, fontSize: 40 * u, fontWeight: 700, color: C.paperInk, letterSpacing: "-0.02em" }}>Pricing sits above the section that justifies it</div>
          {[["WHERE", "/pricing"], ["WHY", "The price shows up before the reason."], ["FIX", "Move the features above pricing."]].map(([k, v]) => <div key={k} style={{ display: "flex", gap: 18 * u, borderTop: `${1.5 * u}px solid ${C.paperLine}`, paddingTop: 14 * u }}>
            <span style={{ ...tiny(u, C.green), width: 90 * u, fontWeight: 700 }}>{k}</span><span style={{ fontFamily: SANS, fontSize: 26 * u, color: C.paperInk }}>{v}</span></div>)}
        </PaperPanel>
      </div>
    </AbsoluteFill>
  </Scene>;
}

function PaperPanel({ at, tilt, u, children }: { at: number; tilt: number; u: number; children: ReactNode }) {
  const p = usePop(at, 130);
  return <div style={{ width: 680 * u, minHeight: 470 * u, padding: 38 * u, boxSizing: "border-box", display: "flex", flexDirection: "column", gap: 20 * u, background: C.paper, borderRadius: 22 * u,
    boxShadow: `0 ${40 * u}px ${100 * u}px rgba(14,17,13,0.16)`, border: `${1.5 * u}px solid ${C.paperLine}`, opacity: Math.min(1, p * 1.4),
    transform: `translateY(${(1 - p) * 420 * u}px) rotateY(${tilt}deg) rotateX(12deg)` }}>{children}</div>;
}

const KINDS: [string, string][] = [
  ["Portfolios", "Your work, not a template's."], ["SaaS", "Landing pages that don't read like every launch."],
  ["Online stores", "Shopify and WordPress, fixed with your approval."], ["Agencies", "Every client, one workspace."],
  ["Class projects", "Learn the patterns, then design past them."],
];

function Kinds() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const end = frame >= 2.6 * BEAT;
  return <Scene length={4 * BEAT}>
    <AbsoluteFill style={{ background: C.paperBg }} />
    {/* The broad curved band of the reel, in green */}
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <div style={{ position: "absolute", width: 2600 * u, height: 2600 * u, borderRadius: "50%", left: vertical ? -1900 * u : -1500 * u, top: vertical ? 900 * u : -300 * u,
        background: "radial-gradient(circle at 70% 40%, #1ED67A, #0C7A42)", opacity: range(frame, 0, 10) }} />
    </AbsoluteFill>
    <AbsoluteFill style={{ justifyContent: vertical ? "flex-start" : "center", padding: vertical ? `${230 * u}px ${80 * u}px` : `0 0 0 ${110 * u}px`, zIndex: 2 }}>
      {!end ? <div style={{ display: "flex", flexDirection: "column" }}>
        <Glow at={2} size={96 * u} color={vertical ? C.paperInk : C.paper} glow={false}>Built for</Glow>
        <Glow at={8} size={120 * u} color={vertical ? C.green : C.paper} glow={false} weight={700}>every site</Glow>
      </div> : <Glow at={2.6 * BEAT} size={130 * u} color={vertical ? C.paperInk : C.paper} glow={false} weight={700}>of every kind.</Glow>}
    </AbsoluteFill>
    <AbsoluteFill style={{ perspective: 1800 * u }}>
      {KINDS.map(([title, sub], i) => {
        const p = usePop(4 + i * 5, 150);
        const x = (vertical ? 50 + i * 70 : 780 + i * 120) * u, y = (vertical ? 760 + i * 170 : 120 + i * 150) * u;
        return <div key={title} style={{ position: "absolute", left: x, top: y, width: 540 * u, padding: 30 * u, boxSizing: "border-box", background: C.paper, borderRadius: 18 * u,
          border: `${1.5 * u}px solid ${C.paperLine}`, borderTop: `${6 * u}px solid ${C.green}`, boxShadow: `0 ${30 * u}px ${70 * u}px rgba(14,17,13,0.18)`,
          opacity: Math.min(1, p * 1.4), transform: `translate(${(1 - p) * 500 * u}px, ${(1 - p) * -200 * u}px) rotateY(-14deg) rotateX(6deg)` }}>
          <div style={{ fontFamily: SANS, fontSize: 40 * u, fontWeight: 700, color: C.paperInk }}>{title}</div>
          <div style={{ fontFamily: SANS, fontSize: 24 * u, color: C.paperCopy, marginTop: 8 * u }}>{sub}</div>
        </div>;
      })}
    </AbsoluteFill>
  </Scene>;
}

function Close() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const phone = usePop(0, 120);
  const fill = range(frame, 8, 30, Easing.out(Easing.cubic));
  const r = 120 * u, c = 2 * Math.PI * r;
  return <Scene length={5 * BEAT + 1}>
    <DarkBg />
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <div style={{ position: "absolute", width: 3000 * u, height: 3000 * u, borderRadius: "50%", left: -600 * u, top: vertical ? 1250 * u : 620 * u,
        background: "radial-gradient(circle at 50% 0%, #14C86B55, #0B3A2000 60%)", border: `${3 * u}px solid rgba(20,200,107,0.5)` }} />
    </AbsoluteFill>
    <AbsoluteFill style={{ flexDirection: vertical ? "column" : "row", alignItems: "center", justifyContent: "center", gap: (vertical ? 60 : 120) * u }}>
      <div style={{ width: 380 * u, height: 780 * u, borderRadius: 60 * u, background: "#0B0D0B", border: `${10 * u}px solid #1F241E`, boxShadow: `0 ${50 * u}px ${120 * u}px rgba(0,0,0,0.7), 0 0 ${60 * u}px rgba(20,200,107,0.25)`,
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 26 * u, transform: `translateY(${(1 - phone) * 500 * u}px) rotate(${(1 - phone) * -8}deg)`, order: vertical ? 2 : 0 }}>
        <svg width={r * 2 + 30 * u} height={r * 2 + 30 * u}><circle cx={r + 15 * u} cy={r + 15 * u} r={r} fill="none" stroke={C.line} strokeWidth={22 * u} />
          <circle cx={r + 15 * u} cy={r + 15 * u} r={r} fill="none" stroke={C.green} strokeWidth={22 * u} strokeLinecap="round" strokeDasharray={`${c * 0.83 * fill} ${c}`} transform={`rotate(-90 ${r + 15 * u} ${r + 15 * u})`} />
          <text x="50%" y="57%" textAnchor="middle" fill={C.ink} style={{ fontFamily: MONO, fontSize: 80 * u, fontWeight: 700 }}>{Math.round(83 * fill)}</text></svg>
        <span style={{ fontFamily: SANS, fontSize: 28 * u, color: C.copy }}>Your site score</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", alignItems: vertical ? "center" : "flex-start", textAlign: vertical ? "center" : "left" }}>
        <Glow at={6} size={240 * u} weight={800} style={{ letterSpacing: "-0.06em" }}>FIG<span style={{ color: C.green }}>.</span></Glow>
        <Glow at={14} size={56 * u} weight={500} color={C.copy} glow={false}>See what makes your site generic.</Glow>
        <div style={{ marginTop: 30 * u, opacity: range(frame, 26, 36), fontFamily: MONO, fontSize: 32 * u, color: C.green }}>Free scan · no account</div>
      </div>
    </AbsoluteFill>
  </Scene>;
}

/* ------------------------------------------------------------------ video */

/** `sound` adds the synthesized track and effects (sound/make_sound.py). */
export const Reel = ({ sound = false }: { sound?: boolean }) => {
  const seq = (start: number, end: number, node: ReactNode) => <Sequence from={start * BEAT} durationInFrames={(end - start) * BEAT}>{node}</Sequence>;
  return <AbsoluteFill style={{ background: "#040604" }}>
    {sound && <Audio src={staticFile("reel-sound.wav")} />}
    {seq(S.hard, S.generic, <Hard />)}
    {seq(S.generic, S.hidden, <Generic />)}
    {seq(S.hidden, S.fig, <Hidden />)}
    {seq(S.fig, S.report, <Fig />)}
    {seq(S.report, S.kinds, <Report />)}
    {seq(S.kinds, S.close, <Kinds />)}
    {seq(S.close, S.end, <Close />)}
  </AbsoluteFill>;
};
