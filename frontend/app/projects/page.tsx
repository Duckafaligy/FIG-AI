import { AuthedDashboardShell } from "@/components/authed-dashboard-shell";
import { ProjectsList } from "@/components/projects-list";

export default function ProjectsPage() {
  return <AuthedDashboardShell><ProjectsList /></AuthedDashboardShell>;
}
