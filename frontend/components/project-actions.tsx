"use client";
import { useEffect, useRef, useState, type FormEvent } from "react";
import styles from "./project-actions.module.css";
import { MoreVertical } from "lucide-react";
import { actions, apiSend } from "@/lib/api";

export function ProjectActions({ id, name, onChange }: { id: string; name: string; onChange: () => void }) {
  const menu = useRef<HTMLDetailsElement>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const [action, setAction] = useState<"rename" | "remove">("rename");
  const [value, setValue] = useState(name);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    const closeOutside = (event: PointerEvent) => {
      if (menu.current && !menu.current.contains(event.target as Node)) menu.current.open = false;
    };
    document.addEventListener("pointerdown", closeOutside);
    return () => document.removeEventListener("pointerdown", closeOutside);
  }, []);
  function open(next: "rename" | "remove") {
    setAction(next); setValue(name); setError("");
    if (menu.current) menu.current.open = false;
    dialog.current?.showModal();
  }
  async function submit(event: FormEvent) {
    event.preventDefault(); if (busy) return;
    setBusy(true); setError("");
    try {
      const result = action === "remove" ? await actions.removeProject(id)
        : await apiSend(`/api/projects/${encodeURIComponent(id)}`, "PATCH", { name: value.trim() });
      if (!result.ok) { setError(result.error); return; }
      dialog.current?.close(); onChange();
    } catch { setError("The request was interrupted. Refresh the project list to check its current state before retrying."); }
    finally { setBusy(false); }
  }
  return <div className={`project-actions ${styles.actions}`}>
    <details ref={menu} onKeyDown={event => { if (event.key === "Escape" && menu.current) { menu.current.open = false; menu.current.querySelector("summary")?.focus(); } }}>
      <summary aria-label={`Actions for ${name}`}><MoreVertical size={18} /></summary>
      <div className="project-actions-popover"><button type="button" onClick={() => open("rename")}>Rename project</button><button type="button" onClick={() => open("remove")}>Remove project</button></div>
    </details>
    <dialog ref={dialog} className={`preview-info-dialog ${styles.dialog}`} aria-label={`${action === "rename" ? "Rename" : "Remove"} project`} onClose={() => menu.current?.querySelector("summary")?.focus()} onCancel={event => { if (busy) event.preventDefault(); }}>
      <h2>{action === "rename" ? "Rename project" : `Remove ${name}?`}</h2>
      <form onSubmit={submit} className="auth-fields">
        {action === "rename" ? <label className="auth-field">Project name<input required maxLength={80} value={value} onChange={event => setValue(event.target.value)} /></label>
          : <p>This removes the project from your active workspace and stops counting it toward per-site billing. Its audit history is retained. Your website is not deleted.</p>}
        {error && <p role="alert" className="form-message">{error}</p>}
        <button type="submit" className="button" disabled={busy}>{busy ? "Saving…" : action === "rename" ? "Save name" : "Remove project"}</button>
        <button type="button" className="secondary-button" disabled={busy} onClick={() => dialog.current?.close()}>Cancel</button>
      </form>
    </dialog>
  </div>;
}
