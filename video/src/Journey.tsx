import type { CSSProperties, ReactNode } from "react";
import { AbsoluteFill, Audio, Easing, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { siGithub, siShopify, siWebflow, siWix, siWordpress } from "simple-icons";
import { BEAT, MONO, Mark, SANS, usePop, useUnit } from "./Promo";

// One phone carries the whole story (after the Zoro app reel): each step of
// FIG's real flow gets a pose, a screen, and a two-part caption either side.
const C = {
  ink: "#F3F5EF", copy: "#AEB6A7", muted: "#8F968A", faint: "#6F7869",
  green: "#14C86B", red: "#E0674F", amber: "#D9A441", line: "#24301F", screen: "#0A0D0A", card: "#121812",
};

// Scene starts in beats (120 BPM; a beat is 15 frames). 80 beats = 40 s.
const SCENES = [
  { id: "intro", at: 0, left: "Is your site", right: "generic?", pose: { x: 0, ry: -18, rz: -4, s: 0.92 } },
  { id: "url", at: 6, left: "Paste your", right: "URL.", pose: { x: 0, ry: 0, rz: 0, s: 1 } },
  { id: "scan", at: 12, left: "Reads every", right: "page.", pose: { x: 0, ry: 16, rz: 2, s: 1 } },
  { id: "score", at: 19, left: "Your score,", right: "by layer.", pose: { x: 0, ry: -12, rz: -2, s: 1.04 } },
  { id: "findings", at: 26, left: "Every finding", right: "explained.", pose: { x: -0.27, ry: 24, rz: 0, s: 0.86 } },
  { id: "connect", at: 34, left: "Connect your", right: "platform.", pose: { x: 0, ry: -14, rz: 0, s: 1 } },
  { id: "ai", at: 42, left: "Ready for", right: "AI answers.", pose: { x: 0, ry: 0, rz: 0, s: 1 } },
  { id: "approve", at: 50, left: "You approve.", right: "It goes live.", pose: { x: 0, ry: 14, rz: 2, s: 1 } },
  { id: "improve", at: 58, left: "Scan again.", right: "See it climb.", pose: { x: 0, ry: -8, rz: 0, s: 1.08 } },
  { id: "end", at: 66, left: "", right: "", pose: { x: -0.2, ry: 12, rz: 0, s: 0.98 } },
] as const;
export const JOURNEY_BEATS = 80;
export const JOURNEY_DURATION = JOURNEY_BEATS * BEAT;
const sceneEnd = (i: number) => (i + 1 < SCENES.length ? SCENES[i + 1].at : JOURNEY_BEATS);

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const soft = Easing.bezier(0.16, 1, 0.3, 1);
const range = (f: number, a: number, b: number, e = soft) => interpolate(f, [a, b], [0, 1], { ...clamp, easing: e });

/* ---------------------------------------------------------------- stage */

function Background() {
  const frame = useCurrentFrame();
  const x = 50 + Math.sin(frame / 40) * 8;
  return <AbsoluteFill style={{ background: `radial-gradient(ellipse at ${x}% 45%, #0F2E1B 0%, #06100A 40%, #030503 78%)` }} />;
}

/** A vertical light streak sweeps across at every scene change. */
function Streak() {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const cut = SCENES.slice(1).map((s) => s.at * BEAT).find((c) => frame >= c - 8 && frame < c + 8);
  if (cut === undefined) return null;
  const p = (frame - (cut - 8)) / 16;
  return <AbsoluteFill style={{ pointerEvents: "none" }}>
    <div style={{ position: "absolute", top: 0, bottom: 0, left: -width * 0.2 + p * width * 1.4, width: width * 0.12,
      background: "linear-gradient(90deg, transparent, rgba(20,200,107,0.35), rgba(220,255,235,0.55), rgba(20,200,107,0.35), transparent)", filter: "blur(18px)", transform: "skewX(-12deg)" }} />
  </AbsoluteFill>;
}

function usePose() {
  const frame = useCurrentFrame();
  let i = SCENES.length - 1;
  while (i > 0 && frame < SCENES[i].at * BEAT) i--;
  const now = SCENES[i].pose, before = SCENES[Math.max(0, i - 1)].pose;
  const k = i === 0 ? 1 : range(frame, SCENES[i].at * BEAT, SCENES[i].at * BEAT + 16);
  const mix = (a: number, b: number) => a + (b - a) * k;
  // A gentle float keeps the phone alive between moves.
  return { x: mix(before.x, now.x), ry: mix(before.ry, now.ry) + Math.sin(frame / 22) * 2, rz: mix(before.rz, now.rz), s: mix(before.s, now.s), i };
}

function Phone({ children }: { children: ReactNode }) {
  const { u, vertical } = useUnit();
  const { width } = useVideoConfig();
  const frame = useCurrentFrame();
  const pose = usePose();
  const rise = range(frame, 6, 30);
  const w = 390 * u, h = 820 * u;
  const x = vertical ? 0 : pose.x * width;
  const y = vertical && pose.i === 4 ? -300 * u : vertical && pose.i === 9 ? 260 * u : 0;
  const s = vertical && pose.i === 4 ? 0.62 : pose.s;
  return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", perspective: 2200 * u }}>
    <div style={{ width: w, height: h, borderRadius: 64 * u, padding: 12 * u, boxSizing: "border-box", background: "linear-gradient(160deg, #2C3A2F, #0D120E 40%, #1B241D)",
      boxShadow: `0 0 0 ${2 * u}px rgba(20,200,107,0.55), 0 0 ${90 * u}px rgba(20,200,107,0.35), 0 ${60 * u}px ${140 * u}px rgba(0,0,0,0.7)`,
      transform: `translate(${x}px, ${y + (1 - rise) * 900 * u}px) rotateY(${pose.ry}deg) rotateZ(${pose.rz}deg) scale(${s})`, opacity: rise }}>
      <div style={{ position: "relative", width: "100%", height: "100%", borderRadius: 52 * u, overflow: "hidden", background: C.screen }}>
        {children}
        <div style={{ position: "absolute", top: 16 * u, left: "50%", width: 110 * u, height: 30 * u, marginLeft: -55 * u, borderRadius: 999, background: "#000" }} />
      </div>
    </div>
  </AbsoluteFill>;
}

/** Two short phrases either side of the phone (above and below it when the screen is tall). */
function Caption({ left, right, top = false }: { left: string; right: string; top?: boolean }) {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const a = range(frame, 4, 16), b = range(frame, 9, 21);
  const size = (vertical ? 84 : 76) * u;
  const text = (s: string, p: number, green: boolean, align: "left" | "right" | "center"): ReactNode => <div style={{ fontFamily: SANS, fontSize: size, fontWeight: 700, letterSpacing: "-0.035em",
    color: green ? C.green : C.ink, textAlign: align, opacity: p, filter: `blur(${(1 - p) * 10}px)`, transform: `translateY(${(1 - p) * 30 * u}px)`,
    textShadow: green ? "0 0 40px rgba(20,200,107,0.5)" : "0 0 30px rgba(243,245,239,0.25)", whiteSpace: "nowrap" }}>{s}</div>;
  // When the phone steps aside for the cards, the caption runs along the top instead.
  if (top) return <AbsoluteFill style={{ alignItems: "center", paddingTop: (vertical ? 150 : 70) * u }}>
    <div style={{ display: "flex", gap: 24 * u }}>{text(left, a, false, "right")}{text(right, b, true, "left")}</div>
  </AbsoluteFill>;
  if (vertical) return <AbsoluteFill style={{ alignItems: "center", justifyContent: "space-between", padding: `${150 * u}px 0 ${170 * u}px` }}>
    {text(left, a, false, "center")}{text(right, b, true, "center")}
  </AbsoluteFill>;
  return <AbsoluteFill style={{ flexDirection: "row", alignItems: "center" }}>
    <div style={{ flex: 1, display: "flex", justifyContent: "flex-end", paddingRight: 300 * u }}>{text(left, a, false, "right")}</div>
    <div style={{ flex: 1, display: "flex", justifyContent: "flex-start", paddingLeft: 300 * u }}>{text(right, b, true, "left")}</div>
  </AbsoluteFill>;
}

/* ------------------------------------------------------------ screen kit */

const Pad = ({ children, gap = 18, style }: { children: ReactNode; gap?: number; style?: CSSProperties }) => {
  const { u } = useUnit();
  return <AbsoluteFill style={{ padding: `${70 * u}px ${26 * u}px ${30 * u}px`, display: "flex", flexDirection: "column", gap: gap * u, ...style }}>{children}</AbsoluteFill>;
};
function Label({ children }: { children: ReactNode }) {
  const { u } = useUnit();
  return <span style={{ fontFamily: MONO, fontSize: 15 * u, color: C.muted, letterSpacing: "0.1em" }}>{children}</span>;
}
function Title({ children, size = 34 }: { children: ReactNode; size?: number }) {
  const { u } = useUnit();
  return <div style={{ fontFamily: SANS, fontSize: size * u, fontWeight: 700, color: C.ink, letterSpacing: "-0.03em", lineHeight: 1.1 }}>{children}</div>;
}
/** A fingertip tap: a ring that grows and fades where the thumb lands. */
function Tap({ at, x, y }: { at: number; x: string; y: string }) {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  if (frame < at - 6 || frame > at + 16) return null;
  const p = range(frame, at, at + 14);
  const come = range(frame, at - 6, at);
  return <div style={{ position: "absolute", left: x, top: y, transform: "translate(-50%,-50%)", pointerEvents: "none" }}>
    <div style={{ width: 60 * u, height: 60 * u, borderRadius: "50%", background: "rgba(243,245,239,0.35)", opacity: come * (1 - p), transform: `scale(${0.6 + come * 0.4})` }} />
    <div style={{ position: "absolute", left: "50%", top: "50%", width: 60 * u, height: 60 * u, marginLeft: -30 * u, marginTop: -30 * u, borderRadius: "50%", border: `${3 * u}px solid ${C.green}`,
      transform: `scale(${1 + p * 1.6})`, opacity: 1 - p }} />
  </div>;
}
function Ring({ value, colour, size = 250, label }: { value: number; colour: string; size?: number; label?: string }) {
  const { u } = useUnit();
  const r = (size / 2 - 16) * u, c = 2 * Math.PI * r, S = size * u;
  return <div style={{ position: "relative", width: S, height: S, alignSelf: "center" }}>
    <svg width={S} height={S}><circle cx={S / 2} cy={S / 2} r={r} fill="none" stroke={C.line} strokeWidth={20 * u} />
      <circle cx={S / 2} cy={S / 2} r={r} fill="none" stroke={colour} strokeWidth={20 * u} strokeLinecap="round" strokeDasharray={`${(value / 100) * c} ${c}`} transform={`rotate(-90 ${S / 2} ${S / 2})`} /></svg>
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
      <span style={{ fontFamily: MONO, fontSize: size * 0.3 * u, fontWeight: 700, color: C.ink, lineHeight: 1 }}>{Math.round(value)}</span>
      {label && <span style={{ fontFamily: SANS, fontSize: 18 * u, color: C.muted }}>{label}</span>}
    </AbsoluteFill>
  </div>;
}
const tone = (v: number) => v >= 80 ? C.green : v >= 50 ? C.amber : C.red;

/* ---------------------------------------------------------------- screens */

function Splash() {
  const { u } = useUnit();
  const p = usePop(20, 150);
  return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", background: "radial-gradient(circle at 50% 45%, #10301C, #0A0D0A 70%)" }}>
    <div style={{ fontFamily: SANS, fontSize: 120 * u, fontWeight: 800, letterSpacing: "-0.06em", color: C.ink, opacity: p, transform: `scale(${0.7 + p * 0.3})`, textShadow: "0 0 50px rgba(20,200,107,0.6)" }}>
      FIG<span style={{ color: C.green }}>.</span></div>
  </AbsoluteFill>;
}

const URL_TEXT = "harborlinedental.com";
function UrlScreen() {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  const typed = Math.max(0, Math.min(URL_TEXT.length, Math.floor((frame - 10) / 1.6)));
  const pressed = frame >= 64 && frame < 72;
  return <Pad gap={22}>
    <Label>FREE SCAN · NO ACCOUNT</Label>
    <Title size={40}>See what makes your site generic.</Title>
    <div style={{ marginTop: 20 * u, padding: `${22 * u}px ${20 * u}px`, border: `${2 * u}px solid ${frame > 8 ? C.green : C.line}`, borderRadius: 16 * u, background: "#0E130E",
      fontFamily: MONO, fontSize: 24 * u, color: C.ink, display: "flex", alignItems: "center", minHeight: 30 * u }}>
      {URL_TEXT.slice(0, typed)}<span style={{ width: 3 * u, height: 30 * u, background: C.green, marginLeft: 2 * u, opacity: Math.floor(frame / 8) % 2 ? 1 : 0.2 }} />
    </div>
    <div style={{ padding: `${22 * u}px 0`, borderRadius: 16 * u, background: C.green, color: "#052012", fontFamily: SANS, fontSize: 28 * u, fontWeight: 800, textAlign: "center",
      transform: `scale(${pressed ? 0.95 : 1})`, boxShadow: `0 0 ${40 * u}px rgba(20,200,107,0.45)` }}>Scan</div>
    <Tap at={66} x="50%" y="52%" />
  </Pad>;
}

const PAGES = ["/", "/services", "/about", "/pricing", "/blog", "/contact"];
function ScanScreen() {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  const done = (i: number) => frame >= 12 + i * 12;
  const progress = range(frame, 6, 12 + PAGES.length * 12, Easing.linear);
  return <Pad gap={16}>
    <Label>READING YOUR SITE</Label>
    <Title>harborlinedental.com</Title>
    <div style={{ height: 8 * u, background: C.line, borderRadius: 999, overflow: "hidden" }}><div style={{ height: "100%", width: `${progress * 100}%`, background: C.green }} /></div>
    {PAGES.map((p, i) => {
      const pop = usePop(12 + i * 12, 280);
      return <div key={p} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: `${16 * u}px ${18 * u}px`, borderRadius: 14 * u, background: C.card, opacity: frame >= i * 6 ? 1 : 0.25 }}>
        <span style={{ fontFamily: MONO, fontSize: 22 * u, color: C.ink }}>{p}</span>
        {done(i) ? <span style={{ width: 34 * u, height: 34 * u, borderRadius: "50%", background: C.green, display: "grid", placeItems: "center", transform: `scale(${pop})`, color: "#052012", fontSize: 20 * u, fontWeight: 900 }}>✓</span>
          : <span style={{ width: 28 * u, height: 28 * u, borderRadius: "50%", border: `${3 * u}px solid ${C.line}`, borderTopColor: C.green, transform: `rotate(${frame * 20}deg)` }} />}
      </div>;
    })}
  </Pad>;
}

const LAYERS: [string, number][] = [["Craft", 52], ["Structure", 40], ["Search", 48], ["Answers", 32]];
function ScoreScreen() {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  const v = 44 * range(frame, 4, 34, Easing.out(Easing.cubic));
  return <Pad gap={20}>
    <Label>SITE SCORE</Label>
    <Ring value={v} colour={tone(v)} label="out of 100" />
    {LAYERS.map(([name, val], i) => {
      const p = range(frame, 30 + i * 6, 46 + i * 6);
      return <div key={name} style={{ display: "flex", alignItems: "center", gap: 14 * u }}>
        <span style={{ width: 120 * u, fontFamily: SANS, fontSize: 22 * u, color: C.copy }}>{name}</span>
        <i style={{ flex: 1, height: 10 * u, background: C.line, borderRadius: 999 }}><b style={{ display: "block", height: "100%", width: `${val * p}%`, background: tone(val), borderRadius: 999 }} /></i>
        <span style={{ width: 40 * u, fontFamily: MONO, fontSize: 22 * u, color: C.ink, textAlign: "right" }}>{Math.round(val * p)}</span>
      </div>;
    })}
  </Pad>;
}

const FINDINGS: [string, string, string][] = [
  ["Pricing sits above the section that justifies it", "Structure", C.red],
  ["The sparkle icon every template uses", "Craft", C.amber],
  ["“Elevate your workflow” reads as stock copy", "Craft", C.amber],
  ["AI answer engines are blocked in robots.txt", "Answers", C.red],
  ["Meta description is 182 characters", "Search", C.amber],
];
function FindingsScreen() {
  const { u } = useUnit();
  return <Pad gap={12}>
    <Label>13 FINDINGS</Label>
    {FINDINGS.map(([t, l, c]) => <div key={t} style={{ padding: `${14 * u}px ${16 * u}px`, borderRadius: 12 * u, background: C.card, borderLeft: `${5 * u}px solid ${c}` }}>
      <div style={{ fontFamily: MONO, fontSize: 14 * u, color: C.muted }}>{l.toUpperCase()}</div>
      <div style={{ fontFamily: SANS, fontSize: 20 * u, fontWeight: 600, color: C.ink, lineHeight: 1.25 }}>{t}</div>
    </div>)}
  </Pad>;
}

/** Outside the phone: finding cards sweep diagonally, then one comes forward. */
function FindingCarousel() {
  const { u, vertical } = useUnit();
  const { width, height } = useVideoConfig();
  const frame = useCurrentFrame();
  const sweep = interpolate(frame, [0, 70], [0, 1], clamp);
  const pick = range(frame, 64, 84);
  return <AbsoluteFill style={{ perspective: 2000 * u }}>
    {FINDINGS.map(([t, l, c], i) => {
      const chosen = i === 0;
      const baseX = (vertical ? 0.1 : 0.42) * width + i * (vertical ? 50 : 110) * u - sweep * (vertical ? 120 : 260) * u;
      const cardW = (vertical ? 600 : 700) * u;
      const baseY = (vertical ? 0.47 : 0.2) * height + i * (vertical ? 150 : 140) * u + (1 - sweep) * 120 * u;
      const cx = (width - (cardW + 160 * u)) / 2, cy = height * (vertical ? 0.42 : 0.3);
      const x = chosen ? baseX + (cx - baseX) * pick : baseX, y = chosen ? baseY + (cy - baseY) * pick : baseY;
      const fade = chosen ? 1 : 1 - pick * 0.85;
      const enter = range(frame, i * 4, i * 4 + 16);
      return <div key={t} style={{ position: "absolute", left: x, top: y, width: chosen ? cardW + 160 * u * pick : cardW, padding: 30 * u, boxSizing: "border-box", borderRadius: 22 * u,
        background: "linear-gradient(160deg, #182218, #0C110C)", border: `${2 * u}px solid rgba(20,200,107,${chosen ? 0.3 + pick * 0.5 : 0.3})`, borderLeft: `${8 * u}px solid ${c}`,
        boxShadow: `0 ${30 * u}px ${80 * u}px rgba(0,0,0,0.6), 0 0 ${chosen ? 70 * pick : 20}px rgba(20,200,107,0.3)`, opacity: enter * fade, zIndex: chosen ? 10 : 5 - i,
        transform: `translateX(${(1 - enter) * 600 * u}px) rotateY(${-18 * (1 - (chosen ? pick : 0))}deg) rotateZ(${-3 * (1 - (chosen ? pick : 0))}deg)` }}>
        <div style={{ fontFamily: MONO, fontSize: 20 * u, color: C.muted, letterSpacing: "0.08em" }}>{l.toUpperCase()} · {c === C.red ? "HIGH" : "MEDIUM"}</div>
        <div style={{ fontFamily: SANS, fontSize: 38 * u, fontWeight: 700, color: C.ink, letterSpacing: "-0.02em", lineHeight: 1.15, marginTop: 8 * u }}>{t}</div>
        {chosen && <div style={{ display: "flex", flexDirection: "column", gap: 12 * u, marginTop: 20 * u * pick, maxHeight: 400 * u * pick, overflow: "hidden", opacity: pick }}>
          {[["WHERE", "/pricing"], ["WHY", "Visitors see the price before the reason to pay it."], ["FIX", "Move the features section above pricing."]].map(([k, v]) =>
            <div key={k} style={{ display: "flex", gap: 20 * u, borderTop: `${1.5 * u}px solid ${C.line}`, paddingTop: 12 * u }}>
              <span style={{ width: 110 * u, fontFamily: MONO, fontSize: 22 * u, fontWeight: 700, color: C.green }}>{k}</span>
              <span style={{ fontFamily: k === "WHERE" ? MONO : SANS, fontSize: 28 * u, color: C.ink }}>{v}</span></div>)}
        </div>}
      </div>;
    })}
  </AbsoluteFill>;
}

const PLATFORMS = [siWordpress, siShopify, siWebflow, siWix, siGithub];
function ConnectScreen() {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  const connected = frame >= 40;
  const badge = usePop(40, 260);
  return <Pad gap={18}>
    <Label>CONNECT A PLATFORM</Label>
    <Title>Where does this site live?</Title>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 * u, marginTop: 8 * u }}>
      {PLATFORMS.map((p, i) => {
        const pop = usePop(6 + i * 3, 260);
        const on = connected && i === 0;
        return <div key={p.slug} style={{ height: 120 * u, borderRadius: 18 * u, background: on ? "#10301C" : C.card, border: `${2 * u}px solid ${on ? C.green : C.line}`, display: "flex",
          flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 10 * u, transform: `scale(${pop * (i === 0 && frame >= 34 && frame < 40 ? 0.94 : 1)})`, gridColumn: i === 4 ? "1 / -1" : undefined }}>
          <Mark icon={p} size={44 * u} fill={p.slug === "github" || p.slug === "wix" ? C.ink : undefined} />
          <span style={{ fontFamily: SANS, fontSize: 18 * u, color: C.copy }}>{p.title}</span>
        </div>;
      })}
    </div>
    <Tap at={36} x="27%" y="44%" />
    {connected && <div style={{ padding: `${16 * u}px`, borderRadius: 14 * u, background: C.green, color: "#052012", fontFamily: SANS, fontSize: 24 * u, fontWeight: 800, textAlign: "center",
      transform: `scale(${badge})` }}>✓ WordPress connected</div>}
  </Pad>;
}

const BOTS = ["GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended", "llms.txt"];
function AiScreen() {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  return <Pad gap={14}>
    <Label>AI ANSWERS</Label>
    <Title>Can AI engines read this site?</Title>
    {BOTS.map((b, i) => {
      const ok = frame >= 14 + i * 7;
      const pop = usePop(14 + i * 7, 280);
      return <div key={b} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: `${16 * u}px ${18 * u}px`, borderRadius: 14 * u, background: C.card }}>
        <span style={{ fontFamily: MONO, fontSize: 22 * u, color: C.ink }}>{b}</span>
        <span style={{ fontFamily: SANS, fontSize: 18 * u, fontWeight: 700, color: ok ? "#052012" : C.muted, background: ok ? C.green : "transparent", padding: `${6 * u}px ${12 * u}px`, borderRadius: 999,
          transform: `scale(${ok ? pop : 1})` }}>{ok ? (b === "llms.txt" ? "Found" : "Allowed") : "Checking"}</span>
      </div>;
    })}
  </Pad>;
}

/** Behind the phone in the AI scene: glowing rings that turn. */
function AiRings() {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  const on = range(frame, 0, 20);
  return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
    {[560, 760, 980].map((s, i) => <div key={s} style={{ position: "absolute", width: s * u, height: s * u, borderRadius: "50%", opacity: on * (0.7 - i * 0.18),
      border: `${(6 - i * 2) * u}px solid transparent`, borderTopColor: C.green, borderRightColor: "rgba(20,200,107,0.4)",
      transform: `rotate(${frame * (i % 2 ? -3 : 4)}deg)`, boxShadow: `0 0 ${60 * u}px rgba(20,200,107,0.25)` }} />)}
  </AbsoluteFill>;
}

function ApproveScreen() {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  const approved = frame >= 22, live = frame >= 36, undo = usePop(48, 260);
  const swap = range(frame, 36, 48);
  return <Pad gap={18}>
    <Label>PROPOSED CHANGE</Label>
    <Title>Page title · /</Title>
    <div style={{ borderRadius: 16 * u, background: C.card, padding: 20 * u, display: "flex", flexDirection: "column", gap: 10 * u }}>
      <span style={{ fontFamily: MONO, fontSize: 16 * u, color: C.muted }}>{live ? "BEFORE" : "NOW"}</span>
      <span style={{ fontFamily: SANS, fontSize: 28 * u, color: C.muted, textDecoration: approved ? "line-through" : "none" }}>Home</span>
    </div>
    <div style={{ borderRadius: 16 * u, background: "#10301C", border: `${2 * u}px solid ${C.green}`, padding: 20 * u, display: "flex", flexDirection: "column", gap: 10 * u }}>
      <span style={{ fontFamily: MONO, fontSize: 16 * u, color: C.green }}>{live ? "LIVE" : "AFTER"}</span>
      <span style={{ fontFamily: SANS, fontSize: 28 * u, fontWeight: 700, color: C.ink }}>Harborline Dental · Family dentist in Halifax</span>
    </div>
    <div style={{ padding: `${20 * u}px 0`, borderRadius: 16 * u, background: live ? "#10301C" : C.green, color: live ? C.green : "#052012", fontFamily: SANS, fontSize: 26 * u, fontWeight: 800,
      textAlign: "center", transform: `scale(${frame >= 18 && frame < 24 ? 0.95 : 1})`, border: live ? `${2 * u}px solid ${C.green}` : "none" }}>
      {live ? "✓ Live on the site" : approved ? "Publishing…" : "Approve"}</div>
    <Tap at={20} x="50%" y="80%" />
    <div style={{ alignSelf: "center", padding: `${10 * u}px ${20 * u}px`, borderRadius: 999, border: `${2 * u}px solid ${C.line}`, fontFamily: SANS, fontSize: 20 * u, color: C.copy,
      opacity: undo * (swap > 0 ? 1 : 0), transform: `scale(${undo})` }}>↶ Undo anytime</div>
  </Pad>;
}

function ImproveScreen() {
  const { u } = useUnit();
  const frame = useCurrentFrame();
  const v = 44 + 39 * range(frame, 8, 44, Easing.inOut(Easing.cubic));
  const chip = usePop(44, 240);
  return <Pad gap={22} style={{ alignItems: "stretch" }}>
    <Label>AFTER THE FIXES</Label>
    <Ring value={v} colour={tone(v)} size={290} label="out of 100" />
    <div style={{ alignSelf: "center", padding: `${10 * u}px ${24 * u}px`, borderRadius: 999, background: C.green, color: "#052012", fontFamily: MONO, fontSize: 30 * u, fontWeight: 800,
      transform: `scale(${chip})` }}>+39</div>
    <div style={{ fontFamily: SANS, fontSize: 22 * u, color: C.copy, textAlign: "center", opacity: chip }}>13 findings → 4</div>
  </Pad>;
}

function EndScreen() {
  const { u } = useUnit();
  return <Pad gap={22}>
    <Label>HARBORLINEDENTAL.COM</Label>
    <Ring value={83} colour={C.green} size={290} label="out of 100" />
    <div style={{ alignSelf: "center", fontFamily: SANS, fontSize: 30 * u, fontWeight: 700, color: C.green }}>Reads as its own site.</div>
  </Pad>;
}

function Brand() {
  const { u, vertical } = useUnit();
  const frame = useCurrentFrame();
  const a = range(frame, 10, 26), b = range(frame, 20, 34), c = range(frame, 30, 44);
  const glow = (p: number): CSSProperties => ({ opacity: p, filter: `blur(${(1 - p) * 12}px)`, transform: `translateY(${(1 - p) * 30 * u}px)` });
  return <AbsoluteFill style={{ alignItems: vertical ? "center" : "flex-end", justifyContent: vertical ? "flex-start" : "center", padding: vertical ? `${190 * u}px 0 0` : `0 ${200 * u}px 0 0` }}>
    <div style={{ display: "flex", flexDirection: "column", alignItems: vertical ? "center" : "flex-start", width: vertical ? undefined : 720 * u, textAlign: vertical ? "center" : "left" }}>
      <div style={{ fontFamily: SANS, fontSize: 250 * u, fontWeight: 800, letterSpacing: "-0.06em", color: C.ink, lineHeight: 0.9, textShadow: "0 0 70px rgba(20,200,107,0.5)", ...glow(a) }}>
        FIG<span style={{ color: C.green }}>.</span></div>
      <div style={{ fontFamily: SANS, fontSize: 52 * u, fontWeight: 600, color: C.copy, marginTop: 16 * u, ...glow(b) }}>See what makes your site generic.</div>
      <div style={{ marginTop: 34 * u, padding: `${16 * u}px ${30 * u}px`, borderRadius: 999, background: C.green, color: "#052012", fontFamily: SANS, fontSize: 34 * u, fontWeight: 800, ...glow(c) }}>
        Free scan · no account</div>
    </div>
  </AbsoluteFill>;
}

/* ------------------------------------------------------------------ video */

const SCREENS: Record<string, () => ReactNode> = {
  intro: Splash, url: UrlScreen, scan: ScanScreen, score: ScoreScreen, findings: FindingsScreen,
  connect: ConnectScreen, ai: AiScreen, approve: ApproveScreen, improve: ImproveScreen, end: EndScreen,
};

/** Screens swap with a quick slide inside the phone. */
function ScreenSlot({ id }: { id: string }) {
  const frame = useCurrentFrame();
  const inn = range(frame, 0, 10);
  const Screen = SCREENS[id];
  return <AbsoluteFill style={{ opacity: inn, transform: `translateY(${(1 - inn) * 40}px)` }}><Screen /></AbsoluteFill>;
}

export const Journey = ({ sound = false }: { sound?: boolean }) => {
  const span = (i: number) => ({ from: SCENES[i].at * BEAT, durationInFrames: (sceneEnd(i) - SCENES[i].at) * BEAT });
  return <AbsoluteFill style={{ background: "#030503" }}>
    {sound && <Audio src={staticFile("journey-sound.wav")} />}
    <Background />
    <Sequence {...span(6)}><AiRings /></Sequence>
    {SCENES.map((s, i) => s.left && <Sequence key={s.id} {...span(i)}><Caption left={s.left} right={s.right} top={s.id === "findings"} /></Sequence>)}
    <Phone>{SCENES.map((s, i) => <Sequence key={s.id} {...span(i)}><ScreenSlot id={s.id} /></Sequence>)}</Phone>
    <Sequence {...span(4)}><FindingCarousel /></Sequence>
    <Sequence {...span(9)}><Brand /></Sequence>
    <Streak />
  </AbsoluteFill>;
};
