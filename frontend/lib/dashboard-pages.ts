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
  Workflow
} from "lucide-react";

export type DashboardPage = {
  eyebrow: string;
  title: string;
  description: string;
  nav: string;
  metrics: { label: string; icon: typeof Search }[];
  sections: { title: string; description: string; icon: typeof Search; kind?: "chart" | "table" | "feed" | "flow" }[];
};

export const dashboardPages: Record<string, DashboardPage> = {
  overview: {
    eyebrow: "Overview",
    title: "Content performance overview",
    description: "Track publishing, SEO, GEO, and content impact from one calm workspace.",
    nav: "Overview",
    metrics: [
      { label: "Published content", icon: FileCheck2 },
      { label: "Organic traffic", icon: Gauge },
      { label: "Average impact", icon: Sparkles },
      { label: "Search visibility", icon: Globe2 }
    ],
    sections: [
      { title: "Performance trends", description: "Traffic and visibility will appear after your first connected scan.", icon: Gauge, kind: "chart" },
      { title: "Content opportunities", description: "Recommendations will appear when FIG has enough site context.", icon: Sparkles, kind: "feed" },
      { title: "Published content", description: "Your connected content library will live here.", icon: FileCheck2, kind: "table" }
    ]
  },
  seo: {
    eyebrow: "SEO",
    title: "SEO content queue",
    description: "Create, optimize, review, and prepare search-ready content.",
    nav: "SEO",
    metrics: [
      { label: "Posts in queue", icon: Layers3 },
      { label: "Published this month", icon: FileCheck2 },
      { label: "Average SEO score", icon: Gauge },
      { label: "Keywords tracked", icon: Search }
    ],
    sections: [
      { title: "Content creation flow", description: "Connect a site to begin the keyword-to-publish workflow.", icon: Workflow, kind: "flow" },
      { title: "Posts for review", description: "Drafts awaiting review will appear here.", icon: FileCheck2, kind: "table" },
      { title: "Keyword momentum", description: "Ranking movement will appear after Search Console syncs.", icon: Gauge, kind: "chart" }
    ]
  },
  geo: {
    eyebrow: "GEO",
    title: "AI visibility & answer optimization",
    description: "Understand how your brand appears in generative search and where it can earn citations.",
    nav: "GEO",
    metrics: [
      { label: "Queries tracked", icon: Search },
      { label: "Answer inclusion", icon: Sparkles },
      { label: "Citation rate", icon: Link2 },
      { label: "Source trust", icon: ShieldCheck }
    ],
    sections: [
      { title: "From content to AI visibility", description: "Connect your content and choose the prompts you want FIG to monitor.", icon: Workflow, kind: "flow" },
      { title: "AI answer preview", description: "A sourced answer preview will appear once a query is monitored.", icon: Sparkles, kind: "feed" },
      { title: "Visibility across AI platforms", description: "Platform coverage will appear after the first monitoring cycle.", icon: Gauge, kind: "chart" }
    ]
  },
  notifications: {
    eyebrow: "Notifications",
    title: "Notifications & alerts",
    description: "Stay on top of approvals, automation issues, sync problems, and account activity.",
    nav: "Notifications",
    metrics: [
      { label: "Unread alerts", icon: Bell },
      { label: "Approval needed", icon: FileCheck2 },
      { label: "Failed automations", icon: Workflow },
      { label: "Scheduled today", icon: Clock3 }
    ],
    sections: [
      { title: "Notification feed", description: "You are all caught up. New alerts will appear here.", icon: Bell, kind: "feed" },
      { title: "Alerts over time", description: "Alert history will build as your automations run.", icon: Gauge, kind: "chart" },
      { title: "Delivery channels", description: "Connect email, Slack, or webhooks to route notifications.", icon: Link2, kind: "table" }
    ]
  },
  history: {
    eyebrow: "History",
    title: "Workspace history",
    description: "Review content changes, publishing, approvals, syncs, and manual updates.",
    nav: "History",
    metrics: [
      { label: "Actions this month", icon: History },
      { label: "Posts published", icon: FileCheck2 },
      { label: "Manual updates", icon: Settings },
      { label: "Automation runs", icon: Workflow }
    ],
    sections: [
      { title: "Activity trend", description: "Workspace activity will be charted here.", icon: Gauge, kind: "chart" },
      { title: "Recent activity", description: "No workspace activity has been recorded yet.", icon: History, kind: "feed" },
      { title: "Detailed audit log", description: "Searchable account actions will appear in this log.", icon: ShieldCheck, kind: "table" }
    ]
  },
  settings: {
    eyebrow: "Settings",
    title: "Settings & workspace configuration",
    description: "Manage your workspace, team, connections, billing, and content defaults.",
    nav: "Settings",
    metrics: [
      { label: "Team members", icon: Layers3 },
      { label: "Connected services", icon: Link2 },
      { label: "Active projects", icon: FileCheck2 },
      { label: "Plan usage", icon: Gauge }
    ],
    sections: [
      { title: "Workspace profile", description: "Add your organization details and primary domain.", icon: Settings, kind: "table" },
      { title: "Connections", description: "Supabase, OpenAI, Claude, Stripe, and publishing integrations will be managed here.", icon: Link2, kind: "table" },
      { title: "Billing & usage", description: "Plan limits and invoices will appear after Stripe is connected.", icon: Gauge, kind: "chart" }
    ]
  }
};
