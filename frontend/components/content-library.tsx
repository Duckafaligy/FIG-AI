"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { apiClient, apiSend, fmt, type ApiProject } from "@/lib/api";
import { BookOpen, Plus, RefreshCw, Search, X, LayoutGrid, List, FileText, ArrowRight, Monitor, Smartphone } from "lucide-react";
import { ArticlePreview } from "./library-article-preview";
import { useDashboardSearch } from "./dashboard-shell";

type Post = {
  id: string; title: string; body: string | null; brief: string | null;
  category: string; keyword: string | null; state: string; word_count: number;
  seo_score: number | null; scheduled_for: string | null;
  project: { id: string; hostname: string } | null;
  next_action: { to: string; label: string } | null;
};
type Library = { items: Post[]; projects: ApiProject[]; total: number; limit: number; offset: number };
const label = (value: string) => value.replaceAll("_", " ");

export function ContentLibrary() {
  const globalSearch = useDashboardSearch();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { id: pathProjectId } = useParams<{ id: string }>();
  // This library is cross-project by default (the "All projects" filter
  // below) -- the ?project= query param is that filter, deliberately
  // independent of which project's sidebar you reached this page from
  // (the [id] path segment, used only to rebuild this page's own base URL).
  const project = searchParams.get("project") ?? "";
  const [data, setData] = useState<Library | null>(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<Post | null>(null);
  const [creating, setCreating] = useState(false);
  const [view, setView] = useState<"grid" | "list">("list");
  const request = useRef(0);
  useEffect(() => { setOffset(0); }, [globalSearch, project]);
  const setProject = (value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set("project", value); else params.delete("project");
    router.replace(`/projects/${encodeURIComponent(pathProjectId)}/library${params.size ? `?${params}` : ""}`, { scroll: false });
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
    <header className="dashboard-heading-row"><div><span className="dashboard-eyebrow">Workspace / Content</span><h1>Content library</h1><p>A home for your ideas, drafts, and published stories.</p></div><button type="button" className="button" disabled={!data?.projects.length} onClick={() => setCreating(true)}><Plus size={16} />New article</button></header>
    <div className="cms-collection-heading"><span className="cms-collection-icon"><BookOpen size={22} /></span><div><h2>Articles</h2><p>Organize your content. Refine every detail before it goes live.</p></div><span className="cms-collection-label">Content collection</span></div>
    <nav className="cms-status-tabs" aria-label="Content status">{[["", "All content"], ["queued", "Queued"], ["in_progress", "Drafts"], ["review", "In review"], ["scheduled", "Scheduled"], ["published", "Published"]].map(([value, name]) => <button type="button" key={value} aria-pressed={status === value} onClick={() => { setStatus(value); setOffset(0); }}>{name}</button>)}</nav>
    <div className="library-toolbar">
      <label><Search size={16} /><input aria-label="Search library" placeholder="Search titles…" value={query} onChange={e => { setQuery(e.target.value); setOffset(0); }} /></label>
      <select aria-label="Filter library by project" value={project} onChange={e => { setProject(e.target.value); setOffset(0); }}><option value="">All projects</option>{data?.projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select>
      <div className="cms-view-controls" aria-label="Library layout"><button type="button" aria-label="List view" aria-pressed={view === "list"} onClick={() => setView("list")}><List size={18} /></button><button type="button" aria-label="Grid view" aria-pressed={view === "grid"} onClick={() => setView("grid")}><LayoutGrid size={18} /></button></div>
      <button className="secondary-button" type="button" onClick={load} disabled={loading}><RefreshCw size={15} />Refresh</button>
    </div>
    {error && <div className="form-message" role="alert">{error} <Link href="/signin">Sign in</Link></div>}
    {loading ? <p role="status">Loading your library…</p> : data && <>
      <p className="library-count">{data.total} content {data.total === 1 ? "item" : "items"}</p>
      {data.items.length ? <div className={`library-grid ${view === "list" ? "cms-list" : ""}`}>{data.items.map(post => <button key={post.id} type="button" className="library-card" onClick={() => setSelected(post)}>
        <span className="library-card-top"><BookOpen size={20} /><span>{label(post.state)}</span></span><h2>{post.title}</h2><p>{post.brief || post.body?.slice(0, 160) || "No draft yet. Open this item to begin writing."}</p>
        <small>{post.project?.hostname}</small><div className="library-card-bottom"><span>{post.word_count ?? 0} words</span><span>SEO {fmt(post.seo_score)}</span></div>
      </button>)}</div> : <section className="library-empty"><div className="cms-empty-art" aria-hidden="true"><FileText size={30} /><i /><i /><i /></div><span className="dashboard-eyebrow">Room for your next idea</span><h2>{query || globalSearch || status ? "No articles match these filters" : "Your next great article starts here"}</h2><p>{query || globalSearch || status ? "Try another title or switch to a different content status." : "Your library is empty. When articles are saved to this workspace, they’ll appear here—ready to edit, review, and prepare for publication."}</p>{data.projects.length ? <button type="button" className="button" onClick={() => setCreating(true)}><Plus size={16} />Create an article</button> : <Link className="button" href="/projects">Connect your first project<ArrowRight size={16} /></Link>}<small>No sample posts. Only your workspace’s content.</small></section>}
      {data.total > 30 && <nav className="library-pagination" aria-label="Library pages"><button type="button" className="secondary-button" disabled={!offset} onClick={() => setOffset(Math.max(0, offset - 30))}>Previous</button><span>Page {Math.floor(offset / 30) + 1} of {Math.max(1, Math.ceil(data.total / 30))}</span><button type="button" className="secondary-button" disabled={offset + 30 >= data.total} onClick={() => setOffset(offset + 30)}>Next</button></nav>}
      <div className="cms-workflow-note"><FileText size={18} /><p><strong>Built for your editorial workflow</strong><span>Draft → Review → Schedule. Your content stays in your workspace as it moves through each stage.</span></p></div>
    </>}
    {(creating || selected) && <ContentEditor initial={selected} defaultProject={project} projects={data?.projects ?? []} onClose={() => { setCreating(false); setSelected(null); }} onSaved={() => { void load(); }} />}
  </div>;
}

function ContentEditor({ initial, defaultProject, projects, onClose, onSaved }: { initial: Post | null; defaultProject: string; projects: ApiProject[]; onClose: () => void; onSaved: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [post, setPost] = useState(initial);
  const [title, setTitle] = useState(initial?.title ?? "");
  const [body, setBody] = useState(initial?.body ?? "");
  const [keyword, setKeyword] = useState(initial?.keyword ?? "");
  const [project, setProject] = useState(initial?.project?.id ?? (projects.some(p => p.id === defaultProject) ? defaultProject : projects[0]?.id) ?? "");
  const [editorView, setEditorView] = useState<"edit" | "preview">("edit");
  const [mobile, setMobile] = useState(false);
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
    <div className="cms-editor-toolbar"><div className="cms-view-controls"><button type="button" aria-pressed={editorView === "edit"} onClick={() => setEditorView("edit")}>Write</button><button type="button" aria-pressed={editorView === "preview"} onClick={() => setEditorView("preview")}>Article layout</button></div>{editorView === "preview" && <div className="cms-view-controls"><button type="button" aria-label="Desktop article layout" aria-pressed={!mobile} onClick={() => setMobile(false)}><Monitor size={17} /></button><button type="button" aria-label="Mobile article layout" aria-pressed={mobile} onClick={() => setMobile(true)}><Smartphone size={17} /></button></div>}</div>
    <form onSubmit={save}><div className="library-editor-fields" hidden={editorView !== "edit"}>
      {!post && <label>Project<select value={project} required onChange={e => setProject(e.target.value)}>{projects.map(p => <option value={p.id} key={p.id}>{p.name}</option>)}</select></label>}
      <label>Title<input value={title} required maxLength={300} onChange={e => setTitle(e.target.value)} /></label>
      <label>Target keyword<input value={keyword} maxLength={200} onChange={e => setKeyword(e.target.value)} /></label>
      {!post && <label>Format<select value={category} onChange={e => setCategory(e.target.value)}>{["blog", "guide", "faq", "glossary", "case"].map(c => <option key={c} value={c}>{label(c)}</option>)}</select></label>}
      {post?.brief && <p>{post.brief}</p>}
      <label className="library-body-field">Draft<textarea value={body} rows={15} onChange={e => setBody(e.target.value)} placeholder="Write or paste your draft. Markdown headings and links are supported by the scorer." /></label>
    </div>{editorView === "preview" && <ArticlePreview title={title} body={body} category={category} hostname={projects.find(p => p.id === project)?.hostname ?? post?.project?.hostname ?? "Your website"} mobile={mobile} />}<footer><span>{post ? label(post.state) + " · SEO " + fmt(post.seo_score) : "New draft"}{dirty ? " · Unsaved changes" : ""}</span><button className="button" type="submit" disabled={busy || !title.trim()}>{busy ? "Working…" : "Save draft"}</button></footer></form>
    {post && <div className="library-editor-actions">{post.next_action && post.next_action.to !== "published" && <button type="button" className="secondary-button" disabled={busy || dirty} onClick={() => move(post.next_action!.to)}>{post.next_action.label === "Schedule" ? "Schedule in 2 days" : post.next_action.label}</button>}{["review", "scheduled"].includes(post.state) && <button className="secondary-button" type="button" disabled={busy || dirty} onClick={() => move(post.state === "review" ? "in_progress" : "review")}>Return to {post.state === "review" ? "draft" : "review"}</button>}<p>AI drafting and publishing new posts are not supported by this backend yet. Saving and review transitions are stored in your account.</p></div>}
    {message && <p className="form-message" role="status">{message}</p>}
  </dialog>;
}
