import { Archive, ArrowDownUp, ChevronLeft, ChevronRight, CopyPlus, FolderKanban, MoreHorizontal, Pencil, Plus, RotateCcw, Search, Trash2, X } from "lucide-react";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Modal } from "../components/Modal";
import { EmptyState, ErrorState, LoadingState } from "../components/PageState";
import { StatusBadge } from "../components/StatusBadge";
import { request } from "../lib/api";
import { formatDate } from "../lib/format";
import type { Project, Team } from "../types/api";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";

type EditorState = { mode: "create" } | { mode: "edit"; project: Project };
const pageSize = 12;

export function ProjectsPage() {
  const { user } = useAuth();
  const { success, error: notifyError } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [status, setStatus] = useState(searchParams.get("status") ?? "");
  const [sort, setSort] = useState(searchParams.get("sort") ?? "updated_at");
  const [page, setPage] = useState(Number(searchParams.get("page") ?? "0"));
  const [editor, setEditor] = useState<EditorState | null>(searchParams.get("new") ? { mode: "create" } : null);
  const [openMenu, setOpenMenu] = useState<number | null>(null);
  const userRole = user?.role.toLowerCase();
  const isAdmin = userRole === "admin";
  const isDeveloper = userRole === "developer";
  const canCreateProject = userRole === "admin" || userRole === "manager";

  const syncUrl = useCallback((nextPage = page) => {
    const next = new URLSearchParams();
    if (search) next.set("search", search);
    if (status) next.set("status", status);
    if (sort !== "updated_at") next.set("sort", sort);
    if (nextPage) next.set("page", String(nextPage));
    setSearchParams(next, { replace: true });
  }, [page, search, setSearchParams, sort, status]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const teamRequest = isAdmin
        ? request<Team[]>("/teams/", { query: { limit: 100, sort_by: "name", sort_order: "asc" } })
        : user
          ? request<Team[]>(`/teams/users/${user.id}/teams`)
          : Promise.resolve([] as Team[]);
      const [projectList, teamList] = await Promise.all([
        request<Project[]>("/projects/", { query: { limit: pageSize, skip: page * pageSize, status: status || undefined, search: search || undefined, sort_by: sort, sort_order: "desc" } }),
        teamRequest,
      ]);
      setProjects(projectList);
      setTeams(teamList);
      setError(null);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to load projects."); }
    finally { setLoading(false); }
  }, [isAdmin, page, search, sort, status, user]);

  useEffect(() => { const timer = window.setTimeout(() => { syncUrl(); void load(); }, 250); return () => window.clearTimeout(timer); }, [load, syncUrl]);

  const teamName = useMemo(() => new Map(teams.map((team) => [team.id, team.name])), [teams]);
  const execute = async (label: string, action: () => Promise<unknown>) => {
    setOpenMenu(null);
    try { await action(); success(label); await load(); } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to update project."); }
  };

  const submitProject = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = { name: String(form.get("name")), description: String(form.get("description")), team_id: Number(form.get("team_id")), status: String(form.get("status")) };
    try {
      if (editor?.mode === "create") await request<Project>("/projects/", { method: "POST", body: JSON.stringify(payload) });
      else if (editor) await request<Project>(`/projects/${editor.project.id}`, { method: "PUT", body: JSON.stringify(payload) });
      success(editor?.mode === "create" ? "Project created." : "Project updated.");
      setEditor(null); await load();
    } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to save project."); }
  };

  return <>
    <section className="page-heading"><div><p className="eyebrow">Plan & deliver</p><h1>Projects</h1><p>Organize work by team, track progress, and keep priorities visible.</p></div>{canCreateProject && <button className="button button--primary" onClick={() => setEditor({ mode: "create" })}><Plus size={18} />New project</button>}</section>
    <section className="toolbar"><label className="search-field"><Search size={18} /><input value={search} onChange={(event) => { setPage(0); setSearch(event.target.value); }} placeholder="Search projects" /></label><select aria-label="Filter projects by status" value={status} onChange={(event) => { setPage(0); setStatus(event.target.value); }}><option value="">All statuses</option><option value="planning">Planning</option><option value="active">Active</option><option value="completed">Completed</option><option value="archived">Archived</option></select><select aria-label="Sort projects" value={sort} onChange={(event) => setSort(event.target.value)}><option value="updated_at">Recently updated</option><option value="created_at">Recently created</option><option value="name">Name</option><option value="status">Status</option></select><span className="toolbar__spacer" /><button className="button button--secondary" onClick={() => void load()}><ArrowDownUp size={16} />Refresh</button></section>
    {loading ? <LoadingState /> : error ? <ErrorState error={error} retry={() => void load()} /> : projects.length ? <section className="project-card-grid">{projects.map((project) => <article className="project-card" key={project.id}><div className="project-card__top"><span className="project-card__glyph">{project.name.slice(0, 1).toUpperCase()}</span>{!isDeveloper && <div className="action-menu"><button className="icon-button" aria-label={`Actions for ${project.name}`} onClick={() => setOpenMenu((current) => current === project.id ? null : project.id)}><MoreHorizontal size={20} /></button>{openMenu === project.id && <div className="action-menu__panel"><button onClick={() => setEditor({ mode: "edit", project })}><Pencil size={15} />Edit details</button><button onClick={() => void execute("Project archived.", () => request(`/projects/archive/${project.id}`, { method: "PUT" }))}><Archive size={15} />Archive</button>{isAdmin && <><button onClick={() => void execute("Project restored.", () => request(`/projects/restore/${project.id}`, { method: "PUT" }))}><RotateCcw size={15} />Restore</button><button className="danger" onClick={() => void execute("Project deleted.", () => request(`/projects/${project.id}`, { method: "DELETE" }))}><Trash2 size={15} />Delete</button></>}</div>}</div>}</div><div className="project-card__body"><StatusBadge value={project.status} /><h2>{project.name}</h2><p>{project.description}</p></div><footer><span>{teamName.get(project.team_id) ?? `Team #${project.team_id}`}</span><time>Updated {formatDate(project.updated_at)}</time></footer></article>)}</section> : <EmptyState title="No projects found" detail={search || status ? "Try changing your search or filters." : "Start by creating the first project for your team."} action={canCreateProject ? <button className="button button--primary" onClick={() => setEditor({ mode: "create" })}><CopyPlus size={17} />Create project</button> : undefined} />}
    <footer className="pagination"><span>Showing page {page + 1}</span><div><button className="icon-button" disabled={page === 0} onClick={() => setPage((current) => current - 1)} aria-label="Previous page"><ChevronLeft size={19} /></button><button className="icon-button" disabled={projects.length < pageSize} onClick={() => setPage((current) => current + 1)} aria-label="Next page"><ChevronRight size={19} /></button></div></footer>
    {editor && <Modal title={editor.mode === "create" ? "Create project" : "Edit project"} onClose={() => setEditor(null)}><form className="form-stack" onSubmit={submitProject}><label><span>Project name</span><input name="name" minLength={3} maxLength={100} required defaultValue={editor.mode === "edit" ? editor.project.name : ""} placeholder="Website redesign" /></label><label><span>Description</span><textarea name="description" minLength={3} maxLength={250} required defaultValue={editor.mode === "edit" ? editor.project.description : ""} placeholder="What outcome is this project working toward?" rows={4} /></label><div className="form-row"><label><span>Team</span><select name="team_id" required defaultValue={editor.mode === "edit" ? editor.project.team_id : ""}><option value="" disabled>Select a team</option>{teams.map((team) => <option value={team.id} key={team.id}>{team.name}</option>)}</select></label><label><span>Status</span><select name="status" defaultValue={editor.mode === "edit" ? projectStatus(editor.project.status) : "active"}><option value="planning">Planning</option><option value="active">Active</option><option value="completed">Completed</option><option value="archived">Archived</option></select></label></div><div className="modal__actions"><button type="button" className="button button--secondary" onClick={() => setEditor(null)}>Cancel</button><button className="button button--primary">{editor.mode === "create" ? "Create project" : "Save changes"}</button></div></form></Modal>}
  </>;
}

function projectStatus(value: string) { return value.toLowerCase(); }
