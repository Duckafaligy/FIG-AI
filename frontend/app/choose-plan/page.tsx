import type { Metadata } from "next";
import { AuthFooter } from "@/components/auth-footer";
import { PlanPicker } from "@/components/plan-picker";
import { PublicNav } from "@/components/public-nav";

export const metadata: Metadata = {
  title: "Choose a plan - FIG",
  robots: { index: false },
};

export default function ChoosePlanPage() {
  return (
    <div className="auth-simple neon-home">
      <PublicNav />
      <main className="page-shell" style={{ padding: "72px 0 96px" }}>
        <PlanPicker />
      </main>
      <AuthFooter />
    </div>
  );
}
