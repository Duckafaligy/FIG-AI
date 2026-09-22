/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async headers() {
    const paths = process.env.NEXT_PUBLIC_DEMO_MODE === "1"
      ? ["/:path*"]
      : ["/app/:path*", "/projects", "/signin", "/signup", "/forgot-password", "/reset-password", "/report/:path*", "/library"];
    return paths.map(source => ({ source, headers: [{ key: "X-Robots-Tag", value: "noindex, nofollow" }] }));
  },
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.unsplash.com" }
    ]
  },
  // Proxies every browser call to `/api/*` through to the real backend
  // (FIG_BACKEND_URL, server-only -- never NEXT_PUBLIC_*). This is required,
  // not cosmetic: the backend's session cookie can only ever be read back by
  // this app's own Server Components (lib/api.ts's apiServer, used by every
  // SSR auth gate and live data fetch) if it was issued by *this app's own
  // origin*. A cookie set by a genuinely different domain -- which is what
  // happens if the browser talks to the backend directly -- is invisible to
  // this app's cookies() no matter what SameSite says: browsers only ever
  // attach a cookie to requests aimed at the domain that issued it. Routing
  // every /api call through this same origin makes the cookie belong to
  // this app's domain, which both the browser's later fetches and this
  // app's own Server Components need. Local dev doesn't need this (see
  // lib/api.ts) since localhost:3001/localhost:8000 already count as
  // same-site regardless of port -- this only matters once deployed.
  async rewrites() {
    const backend = process.env.FIG_BACKEND_URL?.trim().replace(/\/+$/, "");
    if (process.env.VERCEL && process.env.NEXT_PUBLIC_DEMO_MODE !== "1" && !backend) {
      throw new Error("FIG_BACKEND_URL is required for a live Vercel deployment.");
    }
    if (!backend) return [];
    const target = new URL(backend);
    if (!["http:", "https:"].includes(target.protocol) || target.username || target.password || target.search || target.hash || target.pathname !== "/") {
      throw new Error("FIG_BACKEND_URL must be an HTTP(S) origin without credentials, path, query, or fragment.");
    }
    return [
      { source: "/api/:path*", destination: `${backend}/api/:path*` },
      // apiUrl() (lib/api.ts) is relative in production, and it's used for
      // both fetches AND the OAuth "Connect" <a href>, e.g. Settings'
      // Google Analytics/Search Console buttons. Without this, that link
      // resolves to this app's own domain instead of the backend's --
      // there's no /oauth route here at all, so it 404s.
      { source: "/oauth/:path*", destination: `${backend}/oauth/:path*` },
      // The free, unauthenticated scan (POST /scan, GET /scan/{id}, GET
      // /scan/library) doesn't need this for cookie reasons -- it carries no
      // session at all -- but proxying it anyway keeps every backend call
      // the browser makes on this same origin, consistently, rather than
      // exposing the Render domain directly for just this one feature.
      { source: "/scan", destination: `${backend}/scan` },
      { source: "/scan/:path*", destination: `${backend}/scan/:path*` },
    ];
  },
};

export default nextConfig;
