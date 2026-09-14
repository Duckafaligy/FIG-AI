import {
  Bell,
  Clock3,
  FileCheck2,
  Gauge,
  Globe2,
  History,
  Layers3,
  Link2,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Users,
  Workflow
} from "lucide-react";

type Icon = typeof Search;
type Row = { title: string; meta: string; status: string; tone?: "green" | "blue" | "purple" | "amber" | "red" };

export type DashboardPage = {
  eyebrow: string;
  title: string;
  description: string;
  nav: string;
  action: string;
  metrics: { label: string; value: string; change: string; detail: string; icon: Icon; tone?: "green" | "blue" | "purple" | "amber" }[];
  sections: {
    title: string;
    description: string;
    icon: Icon;
    kind: "chart" | "table" | "feed" | "flow";
    chart?: "trend" | "bars" | "donut" | "reliability";
    span?: "wide";
    legend?: string[];
    rows?: Row[];
    columns?: [string, string, string];
    steps?: { label: string; copy: string }[];
  }[];
};

const launchVaultContent: Row[] = [
  { title: "Learn AI in 5 Minutes a Day", meta: "Guide · Updated today", status: "Published", tone: "green" },
  { title: "Investor-ready monthly update generator", meta: "Prompt · Reviewed 2h ago", status: "Ready", tone: "blue" },
  { title: "Ship a lead-magnet in 7 steps", meta: "Workflow · In review", status: "Review", tone: "amber" },
  { title: "Why long-context models change RAG strategy", meta: "Daily insight · Scheduled", status: "Scheduled", tone: "purple" }
];

export const dashboardPages: Record<string, DashboardPage> = {
  overview: {
    eyebrow: "LaunchVault.ca · Overview",
    title: "Content performance overview",
    description: "A single project workspace for LaunchVault's clear, no-jargon AI learning library.",
    nav: "Overview",
    action: "New content",
    metrics: [
      { label: "Published lessons", value: "1,500", change: "+12", detail: "in this preview", icon: FileCheck2, tone: "purple" },
      { label: "Organic traffic", value: "18.4K", change: "+18.7%", detail: "last 30 days", icon: Gauge, tone: "blue" },
      { label: "Average impact", value: "84", change: "+6 pts", detail: "from optimization", icon: Sparkles, tone: "amber" },
      { label: "Search visibility", value: "62%", change: "+9%", detail: "across tracked queries", icon: Globe2, tone: "green" },
      { label: "Content in review", value: "8", change: "+3", detail: "seeded editorial items", icon: FileCheck2, tone: "blue" },
      { label: "AI answer citations", value: "128", change: "+18%", detail: "illustrative monitoring", icon: Link2, tone: "green" }
    ],
    sections: [
      { title: "Performance trends", description: "Illustrative preview data for LaunchVault.ca until Search Console and analytics are connected.", icon: Gauge, kind: "chart", chart: "trend", span: "wide", legend: ["Organic traffic", "Impressions", "Published lessons"] },
      { title: "Top opportunities", description: "Ideas shaped around LaunchVault's AI learning catalogue.", icon: Sparkles, kind: "feed", rows: [
        { title: "Build a beginner AI glossary hub", meta: "Opportunity · 18 related terms", status: "High", tone: "red" },
        { title: "Expand the prompt-engineering learning path", meta: "Content gap · 9 supporting lessons", status: "High", tone: "red" },
        { title: "Link agent blueprints to workflow guides", meta: "Internal linking · 14 suggestions", status: "Medium", tone: "amber" },
        { title: "Refresh AI tool comparison pages", meta: "Optimization · 6 pages", status: "Medium", tone: "amber" }
      ] },
      { title: "Library sample", description: "The LaunchVault items currently represented in this preview.", icon: FileCheck2, kind: "table", columns: ["Content", "Last update", "Status"], rows: launchVaultContent },
      { title: "Content health", description: "A working snapshot of content quality signals across the LaunchVault library.", icon: ShieldCheck, kind: "feed", rows: [
        { title: "Plain-English readability", meta: "Library writing standard", status: "92 / 100", tone: "green" },
        { title: "Topic coverage", meta: "Prompting, agents, business, and workflows", status: "50 topics", tone: "blue" },
        { title: "Internal linking", meta: "Connections between lessons and guides", status: "78 / 100", tone: "amber" }
      ] },
      { title: "Content mix", description: "Illustrative distribution of lessons, prompts, workflows, and daily insights.", icon: Layers3, kind: "chart", chart: "donut", legend: ["Lessons", "Prompts", "Workflows"] },
      { title: "Recent workspace activity", description: "A preview of the latest LaunchVault content actions.", icon: History, kind: "table", span: "wide", columns: ["Action", "Content", "Status"], rows: [
        { title: "Published", meta: "Learn AI in 5 Minutes a Day", status: "2h ago", tone: "green" },
        { title: "Reviewed", meta: "Investor-ready monthly update generator", status: "5h ago", tone: "blue" },
        { title: "Optimized", meta: "Why long-context models change RAG strategy", status: "Yesterday", tone: "purple" }
      ] }
    ]
  },
  seo: {
    eyebrow: "LaunchVault.ca · SEO",
    title: "SEO content queue",
    description: "Plan learning content, target plain-English queries, and move reviewed work toward publication.",
    nav: "SEO",
    action: "Create brief",
    metrics: [
      { label: "Posts in queue", value: "8", change: "+3", detail: "ready to review", icon: Layers3, tone: "purple" },
      { label: "Published this month", value: "14", change: "+27%", detail: "vs. previous month", icon: FileCheck2, tone: "green" },
      { label: "Average SEO score", value: "82", change: "+4 pts", detail: "across reviewed items", icon: Gauge, tone: "amber" },
      { label: "Keywords tracked", value: "312", change: "+28%", detail: "across 50 topics", icon: Search, tone: "blue" },
      { label: "Linking suggestions", value: "14", change: "+5", detail: "in the preview queue", icon: Link2, tone: "purple" },
      { label: "Content freshness", value: "89%", change: "+5 pts", detail: "illustrative quality score", icon: Sparkles, tone: "green" }
    ],
    sections: [
      { title: "Content creation flow", description: "A focused route from LaunchVault topic to reviewed, publish-ready lesson.", icon: Workflow, kind: "flow", span: "wide", steps: [
        { label: "LaunchVault.ca", copy: "Library and topic context" },
        { label: "Query brief", copy: "Plain-English search intent" },
        { label: "Content review", copy: "Quality and clarity checks" },
        { label: "Publish", copy: "Ship to the learning library" }
      ] },
      { title: "Posts for review", description: "Seeded queue content for the single LaunchVault project.", icon: FileCheck2, kind: "table", span: "wide", columns: ["Content", "Target query", "Status"], rows: [
        { title: "The beginner's guide to AI agents", meta: "ai agents for beginners", status: "In review", tone: "amber" },
        { title: "How to write prompts that give usable answers", meta: "how to write ai prompts", status: "Queued", tone: "blue" },
        { title: "A practical RAG explainer without the jargon", meta: "what is RAG AI", status: "Draft", tone: "purple" },
        { title: "Build a personal AI workflow in one afternoon", meta: "ai workflow examples", status: "Ready", tone: "green" }
      ] },
      { title: "Keyword momentum", description: "Illustrative movement for LaunchVault's topic and prompt clusters.", icon: Gauge, kind: "chart", chart: "bars", legend: ["Top 3", "Top 10", "Top 50"] },
      { title: "Highest impact content", description: "The launch preview's strongest AI learning pieces.", icon: Sparkles, kind: "table", columns: ["Content", "Traffic", "Impact"], rows: [
        { title: "Learn AI in 5 Minutes a Day", meta: "4.2K organic visits", status: "92", tone: "green" },
        { title: "How to write prompts that give usable answers", meta: "2.8K organic visits", status: "88", tone: "green" },
        { title: "A practical RAG explainer without the jargon", meta: "1.9K organic visits", status: "84", tone: "blue" }
      ] },
      { title: "Internal linking suggestions", description: "Useful connections between LaunchVault's topic hubs and library content.", icon: Link2, kind: "table", columns: ["From content", "Suggested link", "Status"], rows: [
        { title: "Prompt Engineering Fundamentals", meta: "Copy-ready prompt library", status: "Add link", tone: "purple" },
        { title: "AI Agents & Blueprints", meta: "Build a personal AI workflow", status: "Add link", tone: "purple" },
        { title: "AI Search & RAG", meta: "Long-context models guide", status: "Add link", tone: "purple" }
      ] },
      { title: "Topic cluster coverage", description: "Preview coverage across LaunchVault's learning clusters.", icon: Layers3, kind: "chart", chart: "bars", legend: ["Prompting", "Agents", "Automation"] }
    ]
  },
  geo: {
    eyebrow: "LaunchVault.ca · GEO",
    title: "AI visibility & answer optimization",
    description: "Track how LaunchVault's plain-English learning content may surface in generative search.",
    nav: "GEO",
    action: "Add query",
    metrics: [
      { label: "Queries tracked", value: "64", change: "+12", detail: "across AI learning topics", icon: Search, tone: "blue" },
      { label: "Answer inclusion", value: "42%", change: "+8%", detail: "in preview monitoring", icon: Sparkles, tone: "purple" },
      { label: "Citation rate", value: "28%", change: "+6%", detail: "across sampled answers", icon: Link2, tone: "green" },
      { label: "Source trust", value: "82", change: "+6 pts", detail: "content quality signal", icon: ShieldCheck, tone: "amber" },
      { label: "Prompt coverage", value: "64%", change: "+14%", detail: "illustrative query coverage", icon: Globe2, tone: "blue" },
      { label: "Optimized pages", value: "22", change: "+5", detail: "tracked in this preview", icon: FileCheck2, tone: "purple" }
    ],
    sections: [
      { title: "From content to AI visibility", description: "The workflow connecting LaunchVault lessons to monitored answer experiences.", icon: Workflow, kind: "flow", span: "wide", steps: [
        { label: "LaunchVault library", copy: "Lessons, prompts, and guides" },
        { label: "GEO structure", copy: "Answer-ready content signals" },
        { label: "Answer preview", copy: "Review clarity and sources" },
        { label: "Monitor", copy: "Track inclusion over time" }
      ] },
      { title: "AI answer preview", description: "A seeded preview based on LaunchVault's public learning promise.", icon: Sparkles, kind: "feed", rows: [
        { title: "What is the easiest way to start learning AI?", meta: "LaunchVault is positioned around short, plain-English lessons and copy-ready prompts.", status: "Good", tone: "green" },
        { title: "How do I learn prompt engineering?", meta: "Opportunity to connect the Prompt Engineering Fundamentals course and prompt library.", status: "Improve", tone: "amber" },
        { title: "Where can I find AI workflows for beginners?", meta: "Workflow collection is a relevant source candidate for this intent.", status: "Good", tone: "green" }
      ] },
      { title: "Visibility across AI platforms", description: "Illustrative coverage for ChatGPT, Google AI Overviews, and Perplexity.", icon: Gauge, kind: "chart", chart: "trend", legend: ["ChatGPT", "Google AI", "Perplexity"] },
      { title: "GEO-optimized content", description: "LaunchVault pages prepared for answer-oriented discovery.", icon: FileCheck2, kind: "table", span: "wide", columns: ["Content", "Prompts", "Score"], rows: [
        { title: "The beginner's guide to AI agents", meta: "12 target prompts", status: "92", tone: "green" },
        { title: "A practical RAG explainer without the jargon", meta: "8 target prompts", status: "88", tone: "green" },
        { title: "AI workflow examples for beginners", meta: "10 target prompts", status: "82", tone: "blue" }
      ] },
      { title: "Citation opportunities", description: "Where clearer source structure could improve answer inclusion.", icon: Link2, kind: "feed", rows: [
        { title: "Define AI agents with a citeable first paragraph", meta: "Opportunity · potential reach 12K", status: "High", tone: "red" },
        { title: "Add a concise RAG comparison table", meta: "Opportunity · potential reach 9.8K", status: "Medium", tone: "amber" },
        { title: "Link workflow examples to source guides", meta: "Opportunity · potential reach 7.2K", status: "Medium", tone: "amber" }
      ] },
      { title: "Prompt cluster performance", description: "Illustrative inclusion quality by the way people ask AI learning questions.", icon: Sparkles, kind: "table", columns: ["Prompt cluster", "Inclusion", "Status"], rows: [
        { title: "Beginner AI guidance", meta: "How-to and starting points", status: "68%", tone: "green" },
        { title: "Prompt engineering", meta: "Templates and examples", status: "54%", tone: "blue" },
        { title: "AI agents", meta: "Blueprint and workflow queries", status: "46%", tone: "purple" }
      ] }
    ]
  },
  notifications: {
    eyebrow: "LaunchVault.ca · Notifications",
    title: "Notifications & alerts",
    description: "A preview of content approvals, sync health, and opportunities for the LaunchVault workspace.",
    nav: "Notifications",
    action: "Manage alerts",
    metrics: [
      { label: "Unread alerts", value: "7", change: "-40%", detail: "from last week", icon: Bell, tone: "purple" },
      { label: "Approval needed", value: "3", change: "+1", detail: "ready for review", icon: FileCheck2, tone: "amber" },
      { label: "Automation health", value: "96%", change: "+4%", detail: "preview reliability", icon: Workflow, tone: "green" },
      { label: "Scheduled today", value: "4", change: "+2", detail: "content actions", icon: Clock3, tone: "blue" },
      { label: "Delivery channels", value: "3", change: "+1", detail: "ready to configure", icon: Link2, tone: "purple" },
      { label: "Resolved this week", value: "9", change: "+3", detail: "illustrative activity", icon: ShieldCheck, tone: "green" }
    ],
    sections: [
      { title: "Notification feed", description: "Seeded workspace activity for LaunchVault.ca.", icon: Bell, kind: "feed", span: "wide", rows: [
        { title: "Content approval needed", meta: "The beginner's guide to AI agents is ready for a final review.", status: "2h ago", tone: "amber" },
        { title: "SEO brief completed", meta: "A brief for ‘what is RAG AI?’ is ready to use.", status: "4h ago", tone: "blue" },
        { title: "Library item published", meta: "Why long-context models change RAG strategy has been scheduled.", status: "Today", tone: "green" },
        { title: "GEO review suggested", meta: "Three prompt-engineering queries have new citation opportunities.", status: "Today", tone: "purple" }
      ] },
      { title: "Alerts over time", description: "Illustrative notification volume in the preview workspace.", icon: Gauge, kind: "chart", chart: "trend", legend: ["Total alerts", "Approvals", "Reminders"] },
      { title: "Delivery channels", description: "The routes ready to be wired to the single LaunchVault workspace.", icon: Link2, kind: "table", columns: ["Channel", "Purpose", "Status"], rows: [
        { title: "In-app notifications", meta: "Reviews and publishing", status: "Enabled", tone: "green" },
        { title: "Email updates", meta: "Weekly workspace summary", status: "Ready", tone: "blue" },
        { title: "Slack workspace", meta: "Team mentions and approvals", status: "Optional", tone: "purple" }
      ] },
      { title: "Approval needed", description: "Seeded content waiting on a LaunchVault review decision.", icon: FileCheck2, kind: "feed", rows: [
        { title: "The beginner's guide to AI agents", meta: "Final editorial pass", status: "High", tone: "red" },
        { title: "Build a personal AI workflow in one afternoon", meta: "SEO and clarity review", status: "Medium", tone: "amber" },
        { title: "A practical RAG explainer without the jargon", meta: "Fact-check before scheduling", status: "Medium", tone: "amber" }
      ] },
      { title: "Scheduled content", description: "The next content actions in the seeded LaunchVault calendar.", icon: Clock3, kind: "table", columns: ["Content", "Schedule", "Status"], rows: [
        { title: "Why long-context models change RAG strategy", meta: "Today · 2:00 PM", status: "Today", tone: "green" },
        { title: "Prompting fundamentals checklist", meta: "Tomorrow · 10:00 AM", status: "Scheduled", tone: "blue" },
        { title: "AI agents topic hub", meta: "May 28 · 9:00 AM", status: "Upcoming", tone: "purple" }
      ] },
      { title: "Automation reliability", description: "Preview reliability for the content workflows configured in this design.", icon: Workflow, kind: "chart", chart: "reliability", legend: ["Successful", "Retries", "Warnings"] }
    ]
  },
  history: {
    eyebrow: "LaunchVault.ca · History",
    title: "Workspace history",
    description: "A running view of the content, review, and optimization activity inside LaunchVault's project.",
    nav: "History",
    action: "Export log",
    metrics: [
      { label: "Actions this month", value: "148", change: "+24%", detail: "in preview activity", icon: History, tone: "purple" },
      { label: "Posts published", value: "14", change: "+29%", detail: "month to date", icon: FileCheck2, tone: "green" },
      { label: "Manual updates", value: "31", change: "+18%", detail: "content improvements", icon: Settings, tone: "amber" },
      { label: "Automation runs", value: "54", change: "+22%", detail: "workflow completions", icon: Workflow, tone: "blue" },
      { label: "GEO updates", value: "22", change: "+15%", detail: "illustrative monitoring", icon: Globe2, tone: "purple" },
      { label: "Review requests", value: "12", change: "+4", detail: "seeded content checks", icon: Users, tone: "green" }
    ],
    sections: [
      { title: "Activity trend", description: "Illustrative content activity for the LaunchVault project.", icon: Gauge, kind: "chart", chart: "trend", span: "wide", legend: ["Publishing", "Manual updates", "Automation"] },
      { title: "Recent activity", description: "Seeded activity derived from the LaunchVault learning catalogue.", icon: History, kind: "feed", rows: [
        { title: "Guide scheduled", meta: "The beginner's guide to AI agents moved to the review queue.", status: "12m ago", tone: "green" },
        { title: "Prompt refreshed", meta: "Investor-ready monthly update generator was updated for clarity.", status: "1h ago", tone: "blue" },
        { title: "GEO brief created", meta: "A new brief for AI workflow examples is ready for review.", status: "3h ago", tone: "purple" },
        { title: "Content link added", meta: "RAG explainer linked to the AI Search & RAG topic hub.", status: "Today", tone: "amber" }
      ] },
      { title: "Detailed audit log", description: "A preview of the searchable history that will be powered by the API later.", icon: ShieldCheck, kind: "table", span: "wide", columns: ["Action", "Detail", "Status"], rows: [
        { title: "Published lesson", meta: "Learn AI in 5 Minutes a Day", status: "Success", tone: "green" },
        { title: "Updated meta description", meta: "Why long-context models change RAG strategy", status: "Success", tone: "green" },
        { title: "Generated SEO brief", meta: "what is RAG AI", status: "Complete", tone: "blue" },
        { title: "Requested review", meta: "Build a personal AI workflow in one afternoon", status: "Pending", tone: "amber" }
      ] },
      { title: "Activity by actor", description: "A future workspace view of who is moving content forward.", icon: Users, kind: "table", columns: ["Actor", "Activity", "Share"], rows: [
        { title: "LaunchVault AI", meta: "Draft and optimization support", status: "42%", tone: "purple" },
        { title: "Content editor", meta: "Review and publishing", status: "31%", tone: "green" },
        { title: "SEO specialist", meta: "Briefs and keyword updates", status: "19%", tone: "blue" }
      ] },
      { title: "Most edited content", description: "Library pieces with the highest preview revision activity.", icon: Settings, kind: "table", columns: ["Content", "Updates", "Status"], rows: [
        { title: "How to write prompts that give usable answers", meta: "24 revisions", status: "Active", tone: "green" },
        { title: "A practical RAG explainer without the jargon", meta: "18 revisions", status: "Active", tone: "green" },
        { title: "Build a personal AI workflow in one afternoon", meta: "16 revisions", status: "Review", tone: "amber" }
      ] },
      { title: "Review outcomes", description: "A compact view of approvals and revisions across the content queue.", icon: FileCheck2, kind: "feed", rows: [
        { title: "Prompt library refresh approved", meta: "Quality review completed", status: "Approved", tone: "green" },
        { title: "AI agents guide revised", meta: "Clarity changes requested", status: "Revised", tone: "blue" },
        { title: "RAG explainer review pending", meta: "Awaiting final fact-check", status: "Pending", tone: "amber" }
      ] }
    ]
  }
};
