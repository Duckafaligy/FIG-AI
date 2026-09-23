"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CheckCircle2, RotateCcw, Send, Wand2, XCircle } from "lucide-react";
import { actions, api, type ApiChangeRow, type ApiChangesPage } from "@/lib/api";

const STATE_LABEL: Record<string, string> = {
  proposed: "Proposed", approved: "Approved", published: "Published",
  failed: "Failed", rejected: "Rejected", reverted: "Reverted",
};
const STATE_TONE: Record<string, string> = {
  proposed: "blue", approved: "purple", published: "green",
  failed: "red", rejected: "grey", reverted: "grey",
};

function StateBadge({ state }: { state: string }) {
  return <b className={`pq-status pq-status--${STATE_TONE[state] ?? "grey"}`}>{STATE_LABEL[state] ?? state}</b>;
}

function pageLabel(row: ApiChangeRow): string {
  if (!row.page) return row.hostname;
  try {
    const u = new URL(row.page);
    return u.pathname === "/" ? u.hostname : `${u.hostname}${u.pathname}`;
  } catch {
    return row.page;
  }
}

function Row({ row, onAction, busy }: {
  row: ApiChangeRow; busy: boolean;
  onAction: (id: string, action: "approve" | "reject" | "publish" | "revert") => void;
}) {
  const act = (action: "approve" | "reject" | "publish" | "revert") => onAction(row.id, action);
  return (
    <article className="pq-row">
      <div className="pq-row-main">
        <span className="pq-kind">{row.kind}</span>
        <div>
          <strong>{row.title}</strong>
          <small>{pageLabel(row)}{row.client ? ` · ${row.client}` : ""}</small>
          {row.detail && <p className="pq-detail">{row.detail}</p>}
          {row.state === "failed" && row.error && <p className="pq-error">{row.error}</p>}
        </div>
      </div>
      <span className="pq-platform">{row.platform ?? "Not connected"}</span>
      <StateBadge state={row.state} />
      <div className="pq-actions">
        {row.state === "proposed" && <>
          <button type="button" className="button button--small" disabled={busy} onClick={() => act("approve")}>
            <CheckCircle2 size={14} />Approve
          </button>
          <button type="button" className="secondary-button" disabled={busy} onClick={() => act("reject")}>
            <XCircle size={14} />Reject
          </button>
        </>}
        {row.state === "approved" && <>
          <button type="button" className="button button--small" disabled={busy || !row.can_publish}
                  title={row.can_publish ? "" : "Connect a CMS for this site under Settings first"}
                  onClick={() => act("publish")}>
            <Send size={14} />Publish
          </button>
          <button type="button" className="secondary-button" disabled={busy} onClick={() => act("reject")}>
            <XCircle size={14} />Reject
          </button>
        </>}
        {row.state === "failed" && <>
          <button type="button" className="button button--small" disabled={busy} onClick={() => act("approve")}
                  title="Sends it back to Approved so Publish can be retried">
            <Wand2 size={14} />Retry
          </button>
          <button type="button" className="secondary-button" disabled={busy} onClick={() => act("reject")}>
            <XCircle size={14} />Reject
          </button>
        </>}
        {row.state === "published" && (
          <button type="button" className="secondary-button" disabled={busy} onClick={() => act("revert")}>
            <RotateCcw size={14} />Revert
          </button>
        )}
      </div>
    </article>
  );
}

export function PublishQueue({ projectId, embedded = false }: { projectId?: string; embedded?: boolean } = {}) {
  const [data, setData] = useState<ApiChangesPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [proposing, setProposing] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState("");
  const request = useRef(0);

  const load = useCallback(async () => {
    const id = ++request.current;
    const result = await api.changes(projectId ?? "");
    if (id !== request.current) return;
    setLoading(false);
    if (!result.ok) { setError(result.status === 401 ? "Your session expired. Please sign in again." : result.error); return; }
    setData(result.data); setError("");
  }, [projectId]);
  useEffect(() => { load(); }, [load]);

  const propose = async () => {
    setProposing(true);
    const result = await actions.proposeChanges(projectId ?? "");
    setProposing(false);
    if (result.ok) load();
  };

  const onAction = async (id: string, action: "approve" | "reject" | "publish" | "revert") => {
    setBusyId(id);
    setActionError("");
    const result = await actions.changeAction(id, action);
    setBusyId(null);
    if (!result.ok) { setActionError(result.error); return; }
    load();
  };

  if (loading) return <div className="pq-state">Loading the publish queue…</div>;
  if (error) return <div className="pq-state pq-state--error">{error}</div>;
  if (!data) return null;

  const rows = data.rows;
  const activeRows = rows.filter(r => !["rejected", "reverted"].includes(r.state));
  const doneRows = rows.filter(r => ["rejected", "reverted"].includes(r.state));

  return (
    <div className={embedded ? "publish-queue publish-queue--embedded" : "publish-queue"}>
      {embedded ? (
        <div className="pq-embedded-heading">
          <p>Mechanical fixes from this project's latest scan, reviewed here before anything touches the live site.</p>
          <button type="button" className="button button--small" disabled={proposing} onClick={propose}>
            <Wand2 size={14} />{proposing ? "Checking…" : "Propose changes"}
          </button>
        </div>
      ) : (
        <header className="dashboard-heading-row">
          <div>
            <span className="dashboard-eyebrow">Workspace / Publish</span>
            <h1>Publish queue</h1>
            <p>Mechanical fixes from your latest scans, reviewed here before anything touches a live site.</p>
          </div>
          <button type="button" className="button" disabled={proposing || data.sites === 0} onClick={propose}>
            <Wand2 size={16} />{proposing ? "Checking…" : "Propose changes"}
          </button>
        </header>
      )}

      {!embedded && data.sites === 0 && (
        <div className="pq-empty">
          <p>Add a project first, then come back here — proposed fixes are drawn from a site's most recent scan.</p>
        </div>
      )}

      {data.sites > 0 && data.connected === 0 && (
        <div className="pq-note">
          <p>No CMS is connected {embedded ? "for this project" : "on any of your sites"} yet. Proposed changes
            can still be reviewed and approved here, but Publish stays disabled until you connect one
            {embedded ? " below" : " under Settings → Integrations"}.</p>
        </div>
      )}

      {actionError && <div className="pq-note pq-note--error"><p>{actionError}</p></div>}

      {data.sites > 0 && rows.length === 0 && (
        <div className="pq-empty">
          <p>Nothing proposed yet. Click <strong>Propose changes</strong> to check {embedded ? "this project's" : "your sites'"} latest
            scan for fixes FIG can apply mechanically — titles, heading structure, and (where a platform supports it)
            meta descriptions.</p>
        </div>
      )}

      {activeRows.length > 0 && (
        <div className="pq-list">
          {activeRows.map(row => (
            <Row key={row.id} row={row} busy={busyId === row.id} onAction={onAction} />
          ))}
        </div>
      )}

      {doneRows.length > 0 && (
        <details className="pq-history">
          <summary>{doneRows.length} rejected or reverted</summary>
          <div className="pq-list">
            {doneRows.map(row => (
              <Row key={row.id} row={row} busy={busyId === row.id} onAction={onAction} />
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
