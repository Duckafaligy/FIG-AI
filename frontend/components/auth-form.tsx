"use client";

import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { ArrowRight, CheckCircle2, Eye, EyeOff, LockKeyhole, Mail } from "lucide-react";
import { FormEvent, useState } from "react";
import { siShopify } from "simple-icons/icons";
import { actions, DEMO_MODE } from "@/lib/api";
import { supabase, supabaseConfigured } from "@/lib/supabase";
import { PreviewInfo } from "./preview-info";

function ProviderMark({ icon }: { icon: { path: string; hex: string; title: string } }) {
  return <svg className="provider-mark" aria-label={icon.title} role="img" viewBox="0 0 24 24"><path d={icon.path} fill={`#${icon.hex}`} /></svg>;
}

export function AuthForm({ mode }: { mode: "signin" | "signup" }) {
  const [message, setMessage] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const signup = mode === "signup";
  const router = useRouter();

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (DEMO_MODE) {
      setMessage("This is a demo deployment — sign-in is disabled here so it can never touch a real account.");
      return;
    }
    if (!supabaseConfigured) {
      setMessage("Authentication isn't configured on this deployment (missing Supabase env vars).");
      return;
    }
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    const company = String(form.get("company") ?? "").trim();
    const fullName = String(form.get("full-name") ?? "").trim();

    setBusy(true);
    setMessage("");
    try {
      const { data, error } = signup
        ? await supabase.auth.signUp({ email, password, options: { data: { full_name: fullName } } })
        : await supabase.auth.signInWithPassword({ email, password });

      if (error) {
        setMessage(error.message);
        return;
      }
      if (!data.session) {
        // Signup with email confirmation required: Supabase creates the user
        // but withholds a session until the link in that email is clicked.
        setMessage("Check your email to confirm your account, then sign in.");
        return;
      }

      const established = await actions.signIn(data.session.access_token, company);
      if (!established.ok) {
        setMessage(established.error);
        return;
      }
      router.push("/app");
    } finally {
      setBusy(false);
    }
  };

  const showPendingMessage = (provider?: string) => {
    setMessage(provider ? `${provider} sign-in will be available once it's connected.` : "Password recovery will be available once it's connected.");
  };

  return (
    <form className={`auth-form auth-form--${mode}`} onSubmit={submit}>
      <div className="auth-heading">
        <span className="eyebrow">{signup ? "Start your workspace" : "Welcome back"}</span>
        <h2>{signup ? "Create your FIG account" : "Sign in to FIG"}</h2>
        <p>{signup ? "Start your free trial and see how FIG can help your team get found everywhere." : "Sign in to continue building high-performing content."}</p>
      </div>

      <div className="auth-fields">
        {signup && <label className="auth-field" htmlFor="full-name"><span>Full name</span><input id="full-name" name="full-name" required autoComplete="name" placeholder="LaunchVault team" /></label>}
        <label className="auth-field" htmlFor="email"><span>{signup ? "Work email" : "Email"}</span><div className="input-with-icon"><Mail size={18} aria-hidden="true" /><input id="email" name="email" required type="email" autoComplete="email" placeholder="you@company.com" /></div></label>
        {signup && <label className="auth-field" htmlFor="company"><span>Company name</span><input id="company" name="company" required autoComplete="organization" placeholder="LaunchVault" /></label>}
        {signup && <label className="auth-field" htmlFor="website"><span>Website URL</span><input id="website" name="website" required type="url" placeholder="https://launchvault.ca" /></label>}
        <label className="auth-field" htmlFor="password"><span>Password</span><div className="input-with-icon input-with-icon--password"><LockKeyhole size={18} aria-hidden="true" /><input id="password" name="password" required minLength={8} type={showPassword ? "text" : "password"} autoComplete={signup ? "new-password" : "current-password"} placeholder={signup ? "Create a password" : "Enter your password"} /><button className="password-toggle" type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></label>
      </div>

      {!signup && <div className="form-row"><label className="check"><input type="checkbox" />Remember me</label><button className="text-button" type="button" onClick={() => showPendingMessage()}>Forgot password?</button></div>}
      <button className="button auth-submit" type="submit" disabled={busy} aria-busy={busy}>{busy ? "Please wait…" : signup ? "Start free trial" : "Sign in"}{!busy && <ArrowRight size={18} />}</button>
      {signup && <div className="trial-reassurance" aria-label="Trial terms"><span><CheckCircle2 size={14} />14-day free trial</span><span><CheckCircle2 size={14} />No credit card required</span><span><CheckCircle2 size={14} />Cancel anytime</span></div>}

      <div className="auth-separator"><span>or continue with</span></div>
      <div className="auth-social-buttons">
        <button className="oauth-button" type="button" onClick={() => showPendingMessage("Google")}><Image className="provider-mark" src="/brands/google-g.png" width={23} height={23} alt="" unoptimized />Continue with Google</button>
        <button className="oauth-button" type="button" onClick={() => showPendingMessage("Shopify")}><ProviderMark icon={siShopify} />Continue with Shopify</button>
      </div>
      {signup && <div className="check check--terms"><input id="terms" required type="checkbox" aria-label="Agree to terms and privacy policy" /><div><label htmlFor="terms">I agree to the </label><PreviewInfo label="Terms & Conditions" message="FIG’s published terms aren’t live yet. Creating an account here does start a real Supabase sign-up, though — no billing or subscription starts until you add a payment method." /> and <PreviewInfo label="Privacy Policy" message="FIG’s published privacy policy isn’t live yet. The email and password you enter here are sent to Supabase Auth to create a real account." />.</div></div>}
      {message && <p className="form-message" role="status">{message}</p>}
      <p className="auth-switch">{signup ? "Already have an account?" : "Don’t have an account?"} <Link href={signup ? "/signin" : "/signup"}>{signup ? "Sign in" : "Sign up for free"}</Link></p>
    </form>
  );
}
