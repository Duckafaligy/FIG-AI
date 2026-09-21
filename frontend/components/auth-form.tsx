"use client";

import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { ArrowRight, CheckCircle2, Eye, EyeOff, LockKeyhole, Mail } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { siShopify } from "simple-icons/icons";
import { actions, DEMO_MODE } from "@/lib/api";
import { TRIAL_DAYS } from "@/lib/legal";
import { supabase, supabaseConfigured } from "@/lib/supabase";

function ProviderMark({ icon }: { icon: { path: string; hex: string; title: string } }) {
  return <svg className="provider-mark" aria-label={icon.title} role="img" viewBox="0 0 24 24"><path d={icon.path} fill={`#${icon.hex}`} /></svg>;
}

/**
 * The Google and Shopify buttons only ever showed "will be available once it's
 * connected". A button that promises a sign-in it cannot perform is worse than
 * no button, so they stay hidden until the flows behind them exist (Supabase's
 * Google provider, and a Shopify OAuth app). Flip this when they do.
 */
const SOCIAL_LOGIN_AVAILABLE = false;

export function AuthForm({ mode }: { mode: "signin" | "signup" }) {
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [requestedPlan, setRequestedPlan] = useState("");
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setEmail((params.get("email") ?? "").slice(0, 254));
    const plan = params.get("plan");
    if (plan && ["Starter", "Pro", "Scale", "Enterprise"].includes(plan)) setRequestedPlan(plan);
  }, []);
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
        ? await supabase.auth.signUp({
            email, password,
            // Without this the confirmation link goes to Supabase's Site URL,
            // which was still localhost:3000. It must also be allow-listed in
            // Supabase -> Authentication -> URL Configuration -> Redirect URLs.
            options: { data: { full_name: fullName }, emailRedirectTo: `${window.location.origin}/signin` },
          })
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
    } catch {
      setMessage("We couldn’t reach the sign-in service. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  const showPendingMessage = (provider: string) => {
    setMessage(`${provider} sign-in will be available once it's connected.`);
  };

  return (
    <form className={`auth-form auth-form--${mode}`} onSubmit={submit}>
      <div className="auth-heading">
        <span className="eyebrow">{signup ? "Start your workspace" : "Welcome back"}</span>
        <h2>{signup ? "Create your FIG account" : "Sign in to FIG"}</h2>
        <p>{signup ? "Start your free trial and see how FIG can help your team get found everywhere." : "Sign in to continue building high-performing content."}</p>
      </div>

      {signup && requestedPlan && <p className="form-message">Interested in {requestedPlan} · plan preview only. No subscription has been started.</p>}
      <div className="auth-fields">
        {signup && <label className="auth-field" htmlFor="full-name"><span>Full name</span><input id="full-name" name="full-name" required autoComplete="name" placeholder="LaunchVault team" /></label>}
        <label className="auth-field" htmlFor="email"><span>{signup ? "Work email" : "Email"}</span><div className="input-with-icon"><Mail size={18} aria-hidden="true" /><input id="email" name="email" value={email} onChange={(event) => setEmail(event.target.value)} required type="email" autoComplete="email" placeholder="you@company.com" /></div></label>
        {signup && <label className="auth-field" htmlFor="company"><span>Company name</span><input id="company" name="company" required autoComplete="organization" placeholder="LaunchVault" /></label>}
        {signup && <label className="auth-field" htmlFor="website"><span>Website URL</span><input id="website" name="website" required type="url" placeholder="https://launchvault.ca" /></label>}
        <label className="auth-field" htmlFor="password"><span>Password</span><div className="input-with-icon input-with-icon--password"><LockKeyhole size={18} aria-hidden="true" /><input id="password" name="password" required minLength={8} type={showPassword ? "text" : "password"} autoComplete={signup ? "new-password" : "current-password"} placeholder={signup ? "Create a password" : "Enter your password"} /><button className="password-toggle" type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></label>
      </div>

      {!signup && <div className="form-row"><label className="check"><input type="checkbox" />Remember me</label><Link className="text-button" href="/forgot-password">Forgot password?</Link></div>}
      <button className="button auth-submit" type="submit" disabled={busy} aria-busy={busy}>{busy ? "Please wait…" : signup ? "Start free trial" : "Sign in"}{!busy && <ArrowRight size={18} />}</button>
      {signup && <div className="trial-reassurance" aria-label="Trial terms"><span><CheckCircle2 size={14} />{TRIAL_DAYS}-day free trial</span><span><CheckCircle2 size={14} />No credit card required</span><span><CheckCircle2 size={14} />Cancel anytime</span></div>}

      {SOCIAL_LOGIN_AVAILABLE && (
        <>
          <div className="auth-separator"><span>or continue with</span></div>
          <div className="auth-social-buttons">
            <button className="oauth-button" type="button" onClick={() => showPendingMessage("Google")}><Image className="provider-mark" src="/brands/google-g.png" width={23} height={23} alt="" unoptimized />Continue with Google</button>
            <button className="oauth-button" type="button" onClick={() => showPendingMessage("Shopify")}><ProviderMark icon={siShopify} />Continue with Shopify</button>
          </div>
        </>
      )}
      {signup && <div className="check check--terms"><input id="terms" required type="checkbox" aria-label="Agree to the terms and privacy policy, and confirm you are at least 13" /><div><label htmlFor="terms">I&rsquo;m at least 13 and I agree to the </label><Link href="/terms" target="_blank">Terms of Service</Link> and <Link href="/privacy" target="_blank">Privacy Policy</Link>.</div></div>}
      {message && <p className="form-message" role="status">{message}</p>}
      <p className="auth-switch">{signup ? "Already have an account?" : "Don’t have an account?"} <Link href={signup ? "/signin" : "/signup"}>{signup ? "Sign in" : "Sign up for free"}</Link></p>
    </form>
  );
}
