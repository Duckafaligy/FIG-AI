import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { CTA_REEL, PhotoReel } from "./photo-reel";

export function NeonCta() {
  return (
    <section className="neon-cta-section">
      <div className="page-shell neon-cta-grid neon-cta-grid--media">
        <div className="neon-cta-copy">
          <h2>What could your website do next?</h2>
          <div className="neon-cta-actions">
            <Link className="button" href="/signin">Sign in <ArrowUpRight size={17} /></Link>
            <Link className="secondary-button" href="/signup">Sign up <ArrowUpRight size={17} /></Link>
          </div>
        </div>
        <PhotoReel columns={CTA_REEL} className="neon-cta-reel" />
      </div>
    </section>
  );
}
