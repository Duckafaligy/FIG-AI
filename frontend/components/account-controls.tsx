"use client";

import { FormEvent, useState } from "react";
import { AlertTriangle, Pencil } from "lucide-react";
import { actions } from "@/lib/api";
import styles from "./account-controls.module.css";

/**
 * Rename the workspace, and delete it. Both call the workspace API (see
 * app/webapp.py); deletion is the "on request" the privacy policy promises, done
 * by the person themselves. It cancels the subscription first, and if that
 * fails nothing is deleted, so the message here says exactly that.
 */
export function AccountControls({ currentName, email }: { currentName: string; email: string }) {
  const [name, setName] = useState(currentName);
  const [renameMsg, setRenameMsg] = useState("");
  const [renaming, setRenaming] = useState(false);

  const [open, setOpen] = useState(false);
  const [confirm, setConfirm] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteMsg, setDeleteMsg] = useState("");
  const [done, setDone] = useState<null | { signInRecord: boolean }>(null);

  const rename = async (event: FormEvent) => {
    event.preventDefault();
    setRenaming(true);
    setRenameMsg("");
    const result = await actions.renameWorkspace(name);
    setRenaming(false);
    if (!result.ok) { setRenameMsg(result.error); return; }
    setRenameMsg("Saved.");
    window.setTimeout(() => window.location.reload(), 600);
  };

  const remove = async (event: FormEvent) => {
    event.preventDefault();
    setDeleting(true);
    setDeleteMsg("");
    const result = await actions.deleteAccount(confirm);
    setDeleting(false);
    if (!result.ok) { setDeleteMsg(result.error); return; }
    setDone({ signInRecord: result.data.sign_in_record_deleted });
  };

  if (done) {
    return (
      <section className={`settings-surface ${styles.done}`} role="status">
        <div className="settings-surface-heading"><div><h3>Workspace deleted</h3>
          <p>Your workspace, its sites, scans, drafts and connected services are gone, and your subscription (if you had one) has been cancelled.
            {done.signInRecord ? "" : " Your sign-in record could not be removed automatically; email us and we will remove it."}</p></div></div>
        <a className="button button--small" href="/">Back to the homepage</a>
      </section>
    );
  }

  return (
    <>
      <section className="settings-surface">
        <div className="settings-surface-heading"><div><h3>Workspace name</h3><p>Shown across your workspace and on invoices.</p></div><Pencil size={19} aria-hidden="true" /></div>
        <form className={styles.row} onSubmit={rename}>
          <label htmlFor="workspace-name" className={styles.sr}>Workspace name</label>
          <input id="workspace-name" value={name} onChange={(e) => setName(e.target.value)} minLength={2} maxLength={80} required />
          <button className="button button--small" type="submit" disabled={renaming || name.trim() === currentName || name.trim().length < 2}>{renaming ? "Saving…" : "Save name"}</button>
        </form>
        {renameMsg && <p className="form-message" role="status">{renameMsg}</p>}
      </section>

      <section className={`settings-surface ${styles.danger}`}>
        <div className="settings-surface-heading"><div><h3>Delete workspace</h3><p>Permanently remove this workspace and everything in it.</p></div><AlertTriangle size={19} aria-hidden="true" /></div>
        {!open ? (
          <button type="button" className={styles.dangerButton} onClick={() => setOpen(true)}>Delete this workspace…</button>
        ) : (
          <form onSubmit={remove} className={styles.confirm}>
            <p>This deletes your sites, scan history, content drafts, connected services (including their stored credentials), API keys and sign-in. If you have a subscription it is cancelled first, and if that can&rsquo;t be done nothing is deleted. <strong>This cannot be undone.</strong> Payment records are kept by Stripe as the law requires.</p>
            <label htmlFor="delete-confirm">Type your account email{email && email !== "—" ? <> (<code>{email}</code>)</> : null} to confirm</label>
            <input id="delete-confirm" type="email" autoComplete="off" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
            <div className={styles.actions}>
              <button type="submit" className={styles.dangerButton} disabled={deleting || !confirm.trim()}>{deleting ? "Deleting…" : "Delete everything"}</button>
              <button type="button" className="secondary-button" onClick={() => { setOpen(false); setConfirm(""); setDeleteMsg(""); }} disabled={deleting}>Cancel</button>
            </div>
            {deleteMsg && <p className="form-message" role="alert">{deleteMsg}</p>}
          </form>
        )}
      </section>
    </>
  );
}
