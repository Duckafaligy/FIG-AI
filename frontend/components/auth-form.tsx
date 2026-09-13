"use client";

import Link from "next/link";
import { ArrowRight, Eye, LockKeyhole, Mail } from "lucide-react";
import { FormEvent, useState } from "react";

export function AuthForm({ mode }: { mode: "signin" | "signup" }) {
  const [message, setMessage] = useState("");
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage("The interface is ready. Secure authentication will be connected in the backend phase.");
  };
  const signup = mode === "signup";

  return (
    <form className="auth-form" onSubmit={submit}>
      <div className="auth-heading">
        <span className="eyebrow">{signup ? "Start your workspace" : "Welcome back"}</span>
        <h1>{signup ? "Create your FIG account" : "Sign in to FIG"}</h1>
        <p>{signup ? "Start building content that gets your brand found everywhere." : "Continue building high-performing content."}</p>
      </div>
      {signup && <label>Full name<input required autoComplete="name" placeholder="Jane Cooper" /></label>}
      <label>Email<div className="input-with-icon"><Mail size={18} /><input required type="email" autoComplete="email" placeholder="you@company.com" /></div></label>
      {signup && <label>Company name<input required autoComplete="organization" placeholder="Acme Inc." /></label>}
      {signup && <label>Website URL<input required type="url" placeholder="https://yourcompany.com" /></label>}
      <label>Password<div className="input-with-icon"><LockKeyhole size={18} /><input required minLength={8} type="password" autoComplete={signup ? "new-password" : "current-password"} placeholder={signup ? "At least 8 characters" : "Enter your password"} /><Eye size={18} /></div></label>
      {!signup && <div className="form-row"><label className="check"><input type="checkbox" />Remember me</label><Link href="#">Forgot password?</Link></div>}
      {signup && <label className="check"><input required type="checkbox" />I agree to the <Link href="#">Terms</Link> and <Link href="#">Privacy Policy</Link>.</label>}
      <button className="button auth-submit" type="submit">{signup ? "Start free trial" : "Sign in"}<ArrowRight size={18} /></button>
      <div className="auth-separator"><span>or continue with</span></div>
      <button className="oauth-button" type="button"><b className="google-mark">G</b>Continue with Google</button>
      <button className="oauth-button" type="button"><b className="shopify-mark">S</b>Continue with Shopify</button>
      {message && <p className="form-message" role="status">{message}</p>}
      <p className="auth-switch">{signup ? "Already have an account?" : "Don’t have an account?"} <Link href={signup ? "/signin" : "/signup"}>{signup ? "Sign in" : "Sign up for free"}</Link></p>
    </form>
  );
}
