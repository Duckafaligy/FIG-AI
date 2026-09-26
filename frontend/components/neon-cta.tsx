import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

const u = (id: string) => `https://images.unsplash.com/photo-${id}?auto=format&fit=crop&w=560&h=420&q=70`;
const REEL = [
  [u("1515879218367-8466d910aaa4"), u("1544531586-fde5298cdd40"), u("1758873268023-15a6e6d739ed"), u("1587825140708-dfaf72ae4b04")],
  [u("1758873268745-dd2cf0d677b5"), u("1555066931-4365d14bab8c"), u("1559223694-98ed5e272fef"), u("1758876021859-bd2371d8f0a2")],
];

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
        <div className="neon-cta-reel" aria-hidden="true">
          {REEL.map((col, c) => (
            <div className="reel-col" key={c}>
              <div className="reel-track">
                {[...col, ...col].map((src, i) => <div className="reel-tile" key={i}><Image src={src} alt="" fill sizes="(max-width: 900px) 45vw, 280px" /></div>)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
