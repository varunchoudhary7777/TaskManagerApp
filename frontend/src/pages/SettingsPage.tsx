import { CheckCircle2, Database, KeyRound, Radio, ServerCog, ShieldCheck, UserRound } from "lucide-react";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { LoadingState } from "../components/PageState";
import { request } from "../lib/api";
import { titleCase } from "../lib/format";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";

export function SettingsPage() {
  const { user } = useAuth();
  const { success, error } = useToast();
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const checkHealth = useCallback(async () => { try { await request("/health"); setHealthy(true); } catch { setHealthy(false); } }, []);
  useEffect(() => { void checkHealth(); }, [checkHealth]);
  const changeRole = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const userId = Number(form.get("user_id"));
    try {
      await request(`/auth/change_role/${userId}`, { method: "PUT", body: JSON.stringify({ new_role: form.get("new_role") }) });
      event.currentTarget.reset();
      success("User role updated.");
    } catch (caught) {
      error(caught instanceof Error ? caught.message : "Unable to change the role.");
    }
  };
  if (!user) return <LoadingState />;
  return <><section className="page-heading"><div><p className="eyebrow">Account & environment</p><h1>Settings</h1><p>Review your profile and the current API connection.</p></div></section><section className="settings-grid"><article className="panel"><div className="panel__header"><div><h2>Your profile</h2><p>Your identity comes directly from the authenticated API session.</p></div></div><div className="profile-settings"><span className="profile-settings__avatar">{user.full_name.slice(0, 1).toUpperCase()}</span><div><strong>{user.full_name}</strong><span>{user.email}</span><em>{titleCase(user.role)}</em></div></div><dl className="settings-list"><div><dt><UserRound size={16} />User ID</dt><dd>#{user.id}</dd></div><div><dt><KeyRound size={16} />Authentication</dt><dd>JWT access + refresh session</dd></div></dl></article><article className="panel"><div className="panel__header"><div><h2>System status</h2><p>Live information from the backend services.</p></div></div><dl className="settings-list"><div><dt><ServerCog size={16} />FastAPI health</dt><dd className={healthy === null ? "" : healthy ? "health health--good" : "health health--bad"}>{healthy === null ? "Checking…" : healthy ? <><CheckCircle2 size={15} />Healthy</> : "Unavailable"}</dd></div><div><dt><Database size={16} />Database</dt><dd>{healthy ? "Connected" : "Checked through /health"}</dd></div><div><dt><Radio size={16} />Realtime events</dt><dd>WebSocket notifications enabled</dd></div></dl><button className="button button--secondary" onClick={() => void checkHealth()}>Run health check</button></article>{user.role.toLowerCase() === "admin" && <article className="panel"><div className="panel__header"><div><h2>Role management</h2><p>Assign an application role by User ID. The API enforces Admin access.</p></div><ShieldCheck size={19} className="muted-icon" /></div><form className="add-member-form" onSubmit={changeRole}><label><span>User ID</span><input required min="1" name="user_id" type="number" placeholder="e.g. 12" /></label><label><span>Application role</span><select name="new_role" defaultValue="developer"><option value="developer">Developer</option><option value="manager">Manager</option><option value="admin">Admin</option></select></label><button className="button button--primary">Update role</button></form></article>}</section></>;
}
