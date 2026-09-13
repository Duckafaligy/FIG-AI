"use client";

import { useEffect, useRef } from "react";

/**
 * Ambient hero aura: soft orange + blue glows on a near-black base. The orbs
 * drift on slow Lissajous paths and each eases toward the cursor, and a warm
 * glow trails the pointer directly — so moving the mouse visibly pushes the
 * light around. Canvas 2D with additive ("lighter") blending; no library.
 *
 * - Transparent canvas over the page's --bg, so glows read as light on black.
 * - Edges fade via a radial mask; pointer-events: none so clicks pass through
 *   (cursor interaction still works — we read mousemove on window).
 * - <768px / reduced-motion: one static frame, no loop, no pointer tracking.
 */
export function HeroBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const prefersReduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let width = 0;
    let height = 0;

    type Orb = {
      c: [number, number, number];
      hx: number; // home x (0..1)
      hy: number; // home y (0..1)
      r: number; // radius as fraction of the larger side
      ax: number; // drift amplitude x
      ay: number; // drift amplitude y
      sx: number; // drift speed x
      sy: number; // drift speed y
      ph: number; // phase
      follow: number; // 0..1 pull toward the cursor
      alpha: number;
    };

    // Warm (orange, brand accent) + cool (blue) aura, biased center/right so
    // the left-column headline keeps its contrast.
    const orbs: Orb[] = [
      // orange, just left of center
      { c: [224, 90, 51], hx: 0.5, hy: 0.44, r: 0.46, ax: 0.05, ay: 0.04, sx: 0.00021, sy: 0.00017, ph: 0.0, follow: 0.14, alpha: 0.16 },
      // blue, right — the strong cool pole
      { c: [42, 112, 232], hx: 0.72, hy: 0.55, r: 0.55, ax: 0.06, ay: 0.05, sx: -0.00016, sy: 0.00023, ph: 1.7, follow: 0.1, alpha: 0.2 },
      // warm accent, most cursor-reactive
      { c: [235, 122, 60], hx: 0.44, hy: 0.52, r: 0.34, ax: 0.05, ay: 0.06, sx: 0.00014, sy: -0.0002, ph: 3.3, follow: 0.24, alpha: 0.13 },
      // cool, upper-left — puts blue on both sides so the two interleave
      { c: [70, 160, 240], hx: 0.34, hy: 0.34, r: 0.42, ax: 0.05, ay: 0.04, sx: 0.00019, sy: 0.00012, ph: 4.8, follow: 0.16, alpha: 0.16 },
    ];

    // Eased pointer position (normalized to the canvas box).
    const mouse = { x: 0.55, y: 0.42, tx: 0.55, ty: 0.42 };

    const resize = () => {
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      canvas.width = Math.max(1, Math.floor(width * dpr));
      canvas.height = Math.max(1, Math.floor(height * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();

    const isSmall = window.innerWidth < 768;

    const drawGlow = (
      x: number,
      y: number,
      r: number,
      c: [number, number, number],
      alpha: number
    ) => {
      const g = ctx.createRadialGradient(x, y, 0, x, y, r);
      g.addColorStop(0, `rgba(${c[0]},${c[1]},${c[2]},${alpha})`);
      g.addColorStop(0.5, `rgba(${c[0]},${c[1]},${c[2]},${alpha * 0.35})`);
      g.addColorStop(1, `rgba(${c[0]},${c[1]},${c[2]},0)`);
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    };

    const drawFrame = (t: number) => {
      ctx.clearRect(0, 0, width, height);
      ctx.globalCompositeOperation = "lighter";

      mouse.x += (mouse.tx - mouse.x) * 0.06;
      mouse.y += (mouse.ty - mouse.y) * 0.06;

      const larger = Math.max(width, height) || 1;
      const mx = mouse.x * width;
      const my = mouse.y * height;

      for (const o of orbs) {
        const driftX = o.hx + Math.sin(t * o.sx + o.ph) * o.ax;
        const driftY = o.hy + Math.cos(t * o.sy + o.ph) * o.ay;
        let px = driftX * width;
        let py = driftY * height;
        px += (mx - px) * o.follow;
        py += (my - py) * o.follow;
        drawGlow(px, py, o.r * larger, o.c, o.alpha);
      }

      // Warm glow that trails the cursor directly — the clear interaction.
      // Kept modest so it doesn't let orange overwhelm the blue.
      drawGlow(mx, my, 0.24 * larger, [236, 128, 66], 0.12);

      ctx.globalCompositeOperation = "source-over";
    };

    let raf = 0;
    let t = 0;

    if (isSmall || prefersReduced) {
      drawFrame(1200);
      window.addEventListener("resize", resize);
      return () => window.removeEventListener("resize", resize);
    }

    const onMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const nx = (e.clientX - rect.left) / (rect.width || 1);
      const ny = (e.clientY - rect.top) / (rect.height || 1);
      // Allow a little overscan so the aura can lean off-canvas toward the cursor.
      mouse.tx = Math.min(1.25, Math.max(-0.25, nx));
      mouse.ty = Math.min(1.4, Math.max(-0.4, ny));
    };

    const loop = () => {
      t += 1;
      drawFrame(t);
      raf = requestAnimationFrame(loop);
    };

    window.addEventListener("resize", resize);
    window.addEventListener("mousemove", onMove);
    loop();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMove);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className="pointer-events-none absolute inset-0 h-full w-full"
      style={{
        maskImage:
          "radial-gradient(75% 75% at 55% 42%, #000 55%, transparent 100%)",
        WebkitMaskImage:
          "radial-gradient(75% 75% at 55% 42%, #000 55%, transparent 100%)",
      }}
    />
  );
}
