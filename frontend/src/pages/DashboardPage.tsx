import { AlertTriangle, ArrowUpRight, CheckCircle2, CircleDotDashed, ClipboardList, FolderKanban, Plus, UsersRound } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { EmptyState, ErrorState, LoadingState } from "../components/PageState";
import { StatusBadge } from "../components/StatusBadge";
import { request } from "../lib/api";
import { formatDate, titleCase } from "../lib/format";
import type { DashboardSummary } from "../types/api";
import { useAuth } from "../contexts/AuthContext";

export function DashboardPage() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    try {
      setError(null);
      setSummary(await request<DashboardSummary>("/dashboard/summary"));
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to load the dashboard."); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  if (!summary && !error) return <LoadingState />;
  if (error) return <ErrorState error={error} retry={() => void load()} />;
  if (!summary) return null;
  const isDeveloper = user?.role.toLowerCase() === "developer";
  const scopeDetail = summary.scope === "admin"
    ? summary.scope_description
    : `${summary.scope_description} ${summary.visible_team_count} ${summary.visible_team_count === 1 ? "team" : "teams"} in scope.`;
  const completion = summary.total_tasks ? Math.round((summary.completed_tasks / summary.total_tasks) * 100) : 0;
  const metrics = [
    { label: "Active projects", value: summary.active_projects, icon: FolderKanban, accent: "violet" },
    { label: "All tasks", value: summary.total_tasks, icon: ClipboardList, accent: "blue" },
    { label: "Overdue", value: summary.overdue_tasks, icon: AlertTriangle, accent: "red" },
    { label: "Unassigned", value: summary.unassigned_tasks, icon: UsersRound, accent: "amber" },
  ];
  const progress = [{ label: "To do", value: summary.todo_tasks, tone: "todo" }, { label: "In progress", value: summary.in_progress_tasks, tone: "progress" }, { label: "Completed", value: summary.completed_tasks, tone: "done" }];

  return <>
    <section className="page-heading"><div><p className="eyebrow">{summary.scope_label}</p><h1>Good {new Date().getHours() < 12 ? "morning" : new Date().getHours() < 18 ? "afternoon" : "evening"}, {user?.full_name.split(" ")[0]}.</h1><p>{scopeDetail}</p></div>{!isDeveloper && <Link className="button button--primary" to="/projects?new=1"><Plus size={18} />New project</Link>}</section>
    <section className="metric-grid">{metrics.map(({ label, value, icon: Icon, accent }) => <article className={`metric-card metric-card--${accent}`} key={label}><div className="metric-card__icon"><Icon size={20} /></div><p>{label}</p><strong>{value}</strong></article>)}</section>
    <section className="dashboard-grid">
      <article className="panel panel--progress"><div className="panel__header"><div><h2>Delivery momentum</h2><p>{completion}% of work is complete</p></div><span className="completion-ring">{completion}%</span></div><div className="stacked-progress" aria-label="Task completion progress">{progress.map((item) => <span key={item.label} className={`stacked-progress__segment stacked-progress__segment--${item.tone}`} style={{ width: `${summary.total_tasks ? (item.value / summary.total_tasks) * 100 : 0}%` }} />)}</div><div className="progress-legend">{progress.map((item) => <span key={item.label}><i className={`legend-dot legend-dot--${item.tone}`} />{item.label}<strong>{item.value}</strong></span>)}</div></article>
      <article className="panel panel--attention"><div className="panel__header"><div><h2>Needs attention</h2><p>Keep delivery risks visible.</p></div></div><div className="attention-row"><span className="attention-row__icon"><AlertTriangle size={18} /></span><div><strong>{summary.overdue_tasks} overdue task{summary.overdue_tasks === 1 ? "" : "s"}</strong><p>{summary.overdue_tasks ? "Review due dates and unblock the owners." : "No overdue tasks — great work."}</p></div><Link to="/tasks"><ArrowUpRight size={18} /></Link></div><div className="attention-row"><span className="attention-row__icon attention-row__icon--blue"><CircleDotDashed size={18} /></span><div><strong>{summary.unassigned_tasks} unassigned task{summary.unassigned_tasks === 1 ? "" : "s"}</strong><p>Assign clear owners to keep work moving.</p></div><Link to="/tasks"><ArrowUpRight size={18} /></Link></div></article>
    </section>
    <section className="content-grid content-grid--wide-left"><article className="panel"><div className="panel__header"><div><h2>Recent projects</h2><p>Recently updated work in your dashboard scope.</p></div><Link className="text-link" to="/projects">View all <ArrowUpRight size={15} /></Link></div>{summary.recent_projects.length ? <div className="project-list">{summary.recent_projects.map((project) => <Link to={`/projects?selected=${project.id}`} className="project-row" key={project.id}><span className="project-row__glyph">{project.name.slice(0, 1).toUpperCase()}</span><span className="project-row__content"><strong>{project.name}</strong><small>{project.description}</small></span><StatusBadge value={project.status} /><time>Updated {formatDate(project.updated_at)}</time></Link>)}</div> : <EmptyState title="No visible projects yet" detail={isDeveloper ? "You will see projects when you are added to a team." : "Create the first project for one of your teams."} action={!isDeveloper ? <Link className="button button--secondary" to="/projects?new=1">Create project</Link> : undefined} />}</article>
      <article className="panel"><div className="panel__header"><div><h2>Next open tasks</h2><p>Sorted by closest due date in your dashboard scope.</p></div><Link className="text-link" to="/tasks">Open tasks <ArrowUpRight size={15} /></Link></div>{summary.upcoming_tasks.length ? <div className="task-list">{summary.upcoming_tasks.map((task) => <Link to={`/tasks?task=${task.id}`} className="task-row" key={task.id}><span className="task-row__check"><CheckCircle2 size={17} /></span><span><strong>{task.title}</strong><small>{task.priority ? `${titleCase(task.priority)} priority` : "Priority not set"}</small></span><time>{task.due_date ? formatDate(task.due_date) : "No due date"}</time></Link>)}</div> : <EmptyState title="No open tasks" detail="Your visible projects have no incomplete tasks right now." />}</article></section>
  </>;
}
