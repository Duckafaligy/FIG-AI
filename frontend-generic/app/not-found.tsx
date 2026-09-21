import Link from "next/link";
export default function NotFound() {
  return <main className="route-feedback"><span className="eyebrow">404 · Page not found</span><h1>Let’s get you back on track.</h1><p>This page may have moved. Your workspace is still one click away.</p><div><Link className="button" href="/projects">Open projects</Link><Link className="secondary-button" href="/">FIG home</Link></div></main>;
}
