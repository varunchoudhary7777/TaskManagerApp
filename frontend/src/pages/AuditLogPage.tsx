import { FileClock, Filter, Search } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "../components/PageState";
import { request } from "../lib/api";
import { formatDate, titleCase } from "../lib/format";
import type { AuditLog } from "../types/api";

export function AuditLogPage() {
  const [items, setItems] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [action, setAction] = useState("");
  const [resourceType, setResourceType] = useState("");
  const load = useCallback(async () => { setLoading(true); try { setItems(await request<AuditLog[]>("/audit-logs/", { query: { limit: 100, action: action || undefined, resource_type: resourceType || undefined } })); setError(null); } catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to load audit logs."); } finally { setLoading(false); } }, [action, resourceType]);
  useEffect(() => { void load(); }, [load]);
  return <><section className="page-heading"><div><p className="eyebrow">Admin control</p><h1>Audit log</h1><p>Review the recorded changes that matter across your workspace.</p></div></section><section className="toolbar"><span className="toolbar-filter"><Filter size={17} />Filters</span><input value={action} onChange={(event) => setAction(event.target.value)} placeholder="Action, e.g. TASK_CREATED" /><input value={resourceType} onChange={(event) => setResourceType(event.target.value)} placeholder="Resource, e.g. task" /><span className="toolbar__spacer" /><button className="button button--secondary" onClick={() => void load()}><Search size={16} />Apply</button></section>{loading ? <LoadingState /> : error ? <ErrorState error={error} retry={() => void load()} /> : items.length ? <section className="panel audit-panel"><div className="audit-table-wrap"><table className="audit-table"><thead><tr><th>Event</th><th>Actor</th><th>Resource</th><th>Details</th><th>When</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td><span className="audit-event"><FileClock size={16} />{titleCase(item.action)}</span></td><td>{item.actor_id ? `User #${item.actor_id}` : "System"}</td><td>{titleCase(item.resource_type)} #{item.resource_id}</td><td><code>{item.details ? JSON.stringify(item.details) : "—"}</code></td><td>{formatDate(item.created_at, { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}</td></tr>)}</tbody></table></div></section> : <EmptyState title="No audit events found" detail="Recorded changes will appear here." />}</>;
}
