import {
  Activity,
  Bell,
  Bot,
  CalendarCheck2,
  ChartNoAxesCombined,
  CircleAlert,
  Clock3,
  Database,
  FileCheck2,
  Gauge,
  Globe2,
  History,
  Layers3,
  Link2,
  ListChecks,
  MailCheck,
  MessageCircleQuestion,
  Network,
  Search,
  Send,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Target,
  Trophy,
  Users,
  Workflow
} from "lucide-react";

type Icon = typeof Search;
export type DashboardTone = "green" | "blue" | "purple" | "amber" | "red";

export type DashboardRow = {
  title: string;
  meta: string;
  status: string;
  tone?: DashboardTone;
  rank?: number;
  kicker?: string;
  action?: string;
  category?: string;
  cells?: { value: string; kind?: "text" | "score" | "status"; tone?: DashboardTone }[];
};

export type DashboardStat = {
  label: string;
  value: string;
  change?: string;
  tone?: DashboardTone;
};

export type DashboardSection = {
  area?: string;
  title: string;
  description: string;
  icon: Icon;
  kind: "chart" | "table" | "feed" | "flow" | "summary" | "answer" | "funnel" | "health";
  variant?: "standard" | "ranked" | "library" | "audit" | "channels" | "compact";
  chart?: "trend" | "bars" | "donut" | "reliability";
  span?: "wide" | "two-thirds" | "third" | "half" | "quarter";
  meta?: string;
  legend?: string[];
  distribution?: number[];
  rows?: DashboardRow[];
  columns?: string[];
  steps?: { label: string; copy: string }[];
  stats?: DashboardStat[];
  tabs?: { label: string; count?: number; active?: boolean }[];
  score?: { value: string; label: string; tone?: DashboardTone };
};

export type DashboardPage = {
  layout: "overview" | "seo" | "geo" | "notifications" | "history";
  eyebrow: string;
  title: string;
  description: string;
  nav: string;
  action: string;
  metrics: {
    label: string;
    value: string;
    change: string;
    detail: string;
    icon: Icon;
    tone?: "green" | "blue" | "purple" | "amber";
    lowerIsBetter?: boolean;
  }[];
  sections: DashboardSection[];
};

const libraryRows: DashboardRow[] = [
  { title: "Learn AI in 5 Minutes a Day", meta: "May 25, 2025 · 4.2K visits", status: "92", tone: "green" },
  { title: "Investor-ready monthly update generator", meta: "May 24, 2025 · 2.8K visits", status: "88", tone: "green" },
  { title: "Ship a lead-magnet in 7 steps", meta: "May 22, 2025 · 1.9K visits", status: "84", tone: "blue" },
  { title: "Why long-context models change RAG strategy", meta: "May 21, 2025 · 1.4K visits", status: "82", tone: "blue" },
  { title: "Build a personal AI workflow in one afternoon", meta: "May 19, 2025 · 980 visits", status: "78", tone: "amber" }
];

const publishedLibraryRows: DashboardRow[] = libraryRows.map((row, index) => {
  const [published, traffic] = row.meta.split(" · ");
  return {
    ...row,
    status: "Published",
    category: index === 1 ? "Prompts" : "Guides",
    action: "Manage",
    cells: [
      { value: row.title },
      { value: "Published", kind: "status", tone: "green" },
      { value: published },
      { value: traffic.replace(" visits", "") },
      { value: row.status, kind: "score", tone: row.tone }
    ]
  };
});

export const dashboardPages: Record<string, DashboardPage> = {
  overview: {
    layout: "overview",
    eyebrow: "Overview",
    title: "Content Performance Overview",
    description: "Track blog performance, SEO, GEO, and content impact for Demo workspace.",
    nav: "Overview",
    action: "New content",
    metrics: [
      { label: "Total Published Blogs", value: "28", change: "+15.6%", detail: "from last month", icon: FileCheck2, tone: "purple" },
      { label: "Posts in Queue", value: "12", change: "+3", detail: "from last week", icon: Clock3, tone: "amber" },
      { label: "Organic Traffic", value: "4.2K", change: "+18.7%", detail: "from last month", icon: ChartNoAxesCombined, tone: "blue" },
      { label: "Avg. Impact Score", value: "84", change: "+6 points", detail: "from last month", icon: Sparkles, tone: "purple" },
      { label: "Sync Health", value: "Healthy", change: "Stable", detail: "all systems online", icon: Gauge, tone: "green" },
      { label: "AI Search Visibility", value: "62%", change: "+12%", detail: "from last month", icon: Globe2, tone: "blue" }
    ],
    sections: [
      {
        area: "overview-trends",
        title: "Performance Trends",
        description: "Traffic, impressions, and content impact over time.",
        icon: Sparkles,
        kind: "chart",
        chart: "trend",
        span: "two-thirds",
        meta: "Last 30 days",
        legend: ["Organic Traffic", "Impressions", "Impact Score"]
      },
      {
        area: "overview-analytics",
        title: "Google Analytics (Blog Content)",
        description: "Engagement, conversion, and returning-reader signals for blog content.",
        icon: ChartNoAxesCombined,
        kind: "summary",
        span: "third",
        meta: "Last 30 days",
        stats: [
          { label: "Avg. engagement time", value: "2m 14s", change: "+24%", tone: "green" },
          { label: "Bounce rate", value: "42%", change: "−8%", tone: "green" },
          { label: "Blog conversions", value: "312", change: "+28%", tone: "blue" },
          { label: "Returning readers", value: "18%", change: "+6%", tone: "purple" }
        ]
      },
      {
        area: "overview-search-presence",
        title: "Search Presence & AI Visibility",
        description: "Demo workspace visibility across traditional and answer engines.",
        icon: Target,
        kind: "summary",
        span: "third",
        meta: "Last 30 days",
        stats: [
          { label: "Google Search Visibility", value: "78%", change: "+12%", tone: "blue" },
          { label: "AI Search Mentions", value: "62%", change: "+18%", tone: "purple" },
          { label: "Total Ranking Keywords", value: "142", change: "+26%", tone: "green" },
          { label: "Branded Search Growth", value: "34%", change: "+9%", tone: "amber" }
        ]
      },
      {
        area: "overview-impact",
        title: "Highest Impact Blog Posts",
        description: "Best-performing Demo workspace learning content this reporting period.",
        icon: Trophy,
        kind: "table",
        variant: "ranked",
        span: "half",
        meta: "View all →",
        columns: ["Blog Post", "Traffic", "Impact Score"],
        rows: libraryRows.slice(0, 5).map((row, index) => ({ ...row, meta: row.meta.split(" · ")[1].replace(" visits", ""), rank: index + 1 }))
      },
      {
        area: "overview-funnel",
        title: "Content Publishing Funnel",
        description: "A snapshot of content moving from idea to published lesson.",
        icon: Layers3,
        kind: "funnel",
        span: "half",
        meta: "May 2025",
        stats: [
          { label: "Ideas Generated", value: "36", tone: "blue" },
          { label: "In Writing", value: "18", tone: "amber" },
          { label: "In Review", value: "8", tone: "purple" },
          { label: "Scheduled", value: "12", tone: "blue" },
          { label: "Published", value: "28", tone: "green" }
        ],
        score: { value: "102", label: "Total", tone: "purple" }
      },
      {
        area: "overview-activity",
        title: "Recent Activity",
        description: "The latest actions in this sample workspace.",
        icon: Activity,
        kind: "feed",
        span: "third",
        meta: "View all →",
        rows: [
          { title: "Blog post published", meta: "Learn AI in 5 Minutes a Day", status: "2h ago", tone: "green" },
          { title: "Blog post scheduled", meta: "A practical RAG explainer", status: "5h ago", tone: "blue" },
          { title: "Content optimized", meta: "How to write usable AI prompts", status: "1d ago", tone: "purple" },
          { title: "CMS sync completed", meta: "3 Demo workspace pages updated", status: "1d ago", tone: "green" }
        ]
      },
      {
        area: "overview-keywords",
        title: "Top Ranking Keywords",
        description: "Keyword movement for Demo workspace across tracked search terms.",
        icon: Search,
        kind: "table",
        variant: "ranked",
        span: "third",
        meta: "View all →",
        columns: ["Keyword", "Position", "Traffic"],
        rows: [
          { title: "learn ai daily", meta: "Position 1", status: "1.4K", tone: "green", rank: 1 },
          { title: "ai prompt examples", meta: "Position 3", status: "880", tone: "blue", rank: 2 },
          { title: "rag explained", meta: "Position 2", status: "720", tone: "purple", rank: 3 },
          { title: "ai workflow guide", meta: "Position 4", status: "580", tone: "amber", rank: 4 }
        ]
      },
      {
        area: "overview-opportunities",
        title: "Content Opportunities",
        description: "Topics with the clearest projected discovery upside.",
        icon: Sparkles,
        kind: "table",
        variant: "ranked",
        span: "third",
        meta: "View all →",
        columns: ["Topic", "Priority", "Est. Traffic"],
        rows: [
          { title: "AI agents for beginners", meta: "High priority", status: "1.2K", tone: "red", rank: 1 },
          { title: "Prompt engineering checklist", meta: "High priority", status: "980", tone: "red", rank: 2 },
          { title: "RAG without jargon", meta: "Medium priority", status: "860", tone: "amber", rank: 3 },
          { title: "AI content workflows", meta: "Medium priority", status: "720", tone: "amber", rank: 4 }
        ]
      },
      {
        area: "overview-library",
        title: "Published Blog Library",
        description: "Published Demo workspace content, ordered by the most recent update.",
        icon: Database,
        kind: "table",
        variant: "library",
        span: "two-thirds",
        meta: "Newest first",
        columns: ["Blog Post", "Status", "Published", "Traffic", "Impact Score", "Actions"],
        rows: publishedLibraryRows
      },
      {
        area: "overview-health",
        title: "Workspace Health",
        description: "Connection and workflow readiness for Demo workspace.",
        icon: ShieldCheck,
        kind: "health",
        span: "third",
        meta: "Systems overview",
        score: { value: "92", label: "Healthy", tone: "green" },
        rows: [
          { title: "Content generation", meta: "AI drafting is available", status: "Ready", tone: "green" },
          { title: "Search indexing", meta: "New posts queued for indexing", status: "Healthy", tone: "green" },
          { title: "Analytics integration", meta: "Connection verification is pending", status: "Setup", tone: "blue" }
        ]
      }
    ]
  },

  seo: {
    layout: "seo",
    eyebrow: "SEO",
    title: "SEO Content Queue",
    description: "Create, optimize, review, and publish search-ready content for Demo workspace.",
    nav: "SEO",
    action: "Create brief",
    metrics: [
      { label: "Posts in Queue", value: "12", change: "+3", detail: "from last week", icon: FileCheck2, tone: "purple" },
      { label: "Published This Month", value: "28", change: "+27%", detail: "from last month", icon: FileCheck2, tone: "green" },
      { label: "Avg. SEO Score", value: "78", change: "+6 points", detail: "from last month", icon: Target, tone: "amber" },
      { label: "Avg. Impact Score", value: "84", change: "+8 points", detail: "from last month", icon: Sparkles, tone: "purple" },
      { label: "Organic Click Growth", value: "+42%", change: "+42%", detail: "vs. previous month", icon: ChartNoAxesCombined, tone: "green" },
      { label: "Keywords in Top 10", value: "312", change: "+28%", detail: "from last month", icon: Search, tone: "blue" }
    ],
    sections: [
      {
        area: "seo-flow",
        title: "Content Creation Flow",
        description: "From idea to impact—how a Demo workspace SEO brief becomes published content.",
        icon: Workflow,
        kind: "flow",
        span: "two-thirds",
        meta: "How it works",
        steps: [
          { label: "Connected project", copy: "Demo workspace topics and library" },
          { label: "Keyword & topic intake", copy: "Find plain-English opportunities" },
          { label: "SEO template engine", copy: "Generate structured drafts" },
          { label: "Review & publish", copy: "Approve and ship content" }
        ]
      },
      {
        area: "seo-template",
        title: "Template Preview",
        description: "A compact preview of the selected blog structure.",
        icon: FileCheck2,
        kind: "feed",
        span: "third",
        meta: "View all templates",
        rows: [
          { title: "The Beginner's Guide to AI Agents", meta: "Blog template · ~2,500 words", status: "SEO", tone: "blue", kicker: "BLOG TEMPLATE" },
          { title: "Search intent covered", meta: "Definitions, examples, workflow, FAQs", status: "Ready", tone: "green" },
          { title: "Workspace voice", meta: "Plain English · Beginner friendly", status: "Applied", tone: "purple" }
        ]
      },
      {
        area: "seo-review",
        title: "Blog Posts for Review",
        description: "Editorial queue for the single Demo workspace project.",
        icon: ListChecks,
        kind: "table",
        variant: "library",
        span: "wide",
        meta: "Sort: Newest",
        tabs: [{ label: "All", active: true }, { label: "In Queue" }, { label: "In Review" }, { label: "Approved" }],
        columns: ["Title", "Topic", "Target Keywords", "SEO Score", "Impact Score", "Status", "Actions"],
        rows: [
          { title: "The Beginner's Guide to AI Agents", meta: "ai agents for beginners", category: "AI Guide", status: "In Queue", tone: "blue", action: "Review", cells: [{ value: "92", kind: "score", tone: "green" }, { value: "88", kind: "score", tone: "green" }] },
          { title: "How to Write Prompts That Give Usable Answers", meta: "how to write ai prompts", category: "Prompting", status: "In Queue", tone: "blue", action: "Review", cells: [{ value: "88", kind: "score", tone: "green" }, { value: "82", kind: "score", tone: "green" }] },
          { title: "A Practical RAG Explainer Without the Jargon", meta: "what is RAG AI", category: "AI Search", status: "In Review", tone: "amber", action: "Review", cells: [{ value: "84", kind: "score", tone: "green" }, { value: "80", kind: "score", tone: "green" }] },
          { title: "Build a Personal AI Workflow in One Afternoon", meta: "ai workflow examples", category: "Automation", status: "In Queue", tone: "blue", action: "Review", cells: [{ value: "80", kind: "score", tone: "green" }, { value: "78", kind: "score", tone: "amber" }] },
          { title: "The Best AI Tools for Small Teams", meta: "best ai tools", category: "AI Tools", status: "In Review", tone: "amber", action: "Review", cells: [{ value: "78", kind: "score", tone: "amber" }, { value: "70", kind: "score", tone: "amber" }] },
          { title: "A Practical Checklist for Better AI Results", meta: "ai quality checklist", category: "AI Guide", status: "Approved", tone: "green", action: "Review", cells: [{ value: "91", kind: "score", tone: "green" }, { value: "86", kind: "score", tone: "green" }] }
        ].map((row) => ({ ...row, tone: row.tone as DashboardTone, cells: [{ value: row.title }, { value: row.category }, { value: row.meta }, ...row.cells.map((cell) => ({ ...cell, kind: "score" as const, tone: cell.tone as DashboardTone })), { value: row.status, kind: "status" as const, tone: row.tone as DashboardTone }] }))
      },
      {
        area: "seo-impact",
        title: "Highest Impact Blog Posts",
        description: "Demo workspace content with the strongest search performance.",
        icon: Trophy,
        kind: "table",
        variant: "ranked",
        span: "third",
        meta: "View all →",
        columns: ["Blog Post", "Traffic", "Impact"],
        rows: libraryRows.slice(0, 5).map((row, index) => ({ ...row, meta: row.meta.split(" · ")[1].replace(" visits", ""), rank: index + 1 }))
      },
      {
        area: "seo-momentum",
        title: "Keyword Ranking Momentum",
        description: "Keyword movement across Demo workspace topic clusters.",
        icon: ChartNoAxesCombined,
        kind: "chart",
        chart: "bars",
        span: "third",
        meta: "Last 30 days",
        legend: ["Top 3", "Top 4–10", "Top 11–50"]
      },
      {
        area: "seo-opportunities",
        title: "Optimization Opportunities",
        description: "Priority improvements for current learning content.",
        icon: Sparkles,
        kind: "table",
        span: "third",
        meta: "View all →",
        columns: ["Keyword / Topic", "Opportunity", "Priority"],
        rows: [
          { title: "ai agents", meta: "Create comprehensive guide", status: "High", tone: "red" },
          { title: "prompt examples", meta: "Add copy-ready templates", status: "High", tone: "red" },
          { title: "rag explained", meta: "Expand supporting examples", status: "Medium", tone: "amber" },
          { title: "ai workflows", meta: "Add schema markup", status: "Medium", tone: "amber" }
        ]
      },
      {
        area: "seo-links",
        title: "Internal Linking Suggestions",
        description: "Connections between Demo workspace courses, topics, and practical guides.",
        icon: Link2,
        kind: "table",
        span: "third",
        meta: "View all →",
        columns: ["From Post", "Suggested Link", "Anchor Text"],
        rows: [
          { title: "Prompt Engineering Fundamentals", meta: "Copy-ready prompt library", status: "AI prompts", tone: "purple" },
          { title: "AI Agents & Blueprints", meta: "Personal AI workflow guide", status: "AI workflow", tone: "blue" },
          { title: "AI Search & RAG", meta: "Long-context models guide", status: "RAG", tone: "green" },
          { title: "AI for Business", meta: "Investor update generator", status: "AI tools", tone: "amber" }
        ]
      },
      {
        area: "seo-library",
        title: "Published SEO Library",
        description: "Published Demo workspace pages with traffic and SEO scores.",
        icon: Database,
        kind: "table",
        variant: "library",
        span: "two-thirds",
        meta: "Newest first",
        tabs: [{ label: "All categories", active: true }, { label: "Guides" }, { label: "Prompts" }],
        columns: ["Title", "Status", "Published", "Traffic", "SEO Score", "Actions"],
        rows: publishedLibraryRows
      },
      {
        area: "seo-clusters",
        title: "Keyword Cluster Coverage",
        description: "Coverage across this workspace's core AI learning categories.",
        icon: Network,
        kind: "chart",
        chart: "donut",
        span: "half",
        meta: "All clusters",
        legend: ["Prompting", "Agents", "RAG", "Automation"],
        score: { value: "312", label: "Keywords", tone: "purple" }
      },
      {
        area: "seo-health",
        title: "SEO Health Summary",
        description: "A focused quality summary for the Demo workspace content library.",
        icon: ShieldCheck,
        kind: "health",
        span: "half",
        meta: "View details",
        score: { value: "78", label: "Good", tone: "green" },
        rows: [
          { title: "Content quality", meta: "Originality and clarity", status: "92", tone: "green" },
          { title: "Keyword coverage", meta: "Primary and supporting queries", status: "78", tone: "blue" },
          { title: "Internal linking", meta: "Relevant in-library paths", status: "72", tone: "amber" },
          { title: "Meta data", meta: "Titles and descriptions", status: "88", tone: "green" }
        ]
      }
    ]
  },

  geo: {
    layout: "geo",
    eyebrow: "GEO",
    title: "GEO Visibility & Answer Optimization",
    description: "Track how Demo workspace appears in generative AI search and improve answer inclusion.",
    nav: "GEO",
    action: "Add query",
    metrics: [
      { label: "AI Queries Tracked", value: "1,248", change: "+22%", detail: "from last month", icon: MessageCircleQuestion, tone: "purple" },
      { label: "Answer Inclusion Rate", value: "42%", change: "+8%", detail: "from last month", icon: FileCheck2, tone: "blue" },
      { label: "Citation Rate", value: "28%", change: "+6%", detail: "from last month", icon: Link2, tone: "green" },
      { label: "Avg GEO Impact Score", value: "78", change: "+12 points", detail: "from last month", icon: Sparkles, tone: "purple" },
      { label: "Prompt Coverage", value: "64%", change: "+14%", detail: "from last month", icon: Target, tone: "blue" },
      { label: "Source Trust Score", value: "82", change: "+6 points", detail: "from last month", icon: ShieldCheck, tone: "green" }
    ],
    sections: [
      {
        area: "geo-flow",
        title: "From Content to AI Visibility",
        description: "The GEO workflow used to structure, review, publish, and monitor Demo workspace content.",
        icon: Sparkles,
        kind: "flow",
        span: "wide",
        meta: "GEO workflow",
        steps: [
          { label: "Connected project", copy: "Demo workspace library context" },
          { label: "GEO template layer", copy: "Answer-ready structure" },
          { label: "AI answer review", copy: "Preview clarity and citations" },
          { label: "Publish & monitor", copy: "Track inclusion over time" }
        ]
      },
      {
        area: "geo-answer",
        title: "AI Answer Preview",
        description: "A representative answer preview for a Demo workspace discovery query.",
        icon: Bot,
        kind: "answer",
        span: "half",
        meta: "Try another query",
        rows: [
          { title: "What is the easiest way to start learning AI?", meta: "Demo workspace offers short, plain-English AI lessons, practical workflows, and copy-ready prompts designed to help beginners build useful skills without technical jargon.", status: "Good", tone: "green", kicker: "AI OVERVIEW" },
          { title: "Demo workspace", meta: "Primary owned source", status: "#1", tone: "purple" },
          { title: "AI learning guide", meta: "Supporting library page", status: "#2", tone: "blue" },
          { title: "Prompt fundamentals", meta: "Supporting course", status: "#3", tone: "green" }
        ]
      },
      {
        area: "geo-visibility",
        title: "Visibility Across AI Platforms",
        description: "Visibility trends across the selected generative search platforms.",
        icon: ChartNoAxesCombined,
        kind: "chart",
        chart: "trend",
        span: "half",
        meta: "Last 30 days",
        legend: ["ChatGPT", "Google AI", "Perplexity", "Claude"]
      },
      {
        area: "geo-content",
        title: "GEO-Optimized Content",
        description: "Demo workspace pages structured for clear, citeable answers.",
        icon: FileCheck2,
        kind: "table",
        variant: "library",
        span: "wide",
        meta: "All statuses",
        tabs: [{ label: "All content", active: true }, { label: "Blog posts" }, { label: "Guides" }, { label: "Prompts" }],
        columns: ["Title", "Type", "Target Prompts", "GEO Score", "Last Updated", "Actions"],
        rows: [
          { title: "The Beginner's Guide to AI Agents", category: "Blog posts", meta: "12", status: "In Review", tone: "green", score: "92", date: "May 24, 2025" },
          { title: "How to Write Prompts That Give Usable Answers", category: "Guides", meta: "8", status: "Approved", tone: "green", score: "88", date: "May 22, 2025" },
          { title: "A Practical RAG Explainer Without the Jargon", category: "Blog posts", meta: "15", status: "In Review", tone: "green", score: "85", date: "May 21, 2025" },
          { title: "Build a Personal AI Workflow in One Afternoon", category: "Guides", meta: "10", status: "Approved", tone: "green", score: "80", date: "May 20, 2025" },
          { title: "Investor-ready monthly update generator", category: "Prompts", meta: "9", status: "In Review", tone: "amber", score: "78", date: "May 18, 2025" },
          { title: "Learn AI in 5 Minutes a Day", category: "Blog posts", meta: "6", status: "Approved", tone: "amber", score: "72", date: "May 16, 2025" }
        ].map((row) => ({ ...row, tone: row.tone as DashboardTone, action: "Review", cells: [{ value: row.title }, { value: row.category.replace(/s$/, "") }, { value: row.meta }, { value: row.score, kind: "score" as const, tone: row.tone as DashboardTone }, { value: row.date }] }))
      },
      {
        area: "geo-mentions",
        title: "Top Blogs by AI Mentions",
        description: "Content with the most AI answer mentions.",
        icon: Bot,
        kind: "table",
        variant: "ranked",
        span: "third",
        meta: "View all →",
        columns: ["Blog Post", "Mentions", "Trend"],
        rows: [
          { title: "The Beginner's Guide to AI Agents", meta: "128 mentions", status: "+18%", tone: "green", rank: 1 },
          { title: "How to Write Usable AI Prompts", meta: "96 mentions", status: "+14%", tone: "green", rank: 2 },
          { title: "Build a Personal AI Workflow", meta: "74 mentions", status: "+9%", tone: "blue", rank: 3 },
          { title: "RAG Explained Without Jargon", meta: "62 mentions", status: "+7%", tone: "purple", rank: 4 }
        ]
      },
      {
        area: "geo-citations",
        title: "Citation Opportunities",
        description: "Queries where stronger source structure could increase reach.",
        icon: Link2,
        kind: "table",
        variant: "ranked",
        span: "third",
        meta: "View all →",
        columns: ["Opportunity", "Potential Reach", "Priority"],
        rows: [
          { title: "AI agents for beginners", meta: "12K potential reach", status: "High", tone: "red", rank: 1 },
          { title: "Prompt writing examples", meta: "9.8K potential reach", status: "High", tone: "red", rank: 2 },
          { title: "Simple RAG explanation", meta: "8.6K potential reach", status: "Medium", tone: "amber", rank: 3 },
          { title: "Beginner AI workflows", meta: "7.2K potential reach", status: "Medium", tone: "amber", rank: 4 }
        ]
      },
      {
        area: "geo-prompts",
        title: "Prompt Cluster Performance",
        description: "Answer inclusion by common Demo workspace discovery intent.",
        icon: Network,
        kind: "table",
        variant: "ranked",
        span: "third",
        meta: "View all →",
        columns: ["Prompt Cluster", "Inclusion", "Quality"],
        rows: [
          { title: "Beginner AI guidance", meta: "68% inclusion rate", status: "Strong", tone: "green", rank: 1 },
          { title: "Prompt templates", meta: "54% inclusion rate", status: "Good", tone: "green", rank: 2 },
          { title: "AI agent blueprints", meta: "46% inclusion rate", status: "Build", tone: "blue", rank: 3 },
          { title: "RAG comparisons", meta: "38% inclusion rate", status: "Improve", tone: "amber", rank: 4 }
        ]
      },
      {
        area: "geo-snippets",
        title: "Answer Snippet Quality Review",
        description: "Sampled queries and how clearly the Demo workspace answer appears.",
        icon: MessageCircleQuestion,
        kind: "table",
        span: "two-thirds",
        meta: "View all →",
        columns: ["AI Query", "Source / Last Seen", "Snippet Quality"],
        rows: [
          { title: "What are AI agents?", meta: "ChatGPT · May 25", status: "Excellent", tone: "green" },
          { title: "How do I write a useful AI prompt?", meta: "Google AI · May 24", status: "Good", tone: "green" },
          { title: "What is RAG in simple terms?", meta: "Perplexity · May 24", status: "Good", tone: "blue" },
          { title: "Best AI workflow for beginners?", meta: "Claude · May 23", status: "Fair", tone: "amber" }
        ]
      },
      {
        area: "geo-sources",
        title: "Source Citation Breakdown",
        description: "Citation distribution by Demo workspace content type.",
        icon: Database,
        kind: "chart",
        chart: "donut",
        span: "third",
        meta: "Last 30 days",
        legend: ["Blog posts", "Guides", "Prompts", "Courses"],
        score: { value: "312", label: "Citations", tone: "blue" }
      }
    ]
  },

  notifications: {
    layout: "notifications",
    eyebrow: "Notifications",
    title: "Notifications & Alerts",
    description: "Stay on top of updates, approvals, automation issues, sync problems, and reminders.",
    nav: "Notifications",
    action: "Manage alerts",
    metrics: [
      { label: "Unread Alerts", value: "12", change: "−40%", detail: "from last week", icon: MailCheck, tone: "purple", lowerIsBetter: true },
      { label: "Approval Needed", value: "8", change: "+33%", detail: "from last week", icon: Users, tone: "amber", lowerIsBetter: true },
      { label: "Failed Automations", value: "3", change: "−50%", detail: "from last week", icon: CircleAlert, tone: "purple", lowerIsBetter: true },
      { label: "Failed Syncs", value: "2", change: "−60%", detail: "from last week", icon: Workflow, tone: "blue", lowerIsBetter: true },
      { label: "Scheduled Today", value: "18", change: "+28%", detail: "vs. yesterday", icon: CalendarCheck2, tone: "blue" },
      { label: "Reminder Status", value: "Healthy", change: "Stable", detail: "all systems active", icon: Bell, tone: "green" }
    ],
    sections: [
      {
        area: "notifications-feed",
        title: "Notification Feed",
        description: "Demo workspace alerts ordered from newest to oldest.",
        icon: Bell,
        kind: "feed",
        span: "two-thirds",
        meta: "Most recent",
        tabs: [
          { label: "All", active: true },
          { label: "Unread" },
          { label: "Approvals" },
          { label: "Automations" },
          { label: "Syncs" }
        ],
        rows: [
          { title: "Blog post needs a final review", meta: "The Beginner's Guide to AI Agents · 2 hours ago", status: "Resolve", category: "Approvals", tone: "red" },
          { title: "Content approval needed", meta: "How to Write Prompts That Give Usable Answers · 3 hours ago", status: "View", category: "Approvals", tone: "amber" },
          { title: "Content sync retry scheduled", meta: "Demo workspace library sync · 5 hours ago", status: "Resolve", category: "Syncs", tone: "red" },
          { title: "Scheduled post ready", meta: "A Practical RAG Explainer · 7 hours ago", status: "View", category: "Automations", tone: "blue" },
          { title: "Optimization completed", meta: "Internal linking suggestions · 9 hours ago", status: "View", category: "Automations", tone: "green" },
          { title: "GEO review suggested", meta: "Three answer snippets changed · 1 day ago", status: "Review", category: "Approvals", tone: "purple" },
          { title: "Weekly content report ready", meta: "Your publishing and search summary · 1 day ago", status: "View", category: "Automations", tone: "blue" },
          { title: "Workspace preferences updated", meta: "Default content tone changed to informative · 2 days ago", status: "View", category: "Workspace", tone: "purple" }
        ]
      },
      {
        area: "notifications-trend",
        title: "Alerts Over Time",
        description: "Volume across alerts, errors, approvals, and reminders.",
        icon: ChartNoAxesCombined,
        kind: "chart",
        chart: "trend",
        span: "third",
        meta: "Last 30 days",
        legend: ["Total Alerts", "Errors", "Approvals", "Reminders"]
      },
      {
        area: "notifications-reliability",
        title: "Automation Reliability",
        description: "Reliability across the core Demo workspace workflow.",
        icon: Workflow,
        kind: "chart",
        chart: "reliability",
        span: "third",
        meta: "Last 30 days",
        legend: ["Successful", "Failed", "Timeouts"]
      },
      {
        area: "notifications-automation",
        title: "Automation Alerts",
        description: "Recent workflow conditions that may need attention.",
        icon: Settings,
        kind: "feed",
        span: "third",
        meta: "View all →",
        rows: [
          { title: "Blog publishing retry", meta: "2 hours ago", status: "High", tone: "red" },
          { title: "Keyword research delayed", meta: "1 day ago", status: "High", tone: "red" },
          { title: "SERP tracking delayed", meta: "1 day ago", status: "Medium", tone: "amber" },
          { title: "Report generation completed", meta: "2 days ago", status: "Low", tone: "blue" }
        ]
      },
      {
        area: "notifications-scheduled",
        title: "Scheduled Content Reminders",
        description: "The next Demo workspace publishing events.",
        icon: CalendarCheck2,
        kind: "feed",
        span: "third",
        meta: "View all →",
        rows: [
          { title: "A Practical RAG Explainer", meta: "Today · 2:00 PM", status: "Today", tone: "green" },
          { title: "AI Workflow Examples", meta: "Today · 4:00 PM", status: "Today", tone: "green" },
          { title: "Prompt Engineering Checklist", meta: "May 26, 2025", status: "Upcoming", tone: "blue" },
          { title: "AI Agents Topic Hub", meta: "May 27, 2025", status: "Upcoming", tone: "purple" }
        ]
      },
      {
        area: "notifications-approvals",
        title: "Approval Needed",
        description: "Content waiting for a Demo workspace review decision.",
        icon: Users,
        kind: "feed",
        span: "third",
        meta: "View all →",
        rows: [
          { title: "The Beginner's Guide to AI Agents", meta: "Blog post · 3 hours ago", status: "High", tone: "red" },
          { title: "How to Write Usable AI Prompts", meta: "Blog post · 1 day ago", status: "Medium", tone: "amber" },
          { title: "Prompt Library Refresh", meta: "Product content · 1 day ago", status: "Medium", tone: "amber" },
          { title: "GEO Content Guidelines", meta: "Document · 2 days ago", status: "Low", tone: "blue" }
        ]
      },
      {
        area: "notifications-failures",
        title: "Failed Jobs / Sync Errors",
        description: "Failed jobs, sync attempts, and scheduled retries.",
        icon: CircleAlert,
        kind: "table",
        span: "third",
        meta: "View all →",
        columns: ["Job / Sync", "Type", "Status"],
        rows: [
          { title: "Library content sync", meta: "Sync · 5 hours ago", status: "Failed", tone: "red" },
          { title: "Blog post publishing", meta: "Automation · 2 hours ago", status: "Failed", tone: "red" },
          { title: "GEO answer data", meta: "Sync · 1 day ago", status: "Failed", tone: "red" },
          { title: "Keyword rank tracking", meta: "Automation · 1 day ago", status: "Timeout", tone: "amber" }
        ]
      },
      {
        area: "notifications-channels",
        title: "Notification Channels & Delivery",
        description: "Delivery health for each configured notification channel.",
        icon: Send,
        kind: "table",
        variant: "channels",
        span: "third",
        meta: "Last 30 days",
        columns: ["Channel", "Delivery", "Health"],
        rows: [
          { title: "In-app notifications", meta: "98% delivery", status: "Healthy", tone: "green" },
          { title: "Email notifications", meta: "96% delivery", status: "Healthy", tone: "green" },
          { title: "Slack workspace", meta: "92% delivery", status: "Ready", tone: "blue" },
          { title: "Browser push", meta: "89% delivery", status: "Degraded", tone: "amber" }
        ]
      },
      {
        area: "notifications-rules",
        title: "Escalation Rules",
        description: "Routing rules represented in the reference notification experience.",
        icon: ShieldCheck,
        kind: "feed",
        span: "third",
        meta: "Manage →",
        rows: [
          { title: "Automation failures", meta: "Alert immediately", status: "On", tone: "green" },
          { title: "Repeated sync failures", meta: "Notify after 2 failures", status: "On", tone: "green" },
          { title: "Approval overdue", meta: "Escalate after 48 hours", status: "On", tone: "green" },
          { title: "High-impact errors", meta: "Page team + Slack", status: "On", tone: "green" }
        ]
      },
      {
        area: "notifications-resolved",
        title: "Recently Resolved",
        description: "A complete-width history of recently resolved issues.",
        icon: ShieldCheck,
        kind: "table",
        variant: "audit",
        span: "wide",
        meta: "View all →",
        columns: ["Issue", "Type", "Resolved At", "Resolved By", "Notes"],
        rows: [
          { title: "Keyword rank tracking timeout", meta: "May 24, 4:32 PM · System", status: "Completed on retry", tone: "green" },
          { title: "Content library sync error", meta: "May 24, 1:15 PM · Alex Chen", status: "Rate limit resolved", tone: "green" },
          { title: "Blog post publishing failed", meta: "May 23, 6:20 PM · System", status: "Restored", tone: "green" },
          { title: "GEO data sync failed", meta: "May 23, 11:08 AM · System", status: "Reconnected", tone: "green" }
        ].map((row, index) => ({ ...row, tone: "green" as const, cells: [{ value: row.title }, { value: index % 2 ? "Sync" : "Automation" }, { value: row.meta.split(" · ")[0] }, { value: row.meta.split(" · ")[1] }, { value: row.status }] }))
      }
    ]
  },

  history: {
    layout: "history",
    eyebrow: "History",
    title: "Workspace History",
    description: "Review everything that happened across content creation, publishing, approvals, syncs, and updates.",
    nav: "History",
    action: "Export log",
    metrics: [
      { label: "Total Actions This Month", value: "1,482", change: "+24%", detail: "from last month", icon: Activity, tone: "purple" },
      { label: "Posts Published", value: "126", change: "+29%", detail: "from last month", icon: FileCheck2, tone: "blue" },
      { label: "Manual Updates", value: "312", change: "+18%", detail: "from last month", icon: Settings, tone: "green" },
      { label: "API Sync Events", value: "428", change: "+36%", detail: "from last month", icon: Workflow, tone: "purple" },
      { label: "Automation Runs", value: "540", change: "+22%", detail: "from last month", icon: Bot, tone: "blue" },
      { label: "Failed Actions", value: "18", change: "−40%", detail: "from last month", icon: CircleAlert, tone: "amber", lowerIsBetter: true }
    ],
    sections: [
      {
        area: "history-trend",
        title: "Activity Trend",
        description: "Total workspace actions across publishing, updates, sync events, and automation.",
        icon: ChartNoAxesCombined,
        kind: "chart",
        chart: "trend",
        span: "two-thirds",
        meta: "Last 14 days",
        legend: ["Publishing", "Manual Updates", "Sync Events", "Automation", "Failed Actions"]
      },
      {
        area: "history-categories",
        title: "Actions by Category",
        description: "Distribution of the 1,482 workspace actions by category.",
        icon: Layers3,
        kind: "chart",
        chart: "donut",
        span: "third",
        meta: "May 2025",
        legend: ["Publishing", "Updates", "Sync Events", "Automation", "Other"],
        distribution: [8.5, 21.1, 28.9, 36.4, 5.1],
        score: { value: "1,482", label: "Total", tone: "purple" }
      },
      {
        area: "history-stream",
        title: "Recent Activity Stream",
        description: "The latest workspace actions for Demo workspace.",
        icon: History,
        kind: "feed",
        span: "half",
        meta: "View all →",
        rows: [
          { title: "Blog post published", meta: "Learn AI in 5 Minutes a Day · 2 minutes ago", status: "Published", tone: "green" },
          { title: "Manual update", meta: "Updated meta description · 14 minutes ago", status: "Updated", tone: "blue" },
          { title: "API sync completed", meta: "Content data synced · 27 minutes ago", status: "Success", tone: "green" },
          { title: "Automation run finished", meta: "Internal linking suggestions · 1 hour ago", status: "Completed", tone: "purple" },
          { title: "Approval request submitted", meta: "AI agents guide · 2 hours ago", status: "Pending", tone: "amber" },
          { title: "Content reverted", meta: "Restored previous version · 4 hours ago", status: "Reverted", tone: "purple" }
        ]
      },
      {
        area: "history-filters",
        title: "Quick Filters",
        description: "The filter set planned for the fully connected audit log.",
        icon: SlidersHorizontal,
        kind: "summary",
        span: "half",
        meta: "Clear all",
        stats: [
          { label: "All Activities", value: "1,482", tone: "purple" },
          { label: "Publishing", value: "126", tone: "blue" },
          { label: "Manual Updates", value: "312", tone: "green" },
          { label: "Sync Events", value: "428", tone: "purple" },
          { label: "Automation", value: "540", tone: "amber" },
          { label: "Failures", value: "18", tone: "red" }
        ]
      },
      {
        area: "history-actors",
        title: "Activity by Actor",
        description: "Who or what made the workspace changes.",
        icon: Users,
        kind: "table",
        variant: "ranked",
        span: "half",
        meta: "Last 14 days",
        columns: ["Actor", "Actions", "Share"],
        rows: [
          { title: "John Doe (You)", meta: "562 actions", status: "38%", tone: "purple", rank: 1 },
          { title: "Workspace AI", meta: "428 actions", status: "29%", tone: "blue", rank: 2 },
          { title: "Sarah Smith", meta: "186 actions", status: "13%", tone: "green", rank: 3 },
          { title: "System / Integrations", meta: "92 actions", status: "6%", tone: "amber", rank: 4 }
        ]
      },
      {
        area: "history-audit",
        title: "Detailed Audit Log",
        description: "Complete history of sample workspace actions.",
        icon: ListChecks,
        kind: "table",
        variant: "audit",
        span: "wide",
        meta: "All types · All statuses",
        columns: ["Date & Time", "Type", "Description", "Content", "Actor", "Status", "Actions"],
        rows: [
          { date: "May 25, 2025 10:24 AM", category: "Publish", title: "Blog post published successfully", meta: "Learn AI in 5 Minutes a Day", actor: "John Doe", status: "Success", tone: "green" },
          { date: "May 25, 2025 10:12 AM", category: "Update", title: "Updated meta description", meta: "How to Write Usable AI Prompts", actor: "John Doe", status: "Success", tone: "green" },
          { date: "May 25, 2025 9:47 AM", category: "Sync", title: "Content library data synced", meta: "Demo workspace library (24 items)", actor: "System", status: "Success", tone: "green" },
          { date: "May 25, 2025 8:31 AM", category: "Automation", title: "Internal linking suggestions completed", meta: "5 blog posts", actor: "Workspace AI", status: "Success", tone: "green" },
          { date: "May 24, 2025 6:14 PM", category: "Approval", title: "Approval request submitted", meta: "The Beginner's Guide to AI Agents", actor: "Sarah Smith", status: "Pending", tone: "amber" },
          { date: "May 24, 2025 2:56 PM", category: "Publish", title: "Post publication failed (rate limit)", meta: "A Practical RAG Explainer", actor: "System", status: "Failed", tone: "red" },
          { date: "May 24, 2025 1:22 PM", category: "Revert", title: "Reverted to previous version", meta: "AI Workflow Guide", actor: "John Doe", status: "Success", tone: "green" },
          { date: "May 24, 2025 11:08 AM", category: "GEO", title: "Updated AI search visibility settings", meta: "Site-wide", actor: "Workspace AI", status: "Success", tone: "green" }
        ].map((row) => ({ ...row, tone: row.tone as DashboardTone, action: "Details", cells: [{ value: row.date }, { value: row.category }, { value: row.title }, { value: row.meta }, { value: row.actor }, { value: row.status, kind: "status" as const, tone: row.tone as DashboardTone }] }))
      },
      {
        area: "history-workareas",
        title: "Most Active Work Areas",
        description: "Where workspace activity happened most often.",
        icon: Database,
        kind: "table",
        variant: "ranked",
        span: "quarter",
        meta: "This month",
        columns: ["Area", "Actions", "Share"],
        rows: [
          { title: "Blog Content", meta: "482 actions", status: "32%", tone: "purple", rank: 1 },
          { title: "Learning Guides", meta: "308 actions", status: "21%", tone: "blue", rank: 2 },
          { title: "Site SEO", meta: "246 actions", status: "17%", tone: "green", rank: 3 }
        ]
      },
      {
        area: "history-edited",
        title: "Most Edited Content",
        description: "Items with the most editorial updates.",
        icon: FileCheck2,
        kind: "table",
        variant: "ranked",
        span: "quarter",
        meta: "This month",
        columns: ["Content", "Updates", "Status"],
        rows: [
          { title: "AI Agents Guide", meta: "24 updates", status: "Active", tone: "green", rank: 1 },
          { title: "Prompt Checklist", meta: "18 updates", status: "Active", tone: "green", rank: 2 },
          { title: "RAG Explainer", meta: "16 updates", status: "Review", tone: "amber", rank: 3 }
        ]
      },
      {
        area: "history-publishing",
        title: "Publish History",
        description: "Recent publication outcomes.",
        icon: Send,
        kind: "feed",
        span: "quarter",
        meta: "Recent",
        rows: [
          { title: "May 25 · 10:24 AM", meta: "One Demo workspace item", status: "Success", tone: "green" },
          { title: "May 24 · 4:12 PM", meta: "Three Demo workspace items", status: "Success", tone: "green" },
          { title: "May 23 · 2:36 PM", meta: "Publication retry", status: "Failed", tone: "red" }
        ]
      },
      {
        area: "history-reverts",
        title: "Reverts & Rejections",
        description: "Recent content decisions that were rolled back.",
        icon: History,
        kind: "feed",
        span: "quarter",
        meta: "Recent",
        rows: [
          { title: "May 24 · 1:22 PM", meta: "AI agents guide", status: "Reverted", tone: "purple" },
          { title: "May 22 · 3:16 PM", meta: "Prompt library refresh", status: "Rejected", tone: "red" },
          { title: "May 19 · 11:08 AM", meta: "RAG explainer", status: "Reverted", tone: "purple" }
        ]
      }
    ]
  }
};
