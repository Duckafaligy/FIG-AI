/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
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
    const backend = process.env.FIG_BACKEND_URL;
    if (!backend) return [];
    return [
      { source: "/api/:path*", destination: `${backend}/api/:path*` },
    ];
  },
};

export default nextConfig;
