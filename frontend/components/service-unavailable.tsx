"use client";
import Link from "next/link";
export function ServiceUnavailable({ message = "The workspace service is unavailable. Your data has not been replaced with sample content." }: { message?: string }) {
  return <div className="route-feedback" role="alert"><h2>Unable to load workspace</h2><p>{message}</p><div><button className="button" type="button" onClick={() => window.location.reload()}>Try again</button><Link className="secondary-button" href="/signin">Sign in</Link></div></div>;
}
