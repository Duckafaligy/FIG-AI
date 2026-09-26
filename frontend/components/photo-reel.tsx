import Image from "next/image";

const u = (id: string) => `https://images.unsplash.com/photo-${id}?auto=format&fit=crop&w=560&h=420&q=70`;

export const CTA_REEL = [
  [u("1515879218367-8466d910aaa4"), u("1544531586-fde5298cdd40"), u("1758873268023-15a6e6d739ed"), u("1587825140708-dfaf72ae4b04")],
  [u("1758873268745-dd2cf0d677b5"), u("1555066931-4365d14bab8c"), u("1559223694-98ed5e272fef"), u("1758876021859-bd2371d8f0a2")],
];
// Coding, working in dashboards, team discussions.
export const AUTH_REEL = [
  [u("1515879218367-8466d910aaa4"), u("1542744173-05336fcc7ad4"), u("1758873268745-dd2cf0d677b5"), u("1551288049-bebda4e38f71")],
  [u("1460925895917-afdab827c52f"), u("1758873268023-15a6e6d739ed"), u("1555066931-4365d14bab8c"), u("1758876021859-bd2371d8f0a2")],
];

/** Two columns of photos scrolling in opposite directions; decorative. */
export function PhotoReel({ columns, className = "" }: { columns: string[][]; className?: string }) {
  return (
    <div className={`photo-reel ${className}`} aria-hidden="true">
      {columns.map((col, c) => (
        <div className="reel-col" key={c}>
          <div className="reel-track">
            {[...col, ...col].map((src, i) => <div className="reel-tile" key={i}><Image src={src} alt="" fill sizes="(max-width: 900px) 45vw, 280px" /></div>)}
          </div>
        </div>
      ))}
    </div>
  );
}
