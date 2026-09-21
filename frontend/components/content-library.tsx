"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { apiClient, apiSend, fmt, type ApiProject } from "@/lib/api";
import { BookOpen, Plus, RefreshCw, Search, X } from "lucide-react";
import { useDashboardSearch } from "./dashboard-shell";

type Post = {
  id: string; title: string; body: string | null; brief: string | null;
  category: string; keyword: string | null; state: string; word_count: number;
  seo_score: number | null; scheduled_for: string | null;
  project: { id: string; hostname: string } | null;
  next_action: { to: string; label: string } | null;
};
type Library = { items: Post[]; projects: ApiProject[]; total: number; limit: number; offset: number };
const states = ["queued", "in_progress", "review", "scheduled", "published"];
const label = (value: string) => value.replaceAll("_", " ");

export function ContentLibrary() {
  const globalSearch = useDashboardSearch();
  const router = useRouter();
  const searchParams = useSearchParams();
  const project = searchParams.get("project") ?? "";
  const [data, setData] = useState<Library | null>(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<Post | null>(null);
  const [creating, setCreating] = useState(false);
  const request = useRef(0);
  useEffect(() => { setOffset(0); }, [globalSearch, project]);
  const setProject = (value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set("project", value); else params.delete("project");
    router.replace(`/app/library${params.size ? `?${params}` : ""}`, { scroll: false });
  };
  const load = useCallback(async () => {
    const id = ++request.current;
    setLoading(true);
    const params = new URLSearchParams({ q: query || globalSearch, project, state: status, offset: String(offset) });
    const result = await apiClient<Library>("/api/content?" + params);
    if (id !== request.current) return;
    setLoading(false);
    if (!result.ok) { setData(null); setError(result.status === 401 ? "Your session expired. Please sign in again." : result.error); return; }
    setData(result.data); setError("");
  }, [query, globalSearch, project, status, offset]);
  useEffect(() => { const timer = window.setTimeout(load, 200); return () => { clearTimeout(timer); request.current++; }; }, [load]);
  return <div className="content-library">
    <header className="dashboard-heading-row"><div><span className="dashboard-eyebrow">Content</span><h1>Your library</h1><p>Write, score, and review content across your projects.</p></div><button type="button" className="button" disabled={!data?.projects.length} onClick={() => setCreating(true)}><Plus size={16} />New content</button></header>
    <div className="library-toolbar">
      <label><Search size={16} /><input aria-label="Search library" placeholder="Search titles…" value={query} onChange={e => { setQuery(e.target.value); setOffset(0); }} /></label>
      <select aria-label="Filter library by project" value={project} onChange={e => { setProject(e.target.value); setOffset(0); }}><option value="">All projects</option>{data?.projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select>
      <select aria-label="Filter library by status" value={status} onChange={e => { setStatus(e.target.value); setOffset(0); }}><option value="">All statuses</option>{states.map(s => <option key={s} value={s}>{label(s)}</option>)}</select>
      <button className="secondary-button" type="button" onClick={load} disabled={loading}><RefreshCw size={15} />Refresh</button>
    </div>
    {error && <div className="form-message" role="alert">{error} <Link href="/signin">Sign in</Link></div>}
    {loading ? <p role="status">Loading your library…</p> : data && <>
      <p className="library-count">{data.total} content {data.total === 1 ? "item" : "items"}</p>
      {data.items.length ? <div className="library-grid">{data.items.map(post => <button key={post.id} type="button" className="library-card" onClick={() => setSelected(post)}>
        <span className="library-card-top"><BookOpen size={20} /><span>{label(post.state)}</span></span><h2>{post.title}</h2><p>{post.brief || post.body?.slice(0, 160) || "No draft yet. Open this item to begin writing."}</p>
        <small>{post.project?.hostname}</small><div className="library-card-bottom"><span>{post.word_count ?? 0} words</span><span>SEO {fmt(post.seo_score)}</span></div>
      </button>)}</div> : <section className="library-empty"><BookOpen size={32} /><h2>{query || status || project ? "No matching content" : "Your library starts here"}</h2><p>{data.projects.length ? "Create a draft, then move it through review." : "Add a project before creating your first content item."}</p>{!data.projects.length && <Link className="button" href="/projects">Add a project</Link>}</section>}
      <nav className="library-pagination" aria-label="Library pages"><button type="button" className="secondary-button" disabled={!offset} onClick={() => setOffset(Math.max(0, offset - 30))}>Previous</button><span>Page {Math.floor(offset / 30) + 1} of {Math.max(1, Math.ceil(data.total / 30))}</span><button type="button" className="secondary-button" disabled={offset + 30 >= data.total} onClick={() => setOffset(offset + 30)}>Next</button></nav>
    </>}
    {(creating || selected) && <ContentEditor initial={selected} projects={data?.projects ?? []} onClose={() => { setCreating(false); setSelected(null); }} onSaved={() => { void load(); }} />}
  </div>;
}

function ContentEditor({ initial, projects, onClose, onSaved }: { initial: Post | null; projects: ApiProject[]; onClose: () => void; onSaved: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [post, setPost] = useState(initial);
  const [title, setTitle] = useState(initial?.title ?? "");
  const [body, setBody] = useState(initial?.body ?? "");
  const [keyword, setKeyword] = useState(initial?.keyword ?? "");
  const [project, setProject] = useState(initial?.project?.id ?? projects[0]?.id ?? "");
  const [category, setCategory] = useState(initial?.category ?? "blog");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const dirty = title !== (post?.title ?? "") || body !== (post?.body ?? "") || keyword !== (post?.keyword ?? "");
  const close = () => { if (!busy && (!dirty || window.confirm("Discard your unsaved changes?"))) onClose(); };
  useEffect(() => { const el = dialog.current; el?.showModal(); return () => el?.close(); }, []);
  const save = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setMessage("");
    const result = post
      ? await apiSend<Post>("/api/content/" + encodeURIComponent(post.id), "PATCH", { title, body, keyword })
      : await apiSend<Post>("/api/content", "POST", { title, body, keyword, category, project_id: project });
    setBusy(false);
    if (!result.ok) { setMessage(result.error); return; }
    setPost(result.data); setTitle(result.data.title); setBody(result.data.body ?? ""); setKeyword(result.data.keyword ?? "");
    setMessage("Saved to your workspace."); onSaved();
  };
  const move = async (to: string) => {
    if (!post || dirty) return;
    setBusy(true); setMessage("");
    const result = await apiSend<Post>("/api/content/" + encodeURIComponent(post.id) + "/move", "POST", { to });
    setBusy(false);
    if (!result.ok) { setMessage(result.error); return; }
    setPost(result.data); setMessage("Moved to " + label(result.data.state) + "."); onSaved();
  };
  return <dialog ref={dialog} className="library-editor" aria-labelledby="content-editor-title" onCancel={e => { e.preventDefault(); close(); }} onClick={e => { if (e.target === dialog.current) close(); }}>
    <header><div><span>Content library</span><h2 id="content-editor-title">{post ? "Edit content" : "New content"}</h2></div><button className="secondary-button" aria-label="Close editor" type="button" disabled={busy} onClick={close}><X size={18} /></button></header>
    <form onSubmit={save}><div className="library-editor-fields">
      {!post && <label>Project<select value={project} required onChange={e => setProject(e.target.value)}>{projects.map(p => <option value={p.id} key={p.id}>{p.name}</option>)}</select></label>}
      <label>Title<input value={title} required maxLength={300} onChange={e => setTitle(e.target.value)} /></label>
      <label>Target keyword<input value={keyword} maxLength={200} onChange={e => setKeyword(e.target.value)} /></label>
      {!post && <label>Format<select value={category} onChange={e => setCategory(e.target.value)}>{["blog", "guide", "faq", "glossary", "case"].map(c => <option key={c} value={c}>{label(c)}</option>)}</select></label>}
      {post?.brief && <p>{post.brief}</p>}
      <label className="library-body-field">Draft<textarea value={body} rows={15} onChange={e => setBody(e.target.value)} placeholder="Write or paste your draft. Markdown headings and links are supported by the scorer." /></label>
    </div><footer><span>{post ? label(post.state) + " · SEO " + fmt(post.seo_score) : "New draft"}{dirty ? " · Unsaved changes" : ""}</span><button className="button" type="submit" disabled={busy}>{busy ? "Working…" : "Save draft"}</button></footer></form>
    {post && <div className="library-editor-actions">{post.next_action && post.next_action.to !== "published" && <button type="button" className="secondary-button" disabled={busy || dirty} onClick={() => move(post.next_action!.to)}>{post.next_action.label === "Schedule" ? "Schedule in 2 days" : post.next_action.label}</button>}{["review", "scheduled"].includes(post.state) && <button className="secondary-button" type="button" disabled={busy || dirty} onClick={() => move(post.state === "review" ? "in_progress" : "review")}>Return to {post.state === "review" ? "draft" : "review"}</button>}<p>AI drafting and publishing new posts are not supported by this backend yet. Saving and review transitions are stored in your account.</p></div>}
    {message && <p className="form-message" role="status">{message}</p>}
  </dialog>;
}
