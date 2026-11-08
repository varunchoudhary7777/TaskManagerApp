import { CheckCircle2, Database, KeyRound, Radio, Search, ServerCog, ShieldCheck, UserRound, UsersRound } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "../components/PageState";
import { request } from "../lib/api";
import { titleCase } from "../lib/format";
import type { User } from "../types/api";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";

const roles = ["developer", "manager", "admin"] as const;

export function SettingsPage() {
  const { user } = useAuth();
  const { success, error: showError } = useToast();
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [userSearch, setUserSearch] = useState("");
  const [usersLoading, setUsersLoading] = useState(false);
  const [usersError, setUsersError] = useState<string | null>(null);
  const [roleDrafts, setRoleDrafts] = useState<Record<number, string>>({});
  const [updatingUserId, setUpdatingUserId] = useState<number | null>(null);

  const isAdmin = user?.role.toLowerCase() === "admin";

  const checkHealth = useCallback(async () => {
    try {
      await request("/health");
      setHealthy(true);
    } catch {
      setHealthy(false);
    }
  }, []);

  const loadUsers = useCallback(async () => {
    if (!isAdmin) return;

    setUsersLoading(true);
    try {
      const response = await request<User[]>("/auth/users/", {
        query: {
          limit: 100,
          search: userSearch.trim() || undefined,
        },
      });
      setUsers(response);
      setUsersError(null);
    } catch (caught) {
      setUsersError(caught instanceof Error ? caught.message : "Unable to load users.");
    } finally {
      setUsersLoading(false);
    }
  }, [isAdmin, userSearch]);

  useEffect(() => {
    void checkHealth();
  }, [checkHealth]);

  useEffect(() => {
    if (!isAdmin) return;
    const debounce = window.setTimeout(() => void loadUsers(), 250);
    return () => window.clearTimeout(debounce);
  }, [isAdmin, loadUsers]);

  const updateRole = async (target: User) => {
    const newRole = roleDrafts[target.id] ?? target.role.toLowerCase();
    setUpdatingUserId(target.id);
    try {
      const updatedUser = await request<User>(`/auth/change_role/${target.id}`, {
        method: "PUT",
        body: JSON.stringify({ new_role: newRole }),
      });
      setUsers((items) => items.map((item) => item.id === target.id ? updatedUser : item));
      setRoleDrafts((drafts) => ({ ...drafts, [target.id]: updatedUser.role.toLowerCase() }));
      success(`${updatedUser.full_name}'s role was updated.`);
    } catch (caught) {
      showError(caught instanceof Error ? caught.message : "Unable to change the role.");
    } finally {
      setUpdatingUserId(null);
    }
  };

  if (!user) return <LoadingState />;

  return <>
    <section className="page-heading">
      <div>
        <p className="eyebrow">Account & environment</p>
        <h1>Settings</h1>
        <p>Review your profile and the current API connection.</p>
      </div>
    </section>

    <section className="settings-grid">
      <article className="panel">
        <div className="panel__header"><div><h2>Your profile</h2><p>Your identity comes directly from the authenticated API session.</p></div></div>
        <div className="profile-settings">
          <span className="profile-settings__avatar">{user.full_name.slice(0, 1).toUpperCase()}</span>
          <div><strong>{user.full_name}</strong><span>{user.email}</span><em>{titleCase(user.role)}</em></div>
        </div>
        <dl className="settings-list">
          <div><dt><UserRound size={16} />User ID</dt><dd>#{user.id}</dd></div>
          <div><dt><KeyRound size={16} />Authentication</dt><dd>JWT access + refresh session</dd></div>
        </dl>
      </article>

      <article className="panel">
        <div className="panel__header"><div><h2>System status</h2><p>Live information from the backend services.</p></div></div>
        <dl className="settings-list">
          <div><dt><ServerCog size={16} />FastAPI health</dt><dd className={healthy === null ? "" : healthy ? "health health--good" : "health health--bad"}>{healthy === null ? "Checking…" : healthy ? <><CheckCircle2 size={15} />Healthy</> : "Unavailable"}</dd></div>
          <div><dt><Database size={16} />Database</dt><dd>{healthy ? "Connected" : "Checked through /health"}</dd></div>
          <div><dt><Radio size={16} />Realtime events</dt><dd>WebSocket notifications enabled</dd></div>
        </dl>
        <button className="button button--secondary" onClick={() => void checkHealth()}>Run health check</button>
      </article>
    </section>

    {isAdmin && <section className="panel audit-panel">
      <div className="panel__header" style={{ padding: "21px 21px 0" }}>
        <div><h2>User management</h2><p>Search people and assign their workspace role. Your own role is locked here to avoid accidentally removing your access.</p></div>
        <ShieldCheck size={19} className="muted-icon" />
      </div>
      <div className="toolbar" style={{ padding: "0 21px" }}>
        <label className="search-field"><Search size={18} /><input value={userSearch} onChange={(event) => setUserSearch(event.target.value)} placeholder="Search name or email" /></label>
        <span className="toolbar__spacer" />
        <span className="result-count">{users.length} {users.length === 1 ? "user" : "users"}</span>
      </div>
      {usersLoading ? <LoadingState label="Loading people…" /> : usersError ? <div style={{ padding: "0 21px 21px" }}><ErrorState error={usersError} retry={() => void loadUsers()} /></div> : users.length ? <div className="audit-table-wrap"><table className="audit-table"><thead><tr><th>Person</th><th>Current role</th><th>Change role</th><th /></tr></thead><tbody>{users.map((member) => {
        const isSelf = member.id === user.id;
        const selectedRole = roleDrafts[member.id] ?? member.role.toLowerCase();
        const changed = selectedRole !== member.role.toLowerCase();
        return <tr key={member.id}><td><strong>{member.full_name}</strong><br /><small>{member.email}</small></td><td>{titleCase(member.role)}</td><td><select aria-label={`Role for ${member.full_name}`} value={selectedRole} disabled={isSelf || updatingUserId === member.id} onChange={(event) => setRoleDrafts((drafts) => ({ ...drafts, [member.id]: event.target.value }))}>{roles.map((role) => <option key={role} value={role}>{titleCase(role)}</option>)}</select></td><td><button className="button button--secondary" disabled={isSelf || !changed || updatingUserId === member.id} title={isSelf ? "You cannot change your own role here." : undefined} onClick={() => void updateRole(member)}>{updatingUserId === member.id ? "Updating…" : isSelf ? "Current user" : "Save role"}</button></td></tr>;
      })}</tbody></table></div> : <div style={{ padding: "0 21px 21px" }}><EmptyState title="No users found" detail="Try a different name or email address." action={<UsersRound size={18} />} /></div>}
    </section>}
  </>;
}
