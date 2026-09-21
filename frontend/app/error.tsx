"use client";
import Link from "next/link";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return <div className="route-feedback" role="alert"><h2>This page couldn’t load.</h2><p>Try again, or return to your projects.</p><div><button type="button" className="button" onClick={reset}>Try again</button><Link className="secondary-button" href="/projects">Open projects</Link></div></div>;
}
