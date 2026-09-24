"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiClient, apiSend } from "@/lib/api";
import styles from "./analytics-property-picker.module.css";

type Properties = { selected: string | null; properties: { id: string; name: string; account: string }[] };

export function AnalyticsPropertyPicker({ projectId }: { projectId: string }) {
  const [data, setData] = useState<Properties | null>(null);
  const [selected, setSelected] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [reload, setReload] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true); setData(null); setError(""); setMessage("");
    apiClient<Properties>(`/api/projects/${encodeURIComponent(projectId)}/analytics-properties`).then(result => {
      if (!active) return;
      if (result.ok) { setData(result.data); setSelected(result.data.selected ?? ""); }
      else setError(result.error);
      setLoading(false);
    });
    return () => { active = false; };
  }, [projectId, reload]);
  const save = async () => {
    if (saving) return;
    setSaving(true); setError(""); setMessage("");
    const result = await apiSend<{ selected: string | null }>(`/api/projects/${encodeURIComponent(projectId)}/analytics-property`, "PATCH", { property: selected || null });
    if (result.ok) {
      setData(current => current && { ...current, selected: result.data.selected });
      setMessage(result.data.selected ? "Reporting property saved for this project." : "Selection cleared. Analytics will show unavailable until a property is selected.");
    } else setError(result.error);
    setSaving(false);
  };
  const missing = data?.selected && !data.properties.some(property => property.id === data.selected);
  return <section className={`settings-surface ${styles.panel}`} aria-labelledby="analytics-property-title">
    <div><h3 id="analytics-property-title">Analytics reporting source</h3><p>Choose the GA4 property for this website. Google authorization is shared across your workspace, but this selection only affects this project.</p></div>
    {loading ? <p role="status">Loading authorized properties…</p> : data && <>
      <label htmlFor="ga-property">Google Analytics property</label>
      <select id="ga-property" value={selected} onChange={event => { setSelected(event.target.value); setMessage(""); }} disabled={saving}>
        <option value="">No property selected</option>
        {missing && <option value={data.selected!} disabled>{data.selected} — access unavailable</option>}
        {data.properties.map(property => <option key={property.id} value={property.id}>{property.name} · {property.id}{property.account ? ` · ${property.account}` : ""}</option>)}
      </select>
      {!data.properties.length && <p>No GA4 properties were returned by Google. Check the connected account’s access.</p>}
      {missing && <p role="alert">The saved property is no longer in the authorized list. Select an available property or clear the selection.</p>}
      <button type="button" className="button button--small" disabled={saving || selected === (data.selected ?? "")} onClick={save}>{saving ? "Saving…" : "Save reporting source"}</button>
    </>}
    {error && <p role="alert">{error}</p>}
    {message && <p role="status">{message}</p>}
    <div className={styles.actions}><Link href="/projects/settings">Manage Google connection</Link><button type="button" className="settings-link-button" disabled={loading || saving} onClick={() => setReload(value => value + 1)}>Refresh properties</button></div>
    <p>Search Console uses a verified property matching this project’s domain. If none matches, its data stays unavailable.</p>
  </section>;
}
