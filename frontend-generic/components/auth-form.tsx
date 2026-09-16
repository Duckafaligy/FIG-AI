"use client";

import Link from "next/link";
import Image from "next/image";
import { ArrowRight, CheckCircle2, Eye, EyeOff, LockKeyhole, Mail } from "lucide-react";
import { FormEvent, useState } from "react";
import { siShopify } from "simple-icons/icons";
import { PreviewInfo } from "./preview-info";

function ProviderMark({ icon }: { icon: { path: string; hex: string; title: string } }) {
  return <svg className="provider-mark" aria-label={icon.title} role="img" viewBox="0 0 24 24"><path d={icon.path} fill={`#${icon.hex}`} /></svg>;
}

export function AuthForm({ mode }: { mode: "signin" | "signup" }) {
  const [message, setMessage] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const signup = mode === "signup";

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage("This is a frontend preview. Secure authentication will be connected during the backend phase.");
  };

  const showPendingMessage = (provider?: string) => {
    setMessage(provider ? `${provider} sign-in will be available once authentication is connected.` : "Password recovery will be available once authentication is connected.");
  };

  return (
    <form className={`auth-form auth-form--${mode}`} onSubmit={submit}>
      <div className="auth-heading">
        <span className="eyebrow">{signup ? "Start your workspace" : "Welcome back"}</span>
        <h2>{signup ? "Create your FIG account" : "Sign in to FIG"}</h2>
        <p>{signup ? "Start your free trial and see how FIG can help your team get found everywhere." : "Sign in to continue building high-performing content."}</p>
      </div>

      <div className="auth-fields">
        {signup && <label className="auth-field" htmlFor="full-name"><span>Full name</span><input id="full-name" required autoComplete="name" placeholder="Demo workspace team" /></label>}
        <label className="auth-field" htmlFor="email"><span>{signup ? "Work email" : "Email"}</span><div className="input-with-icon"><Mail size={18} aria-hidden="true" /><input id="email" required type="email" autoComplete="email" placeholder="you@company.com" /></div></label>
        {signup && <label className="auth-field" htmlFor="company"><span>Company name</span><input id="company" required autoComplete="organization" placeholder="Demo workspace" /></label>}
        {signup && <label className="auth-field" htmlFor="website"><span>Website URL</span><input id="website" required type="url" placeholder="https://demo-workspace.example" /></label>}
        <label className="auth-field" htmlFor="password"><span>Password</span><div className="input-with-icon input-with-icon--password"><LockKeyhole size={18} aria-hidden="true" /><input id="password" required minLength={8} type={showPassword ? "text" : "password"} autoComplete={signup ? "new-password" : "current-password"} placeholder={signup ? "Create a password" : "Enter your password"} /><button className="password-toggle" type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></label>
      </div>

      {!signup && <div className="form-row"><label className="check"><input type="checkbox" />Remember me</label><button className="text-button" type="button" onClick={() => showPendingMessage()}>Forgot password?</button></div>}
      <button className="button auth-submit" type="submit">{signup ? "Start free trial" : "Sign in"}<ArrowRight size={18} /></button>
      {signup && <div className="trial-reassurance" aria-label="Trial terms"><span><CheckCircle2 size={14} />14-day free trial</span><span><CheckCircle2 size={14} />No credit card required</span><span><CheckCircle2 size={14} />Cancel anytime</span></div>}
      <p className="auth-preview-note">Frontend preview — no account or payment is created yet.</p>

      <div className="auth-separator"><span>or continue with</span></div>
      <div className="auth-social-buttons">
        <button className="oauth-button" type="button" onClick={() => showPendingMessage("Google")}><Image className="provider-mark" src="/brands/google-g.png" width={23} height={23} alt="" unoptimized />Continue with Google</button>
        <button className="oauth-button" type="button" onClick={() => showPendingMessage("Shopify")}><ProviderMark icon={siShopify} />Continue with Shopify</button>
      </div>
      {signup && <div className="check check--terms"><input id="terms" required type="checkbox" aria-label="Agree to terms and privacy policy" /><div><label htmlFor="terms">I agree to the </label><PreviewInfo label="Terms & Conditions" message="FIG’s terms will be published before account creation is enabled. This frontend preview does not create an account or start a subscription." /> and <PreviewInfo label="Privacy Policy" message="The privacy policy will be published before authentication is enabled. This form does not send or store the information you enter." />.</div></div>}
      {message && <p className="form-message" role="status">{message}</p>}
      <p className="auth-switch">{signup ? "Already have an account?" : "Don’t have an account?"} <Link href={signup ? "/signin" : "/signup"}>{signup ? "Sign in" : "Sign up for free"}</Link></p>
    </form>
  );
}
