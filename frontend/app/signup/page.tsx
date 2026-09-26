import type { Metadata } from "next";
import { AuthForm } from "@/components/auth-form";
import { AuthFooter } from "@/components/auth-footer";
import { PhotoReel, AUTH_REEL } from "@/components/photo-reel";
import { PublicNav } from "@/components/public-nav";
import { TRIAL_DAYS } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Create your account - FIG",
  description: `Create a FIG account for a ${TRIAL_DAYS}-day free trial with no card, then scan your sites and track what changes.`,
  alternates: { canonical: "/signup" },
};

export default function SignUpPage() {
  return (
    <div className="auth-simple neon-home">
      <PublicNav />
      <main className="page-shell auth-simple-main">
        <div className="auth-simple-copy">
          <h1>Start with your website.</h1>
          <p>Create an account for a {TRIAL_DAYS}-day trial with no card. Or run a free scan with no account at all.</p>
          <PhotoReel columns={AUTH_REEL} className="auth-reel" />
        </div>
        <div className="auth-simple-card"><AuthForm mode="signup" /></div>
      </main>
      <AuthFooter />
    </div>
  );
}
