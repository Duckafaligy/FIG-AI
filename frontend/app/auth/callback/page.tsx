import type { Metadata } from "next";
import { OAuthCallback } from "@/components/oauth-callback";
import { PublicNav } from "@/components/public-nav";

export const metadata: Metadata = { title: "Signing in - FIG", robots: { index: false, follow: false } };

export default function OAuthCallbackPage() {
  return (
    <div className="auth-simple neon-home">
      <PublicNav />
      <main className="page-shell auth-simple-main auth-simple-main--center">
        <OAuthCallback />
      </main>
    </div>
  );
}
