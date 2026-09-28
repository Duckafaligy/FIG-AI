"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Activity, ArrowRight, BarChart3, Bell, CalendarDays, Check, ChevronDown, Clock3, ExternalLink, Globe2, LayoutGrid, List, Plus, Search, Settings2, ShieldCheck, Sparkles, X } from "lucide-react";
import { ServiceUnavailable } from "@/components/service-unavailable";
import { ProjectActions } from "@/components/project-actions";
import { ProjectConnectors } from "@/components/project-connectors";
import { api, apiClient, fmt, type ApiProjectsPage } from "@/lib/api";
import styles from "./projects-overview.module.css";

type ScheduledItem = { id: string; title: string; category: string; scheduled_for: string | null };

function projectUrl(hostname: string, suffix = "") { return `/projects/${encodeURIComponent(hostname)}${suffix}`; }
function initials(name: string) { return name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("") || "F"; }
function scheduledDate(value: string) { return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }).format(new Date(value)); }

export default function ProjectsPage() {
  const router = useRouter();
  const dialog = useRef<HTMLDialogElement>(null);
  const [live, setLive] = useState<ApiProjectsPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [query, setQuery] = useState("");
  const [view, setView] = useState<"grid" | "list">("grid");
  const [sort, setSort] = useState<"default" | "name">("default");
  const [scheduled, setScheduled] = useState<ScheduledItem[]>([]);
  const [scheduleError, setScheduleError] = useState(false);

  const loadProjects = () => {
    api.projects().then((result) => {
      setLoading(false);
      if (result.ok) { setLive(result.data); setLoadError(""); }
      else if (result.status === 402) window.location.replace("/choose-plan");
      else setLoadError("Unable to load projects. Please sign in or retry.");
    });
  };
  useEffect(loadProjects, []);
  useEffect(() => {
    let cancelled = false;
    apiClient<{ items: ScheduledItem[] }>("/api/content?state=scheduled&limit=100").then((result) => {
      if (cancelled) return;
      if (result.ok) setScheduled(result.data.items.filter((item) => item.scheduled_for));
      else setScheduleError(true);
    });
    return () => { cancelled = true; };
  }, []);

  const visibleCards = useMemo(() => {
    const cards = (live?.cards ?? []).filter((card) => `${card.name} ${card.hostname} ${card.tagline}`.toLowerCase().includes(query.trim().toLowerCase()));
    return sort === "name" ? [...cards].sort((a, b) => a.name.localeCompare(b.name)) : cards;
  }, [live, query, sort]);
  const upcoming = useMemo(() => scheduled
    .filter((item) => item.scheduled_for && new Date(item.scheduled_for).getTime() >= Date.now())
    .sort((a, b) => new Date(a.scheduled_for!).getTime() - new Date(b.scheduled_for!).getTime())
    .slice(0, 4), [scheduled]);

  if (loading) return <div className={styles.loading} role="status">Loading your workspace…</div>;
  if (!live) return <ServiceUnavailable message={loadError} />;

  const firstSite = live.cards[0]?.hostname;
  const siteHref = (suffix = "") => firstSite ? projectUrl(firstSite, suffix) : "/projects";
  const nextOpportunity = live.opportunities[0];
  const handleProjectCreated = (project: { id: string; hostname: string }) => {
    dialog.current?.close(); loadProjects(); router.push(projectUrl(project.hostname));
  };

  return <main className={styles.page}>
    <header className={styles.topbar}>
      <Link className={styles.wordmark} href="/" aria-label="FIG home">FIG<span>.</span></Link>
      <span className={styles.topDivider} aria-hidden="true" />
      <span className={styles.topLocation}>Workspace <span>/</span> All projects</span>
      <div className={styles.topActions}>
        <span className={styles.workspaceName}><span>{live.initials || initials(live.account.name)}</span>{live.account.name}</span>
        <Link href={siteHref("/notifications")} className={styles.iconLink} aria-label="Notifications"><Bell size={18} />{live.alerts > 0 && <i />}</Link>
        <Link href="/projects/settings" className={styles.accountLink} aria-label="Account settings">{initials(live.account.name)}</Link>
      </div>
    </header>

    <div className={styles.shell}>
      <aside className={styles.sidebar} aria-label="Workspace navigation">
        <div className={styles.sidebarLabel}>WORKSPACE</div>
        <a className={`${styles.sideLink} ${styles.sideLinkActive}`} href="#overview"><LayoutGrid size={18} />Overview</a>
        <a className={styles.sideLink} href="#sites"><Globe2 size={18} />Websites<span>{live.cards.length}</span></a>
        <a className={styles.sideLink} href="#attention"><Sparkles size={18} />Next steps</a>
        <a className={styles.sideLink} href="#schedule"><CalendarDays size={18} />Schedule</a>
        <Link className={styles.sideLink} href="/projects/settings"><Settings2 size={18} />Settings</Link>
        <div className={styles.sidebarBottom}><span className={styles.sidebarStatus}><i />{live.demo ? "Sample workspace" : "Your workspace"}</span><p>Review a finding, make a change, and scan again.</p></div>
      </aside>

      <div className={styles.content} id="overview">
        <div className={styles.hero}>
          <div className={styles.heroCopy}><span className={styles.eyebrow}><span />FIG WORKSPACE</span><h1>Every site.<br /><em>A clearer next move.</em></h1><p>See what your latest audits found, then choose what to improve next.</p>
            <div className={styles.heroActions}><button type="button" className={styles.primaryButton} onClick={() => dialog.current?.showModal()}><Plus size={17} />Add a website</button>{firstSite && <Link className={styles.textAction} href={siteHref()}>Open latest project <ArrowRight size={16} /></Link>}</div>
          </div>
          <div className={styles.heroAside}><span>WORKSPACE SNAPSHOT</span><strong>{live.kpis.projects.toString().padStart(2, "0")}</strong><p>website{live.kpis.projects === 1 ? "" : "s"} in view</p><div><ShieldCheck size={16} />{live.kpis.synced} with an audit</div></div>
        </div>

        {live.demo && <div className={styles.demoNotice}><span>i</span> This is a seeded demo workspace. Its sample activity and figures are for exploring the interface.</div>}

        <section className={styles.metrics} aria-label="Workspace summary">
          <div className={styles.metric}><span>PROJECTS</span><strong>{live.kpis.projects}</strong><small>Websites in this workspace</small></div>
          <div className={styles.metric}><span>AUDITED</span><strong>{live.kpis.synced}</strong><small>Sites with a latest scan</small></div>
          <div className={styles.metric}><span>AVERAGE SITE SCORE</span><strong>{fmt(live.kpis.impact)}</strong><small>From completed audits</small></div>
          <div className={styles.metric}><span>PUBLISHED</span><strong>{live.kpis.published}</strong><small>Saved published pieces</small></div>
        </section>

        <section className={styles.sitesSection} id="sites">
          <div className={styles.sectionHeader}><div><span className={styles.sectionIndex}>01 / YOUR WEBSITES</span><h2>Projects you can act on.</h2><p>Open a site to inspect findings, content, and its history.</p></div>
            <div className={styles.siteControls}><label className={styles.search}><Search size={17} /><input aria-label="Search projects" placeholder="Search websites" value={query} onChange={(event) => setQuery(event.target.value)} /></label><div className={styles.viewToggle} aria-label="Project view"><button type="button" aria-label="Grid view" aria-pressed={view === "grid"} onClick={() => setView("grid")}><LayoutGrid size={17} /></button><button type="button" aria-label="List view" aria-pressed={view === "list"} onClick={() => setView("list")}><List size={18} /></button></div><label className={styles.sort}><span className={styles.srOnly}>Sort projects</span><select value={sort} onChange={(event) => setSort(event.target.value as "default" | "name")}><option value="default">Default</option><option value="name">A–Z</option></select><ChevronDown size={14} /></label></div>
          </div>
          <div className={`${styles.siteGrid} ${view === "list" ? styles.siteGridList : ""}`}>
            {visibleCards.map((card) => <article className={styles.siteCard} key={card.id}>
              <div className={styles.cardTop}><span className={styles.siteMark}>{card.initial || card.name[0]}</span><span className={styles.siteState} data-state={card.state.toLowerCase()}><i />{card.state}</span><ProjectActions id={card.id} name={card.name} onChange={loadProjects} /></div>
              <div className={styles.cardIdentity}><Link href={projectUrl(card.hostname)}><h3>{card.name}<ArrowRight size={18} /></h3></Link><span>{card.hostname}</span>{card.tagline && <p>{card.tagline}</p>}</div>
              <div className={styles.cardMetrics}><div><span>LATEST SITE SCORE</span><strong>{fmt(card.impact)}</strong></div><div><span>PUBLISHED</span><strong>{card.published}</strong></div></div>
              <Link className={styles.cardFooter} href={projectUrl(card.hostname)}>View project <ArrowRight size={16} /></Link>
            </article>)}
            {visibleCards.length === 0 && <div className={styles.noResults}><Search size={22} /><strong>{query ? "No matching websites" : "No websites yet"}</strong><p>{query ? "Try another name or domain." : "Connect your first site to start seeing audit results here."}</p>{query ? <button type="button" onClick={() => setQuery("")}>Clear search</button> : <button type="button" onClick={() => dialog.current?.showModal()}>Add a website</button>}</div>}
            {!query && <button className={styles.addCard} type="button" onClick={() => dialog.current?.showModal()}><span><Plus size={25} /></span><strong>Add another website</strong><small>Connect a platform and start its first audit.</small></button>}
          </div>
        </section>

        <div className={styles.lowerGrid} id="attention">
          <section className={styles.insightPanel}><div className={styles.panelTop}><span className={styles.sectionIndex}>02 / THE SIGNAL</span>{firstSite && <a href="#sites">Explore websites <ArrowRight size={15} /></a>}</div><h2>What needs attention.</h2>
            {nextOpportunity ? <div className={styles.featuredFinding}><span className={styles.findingPriority}>{nextOpportunity.level} PRIORITY</span><h3>{nextOpportunity.title}</h3><p>{nextOpportunity.sub}</p><a href="#sites">Choose a website <ArrowRight size={16} /></a></div> : <div className={styles.emptyInsight}><Check size={23} /><strong>Nothing to review yet</strong><p>Run an audit on a website and its next steps will appear here.</p></div>}
            <div className={styles.scoreRow}><div><Search size={18} /><span>Search basics</span><strong>{fmt(live.seo_health.value)}</strong></div><div><Sparkles size={18} /><span>Answer readiness</span><strong>{fmt(live.geo_health.value)}</strong></div></div>
          </section>
          <section className={styles.activityPanel}><div className={styles.panelTop}><span className={styles.sectionIndex}>03 / ACTIVITY</span>{firstSite && <Link href={siteHref("/history")}>Full history <ArrowRight size={15} /></Link>}</div><h2>What changed recently.</h2>
            {live.activity.length ? <div className={styles.activityList}>{live.activity.slice(0, 4).map((item, index) => <div className={styles.activityItem} key={`${item.title}-${index}`}><span className={styles.activityIcon}><Activity size={17} /></span><div><strong>{item.title}</strong><small>{item.sub}</small></div><time>{item.ago}</time></div>)}</div> : <div className={styles.emptyInsight}><Clock3 size={23} /><strong>Your history starts here</strong><p>Audit a website to begin building a record of changes.</p></div>}
          </section>
        </div>

        <section className={styles.schedulePanel} id="schedule"><div className={styles.scheduleIntro}><span className={styles.sectionIndex}>04 / CONTENT RHYTHM</span><h2>Keep the next piece in view.</h2><p>Scheduled content from your workspace, shown in your timezone.</p>{firstSite && <Link href={siteHref("/library")}>Open content library <ExternalLink size={15} /></Link>}</div>
          <div className={styles.scheduleList}>{upcoming.length ? upcoming.map((item) => <div className={styles.scheduleItem} key={item.id}><span><CalendarDays size={17} /></span><div><strong>{item.title}</strong><small>{item.category}</small></div><time>{scheduledDate(item.scheduled_for!)}</time></div>) : <div className={styles.scheduleEmpty}><CalendarDays size={23} /><strong>{scheduleError ? "Schedule unavailable" : "Nothing scheduled yet"}</strong><p>{scheduleError ? "Open the library to retry loading your content." : "Plan a piece in the content library and it will appear here."}</p></div>}</div>
        </section>
        <footer className={styles.footer}><span>FIG <i /> A clearer internet.</span><Link href="/">Back to website <ArrowRight size={14} /></Link></footer>
      </div>
    </div>

    <dialog ref={dialog} className="preview-info-dialog" aria-labelledby="project-dialog-title"><div><h2 id="project-dialog-title">Add a website</h2><button type="button" aria-label="Close" onClick={() => dialog.current?.close()}><X size={18} /></button></div><div className={styles.dialogBody}><p>Connect the platform this site runs on. FIG creates the project and queues its first audit.</p><ProjectConnectors apis={[]} compact onCreated={handleProjectCreated} /><p className="project-connectors-compact-note"><BarChart3 size={13} />Google Analytics and Search Console connect across your workspace from <Link href="/projects/settings">account settings</Link>.</p></div></dialog>
  </main>;
}
