import type { Metadata } from "next";
import { AuthForm } from "@/components/auth-form";
import { AuthFooter } from "@/components/auth-footer";
import { PublicNav } from "@/components/public-nav";

export const metadata: Metadata = {
  title: "Sign in - FIG",
  description: "Sign in to your FIG workspace to see your sites, findings and scan history.",
  alternates: { canonical: "/signin" },
};

export default function SignInPage() {
  return (
    <div className="auth-simple neon-home">
      <PublicNav />
      <main className="page-shell auth-simple-main">
        <div className="auth-simple-copy">
          <h1>Welcome back.</h1>
          <p>Your sites, findings and scan history are where you left them.</p>
        </div>
        <div className="auth-simple-card"><AuthForm mode="signin" /></div>
      </main>
      <AuthFooter />
    </div>
  );
}
