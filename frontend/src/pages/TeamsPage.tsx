import { ChevronRight, Crown, Pencil, Plus, Search, Trash2, UserMinus, UserPlus, UsersRound } from "lucide-react";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Modal } from "../components/Modal";
import { EmptyState, ErrorState, LoadingState } from "../components/PageState";
import { request } from "../lib/api";
import { formatDate, titleCase } from "../lib/format";
import type { Team, User } from "../types/api";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";

type TeamEditor = { mode: "create" } | { mode: "edit"; team: Team };

export function TeamsPage() {
  const { user } = useAuth();
  const { success, error: notifyError } = useToast();
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [editor, setEditor] = useState<TeamEditor | null>(null);
  const [membersTeam, setMembersTeam] = useState<Team | null>(null);

  const load = useCallback(async () => { setLoading(true); try { setTeams(await request<Team[]>("/teams/", { query: { limit: 100, search: search || undefined, sort_by: "name", sort_order: "asc" } })); setError(null); } catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to load teams."); } finally { setLoading(false); } }, [search]);
  useEffect(() => { const timeout = window.setTimeout(() => void load(), 250); return () => window.clearTimeout(timeout); }, [load]);
  const submit = async (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); const form = new FormData(event.currentTarget); const payload = { name: String(form.get("name")), description: String(form.get("description")) }; try { if (editor?.mode === "create") await request<Team>("/teams/", { method: "POST", body: JSON.stringify(payload) }); else if (editor) await request<Team>(`/teams/${editor.team.id}`, { method: "PUT", body: JSON.stringify(payload) }); success(editor?.mode === "create" ? "Team created." : "Team updated."); setEditor(null); await load(); } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to save team."); } };
  const deleteTeam = async (team: Team) => { try { await request(`/teams/${team.id}`, { method: "DELETE" }); success("Team deleted."); await load(); } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to delete team."); } };
  const isAdmin = user?.role.toLowerCase() === "admin";

  return <>
    <section className="page-heading"><div><p className="eyebrow">People & ownership</p><h1>Teams</h1><p>Set up the groups that own work, and keep their membership clear.</p></div>{isAdmin && <button className="button button--primary" onClick={() => setEditor({ mode: "create" })}><Plus size={18} />New team</button>}</section>
    {!isAdmin && <div className="permission-notice"><Crown size={18} /><span>Team administration is available to Admin users. Your backend applies this restriction too.</span></div>}
    <section className="toolbar"><label className="search-field"><Search size={18} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search teams" /></label><span className="toolbar__spacer" /><span className="result-count">{teams.length} teams</span></section>
    {loading ? <LoadingState /> : error ? <ErrorState error={error} retry={() => void load()} /> : teams.length ? <section className="team-grid">{teams.map((team) => <article className="team-card" key={team.id}><div className="team-card__avatar">{team.name.slice(0, 1).toUpperCase()}</div><div className="team-card__body"><h2>{team.name}</h2><p>{team.description}</p><span>Created {formatDate(team.created_at)}</span></div><footer><button className="button button--secondary" onClick={() => setMembersTeam(team)}><UsersRound size={16} />Members</button>{isAdmin && <div className="inline-actions"><button className="icon-button" onClick={() => setEditor({ mode: "edit", team })} aria-label={`Edit ${team.name}`}><Pencil size={17} /></button><button className="icon-button danger-button" onClick={() => void deleteTeam(team)} aria-label={`Delete ${team.name}`}><Trash2 size={17} /></button></div>}</footer></article>)}</section> : <EmptyState title="No teams found" detail="Create a team to group people and projects." action={isAdmin ? <button className="button button--primary" onClick={() => setEditor({ mode: "create" })}>Create team</button> : undefined} />}
    {editor && <Modal title={editor.mode === "create" ? "Create team" : "Edit team"} onClose={() => setEditor(null)}><form className="form-stack" onSubmit={submit}><label><span>Team name</span><input name="name" required minLength={2} maxLength={255} defaultValue={editor.mode === "edit" ? editor.team.name : ""} placeholder="Product design" /></label><label><span>Description</span><textarea name="description" required minLength={3} maxLength={100} defaultValue={editor.mode === "edit" ? editor.team.description : ""} placeholder="What this team owns" rows={3} /></label><div className="modal__actions"><button type="button" className="button button--secondary" onClick={() => setEditor(null)}>Cancel</button><button className="button button--primary">{editor.mode === "create" ? "Create team" : "Save changes"}</button></div></form></Modal>}
    {membersTeam && <TeamMembersModal team={membersTeam} onClose={() => setMembersTeam(null)} />}
  </>;
}

function TeamMembersModal({ team, onClose }: { team: Team; onClose: () => void }) {
  const { user } = useAuth();
  const { success, error: notifyError } = useToast();
  const [members, setMembers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const isAdmin = user?.role.toLowerCase() === "admin";
  const load = useCallback(async () => { setLoading(true); try { setMembers(await request<User[]>(`/teams/${team.id}/members`)); } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to load members."); } finally { setLoading(false); } }, [notifyError, team.id]);
  useEffect(() => { void load(); }, [load]);
  const addMember = async (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); const form = new FormData(event.currentTarget); try { await request(`/teams/${team.id}/members`, { method: "POST", body: JSON.stringify({ user_id: Number(form.get("user_id")), role: String(form.get("role")) }) }); success("Member added."); setAdding(false); await load(); } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to add member."); } };
  const removeMember = async (member: User) => { try { await request(`/teams/${team.id}/members/${member.id}`, { method: "DELETE" }); success("Member removed."); await load(); } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to remove member."); } };
  return <Modal title={`${team.name} members`} onClose={onClose}><div className="member-dialog">{isAdmin && <button className="button button--secondary button--full" onClick={() => setAdding((open) => !open)}><UserPlus size={16} />Add member</button>}{adding && <form className="add-member-form" onSubmit={addMember}><label><span>User ID</span><input required name="user_id" type="number" min="1" placeholder="e.g. 12" /></label><label><span>Team role</span><select name="role" defaultValue="developer"><option value="developer">Developer</option><option value="manager">Manager</option></select></label><button className="button button--primary">Add</button></form>}{loading ? <LoadingState label="Loading members…" /> : members.length ? <ul className="member-list">{members.map((member) => <li key={member.id}><span className="avatar">{member.full_name.slice(0, 1)}</span><span><strong>{member.full_name}</strong><small>{member.email} · {titleCase(member.role)}</small></span>{isAdmin && <button className="icon-button danger-button" onClick={() => void removeMember(member)} aria-label={`Remove ${member.full_name}`}><UserMinus size={17} /></button>}<ChevronRight size={17} className="muted-icon" /></li>)}</ul> : <EmptyState title="No members yet" detail="Use a User ID to add someone to this team." />}</div></Modal>;
}
