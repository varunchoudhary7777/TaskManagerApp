import { CalendarDays, Check, ChevronDown, CirclePlus, Clock3, Download, FileUp, FolderKanban, MoreHorizontal, Paperclip, Pencil, Plus, Search, Send, Trash2, UserPlus, X } from "lucide-react";
import { ChangeEvent, FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Modal } from "../components/Modal";
import { EmptyState, ErrorState, LoadingState } from "../components/PageState";
import { StatusBadge } from "../components/StatusBadge";
import { download, request } from "../lib/api";
import { fileSize, formatDate, formatRelativeTime, titleCase } from "../lib/format";
import type { Attachment, Comment, Project, Task, TaskStatus } from "../types/api";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";

type TaskEditor = { mode: "create" } | { mode: "edit"; task: Task };
const columns: Array<{ key: "TODO" | "IN_PROGRESS" | "COMPLETED"; title: string; helper: string }> = [
  { key: "TODO", title: "To do", helper: "Ready when you are" },
  { key: "IN_PROGRESS", title: "In progress", helper: "Active work" },
  { key: "COMPLETED", title: "Completed", helper: "Done and delivered" },
];

export function TasksPage() {
  const { user } = useAuth();
  const { success, error: notifyError } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [editor, setEditor] = useState<TaskEditor | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [taskList, projectList] = await Promise.all([
        request<Task[]>("/tasks/"),
        request<Project[]>("/projects/", { query: { limit: 100, sort_by: "name", sort_order: "asc" } }),
      ]);
      setTasks(taskList); setProjects(projectList); setError(null);
      const taskId = Number(searchParams.get("task"));
      if (taskId) setSelectedTask(taskList.find((task) => task.id === taskId) ?? null);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to load tasks."); }
    finally { setLoading(false); }
  }, [search, searchParams]);
  useEffect(() => { const timeout = window.setTimeout(() => void load(), 250); return () => window.clearTimeout(timeout); }, [load]);

  const projectName = useMemo(() => new Map(projects.map((project) => [project.id, project.name])), [projects]);
  const statusOf = (task: Task) => (task.status?.toUpperCase() ?? "TODO") as "TODO" | "IN_PROGRESS" | "COMPLETED";
  const openTask = (task: Task) => { setSelectedTask(task); setSearchParams({ task: String(task.id) }, { replace: true }); };
  const closeTask = () => { setSelectedTask(null); setSearchParams({}, { replace: true }); };

  const changeStatus = async (task: Task, taskStatus: TaskStatus) => {
    try {
      const updated = await request<Task>(`/tasks/task_status/${task.id}`, { method: "PUT", body: JSON.stringify({ task_status: taskStatus }) });
      setTasks((items) => items.map((item) => item.id === task.id ? { ...item, ...updated, status: taskStatus } : item));
      setSelectedTask((current) => current?.id === task.id ? { ...current, ...updated, status: taskStatus } : current);
      success(`Task moved to ${titleCase(taskStatus)}.`);
    } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to update task status."); }
  };

  const saveTask = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const rawDueDate = String(form.get("due_date") ?? "");
    const base = { title: String(form.get("title")), description: String(form.get("description")), priority: String(form.get("priority")) || undefined, due_date: rawDueDate ? new Date(rawDueDate).toISOString() : undefined };
    try {
      if (editor?.mode === "create") {
        const assigneeValue = String(form.get("assignee_id") ?? "");
        await request<Task>("/tasks/", { method: "POST", body: JSON.stringify({ ...base, project_id: Number(form.get("project_id")), assignee_id: assigneeValue ? Number(assigneeValue) : null }) });
        success("Task created.");
      } else if (editor) {
        await request<Task>(`/tasks/update/${editor.task.project_id}/${editor.task.id}`, { method: "PUT", body: JSON.stringify(base) });
        success("Task updated.");
      }
      setEditor(null); await load();
    } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to save task."); }
  };

  const filteredTasks = tasks.filter((task) => task.title.toLowerCase().includes(search.toLowerCase()) || task.description.toLowerCase().includes(search.toLowerCase()));

  return <>
    <section className="page-heading"><div><p className="eyebrow">Execution</p><h1>My tasks</h1><p>Keep ownership, conversations, attachments, and delivery status in one focused view.</p></div><button className="button button--primary" onClick={() => setEditor({ mode: "create" })}><Plus size={18} />New task</button></section>
    <section className="toolbar"><label className="search-field"><Search size={18} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search tasks" /></label><span className="toolbar__spacer" /><span className="result-count">{filteredTasks.length} tasks</span></section>
    {loading ? <LoadingState /> : error ? <ErrorState error={error} retry={() => void load()} /> : filteredTasks.length ? <section className="kanban-board">{columns.map((column) => { const items = filteredTasks.filter((task) => statusOf(task) === column.key); return <div className="kanban-column" key={column.key}><header><div><h2>{column.title}<span>{items.length}</span></h2><p>{column.helper}</p></div><button className="icon-button" onClick={() => setEditor({ mode: "create" })} aria-label={`Add ${column.title} task`}><Plus size={17} /></button></header><div className="kanban-column__body">{items.map((task) => <TaskCard key={task.id} task={task} projectName={projectName.get(task.project_id)} currentUserId={user?.id} onOpen={() => openTask(task)} onStatusChange={changeStatus} />)}{!items.length && <div className="kanban-empty">No tasks here</div>}</div></div>; })}</section> : <EmptyState title="No tasks found" detail="Create a task to turn a plan into a clear next action." action={<button className="button button--primary" onClick={() => setEditor({ mode: "create" })}><CirclePlus size={17} />Create task</button>} />}
    {editor && <TaskEditorModal editor={editor} projects={projects} onClose={() => setEditor(null)} onSubmit={saveTask} />}
    {selectedTask && <TaskDetailModal task={selectedTask} projects={projects} onClose={closeTask} onUpdate={(task) => { setTasks((items) => items.map((item) => item.id === task.id ? task : item)); setSelectedTask(task); }} onRefresh={load} />}
  </>;
}

function TaskCard({ task, projectName, currentUserId, onOpen, onStatusChange }: { task: Task; projectName?: string; currentUserId?: number; onOpen: () => void; onStatusChange: (task: Task, status: TaskStatus) => void }) {
  const [menu, setMenu] = useState(false);
  return <article className="task-card" onClick={onOpen}><div className="task-card__header"><span className={`priority-dot priority-dot--${(task.priority ?? "low").toLowerCase()}`} /><div className="action-menu"><button className="icon-button" onClick={(event) => { event.stopPropagation(); setMenu((open) => !open); }} aria-label="Task actions"><MoreHorizontal size={18} /></button>{menu && <div className="action-menu__panel" onClick={(event) => event.stopPropagation()}>{(["TODO", "IN_PROGRESS", "COMPLETED"] as const).map((status) => <button key={status} onClick={() => { onStatusChange(task, status); setMenu(false); }}><Check size={15} />Move to {titleCase(status)}</button>)}</div>}</div></div><h3>{task.title}</h3><p>{task.description}</p><footer><span className="task-card__project"><FolderKanban size={13} />{projectName ?? `Project #${task.project_id}`}</span><span className="task-card__meta"><CalendarDays size={13} />{task.due_date ? formatDate(task.due_date) : "No date"}</span></footer><div className="task-card__assignee">{task.assignee_id === currentUserId ? <span className="assignee-avatar">You</span> : task.assignee_id ? <span className="assignee-avatar">#{task.assignee_id}</span> : <span className="unassigned">Unassigned</span>}</div></article>;
}

function TaskEditorModal({ editor, projects, onClose, onSubmit }: { editor: TaskEditor; projects: Project[]; onClose: () => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) {
  const task = editor.mode === "edit" ? editor.task : undefined;
  return <Modal title={task ? "Edit task" : "Create task"} onClose={onClose}><form className="form-stack" onSubmit={onSubmit}><label><span>Task title</span><input name="title" minLength={3} maxLength={200} required defaultValue={task?.title} placeholder="Prepare stakeholder review" /></label><label><span>Description</span><textarea name="description" minLength={3} maxLength={300} required defaultValue={task?.description} rows={4} placeholder="Describe the outcome and important context." /></label>{!task && <label><span>Project</span><select name="project_id" defaultValue="" required><option value="" disabled>Select project</option>{projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</select></label>}<div className="form-row"><label><span>Priority</span><select name="priority" defaultValue={task?.priority?.toUpperCase() ?? "LOW"}><option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="URGENT">Urgent</option></select></label><label><span>Due date</span><input name="due_date" type="datetime-local" defaultValue={task?.due_date ? dateTimeInputValue(task.due_date) : ""} /></label></div>{!task && <label><span>Assignee ID <em>(optional)</em></span><input name="assignee_id" type="number" min="1" placeholder="e.g. 12" /></label>}<div className="modal__actions"><button type="button" className="button button--secondary" onClick={onClose}>Cancel</button><button className="button button--primary">{task ? "Save changes" : "Create task"}</button></div></form></Modal>;
}

function TaskDetailModal({ task, projects, onClose, onUpdate, onRefresh }: { task: Task; projects: Project[]; onClose: () => void; onUpdate: (task: Task) => void; onRefresh: () => Promise<void> }) {
  const { user } = useAuth();
  const { success, error: notifyError } = useToast();
  const [comments, setComments] = useState<Comment[]>([]);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [loading, setLoading] = useState(true);
  const [assignOpen, setAssignOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [working, setWorking] = useState(false);
  const project = projects.find((item) => item.id === task.project_id);
  const status = task.status?.toUpperCase() ?? "TODO";
  const loadDetail = useCallback(async () => { setLoading(true); try { const [commentList, attachmentList] = await Promise.all([request<Comment[]>(`/comments/task/${task.id}`), request<Attachment[]>(`/attachments/task/${task.id}`)]); setComments(commentList); setAttachments(attachmentList); } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to load task details."); } finally { setLoading(false); } }, [notifyError, task.id]);
  useEffect(() => { void loadDetail(); }, [loadDetail]);

  const addComment = async (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); const form = new FormData(event.currentTarget); const content = String(form.get("content") ?? ""); if (!content.trim()) return; try { const comment = await request<Comment>("/comments/", { method: "POST", body: JSON.stringify({ task_id: task.id, content }) }); setComments((items) => [...items, comment]); event.currentTarget.reset(); success("Comment added."); } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to add comment."); } };
  const uploadFile = async (event: ChangeEvent<HTMLInputElement>) => { const file = event.target.files?.[0]; if (!file) return; const form = new FormData(); form.append("file", file); setUploading(true); try { const attachment = await request<Attachment>(`/attachments/task/${task.id}`, { method: "POST", body: form }); setAttachments((items) => [...items, attachment]); success("Attachment uploaded."); } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to upload attachment."); } finally { setUploading(false); event.target.value = ""; } };
  const assignTask = async (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); const id = Number(new FormData(event.currentTarget).get("assignee_id")); setWorking(true); try { const updated = await request<Task>(`/tasks/assign/${task.id}/${id}`, { method: "PUT" }); onUpdate({ ...task, ...updated, assignee_id: id }); setAssignOpen(false); success("Task assigned and notification queued."); await onRefresh(); } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to assign task."); } finally { setWorking(false); } };
  const setStatus = async (taskStatus: TaskStatus) => { setWorking(true); try { const updated = await request<Task>(`/tasks/task_status/${task.id}`, { method: "PUT", body: JSON.stringify({ task_status: taskStatus }) }); onUpdate({ ...task, ...updated, status: taskStatus }); success(`Task moved to ${titleCase(taskStatus)}.`); await onRefresh(); } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to update task status."); } finally { setWorking(false); } };
  const deleteAttachment = async (attachment: Attachment) => { try { await request(`/attachments/${attachment.id}`, { method: "DELETE" }); setAttachments((items) => items.filter((item) => item.id !== attachment.id)); success("Attachment deleted."); } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to delete attachment."); } };
  const deleteTask = async () => { setWorking(true); try { await request(`/tasks/${task.project_id}/${task.id}`, { method: "DELETE" }); success("Task deleted."); await onRefresh(); onClose(); } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to delete task."); } finally { setWorking(false); } };

  return <Modal title="Task details" onClose={onClose} wide><div className="task-detail"><section className="task-detail__main"><div className="task-detail__topline"><StatusBadge value={status} /><div className="task-detail__actions"><button className="button button--secondary" onClick={() => setEditing(true)}><Pencil size={16} />Edit</button><button className="icon-button danger-button" onClick={() => void deleteTask()} disabled={working} aria-label="Delete task"><Trash2 size={18} /></button></div></div><h2>{task.title}</h2><p className="task-detail__description">{task.description}</p><div className="detail-meta"><span><FolderKanban size={16} />{project?.name ?? `Project #${task.project_id}`}</span><span><CalendarDays size={16} />{task.due_date ? `Due ${formatDate(task.due_date)}` : "No due date"}</span><span><Clock3 size={16} />Created {formatDate(task.created_at)}</span></div><section className="detail-section"><header><h3>Progress</h3><select value={status} onChange={(event) => void setStatus(event.target.value)} disabled={working}><option value="TODO">To do</option><option value="IN_PROGRESS">In progress</option><option value="COMPLETED">Completed</option></select></header><div className="status-stepper">{["TODO", "IN_PROGRESS", "COMPLETED"].map((item, index) => <button key={item} className={item === status ? "status-stepper__item status-stepper__item--active" : "status-stepper__item"} onClick={() => void setStatus(item)} disabled={working}><i>{index + 1}</i>{titleCase(item)}</button>)}</div></section><section className="detail-section"><header><h3>Attachments</h3><label className="button button--secondary file-button"><FileUp size={16} />{uploading ? "Uploading…" : "Upload file"}<input type="file" onChange={uploadFile} disabled={uploading} /></label></header>{loading ? <p className="muted">Loading files…</p> : attachments.length ? <ul className="attachment-list">{attachments.map((attachment) => <li key={attachment.id}><Paperclip size={16} /><span><strong>{attachment.original_filename}</strong><small>{fileSize(attachment.size_bytes)} · {formatDate(attachment.created_at)}</small></span><button className="icon-button" onClick={() => void download(`/attachments/${attachment.id}/download`, attachment.original_filename)} aria-label={`Download ${attachment.original_filename}`}><Download size={16} /></button><button className="icon-button danger-button" onClick={() => void deleteAttachment(attachment)} aria-label={`Delete ${attachment.original_filename}`}><X size={16} /></button></li>)}</ul> : <p className="muted">No files attached yet.</p>}</section><section className="detail-section"><header><h3>Conversation</h3><span>{comments.length} comment{comments.length === 1 ? "" : "s"}</span></header>{loading ? <p className="muted">Loading conversation…</p> : <div className="comment-list">{comments.map((comment) => <article key={comment.id}><span className="comment-avatar">#{comment.author_id}</span><div><header><strong>{comment.author_id === user?.id ? "You" : `User #${comment.author_id}`}</strong><time>{formatRelativeTime(comment.created_at)}</time></header><p>{comment.content}</p></div></article>)}</div>}<form className="comment-form" onSubmit={addComment}><textarea required name="content" placeholder="Write a comment…" rows={2} /><button className="button button--primary" aria-label="Post comment"><Send size={17} /></button></form></section></section><aside className="task-detail__side"><section><span className="eyebrow">Assignee</span><div className="assignee-panel"><span className="avatar">{task.assignee_id ? `#${task.assignee_id}` : "?"}</span><div><strong>{task.assignee_id === user?.id ? "You" : task.assignee_id ? `User #${task.assignee_id}` : "Unassigned"}</strong><small>{task.assignee_id ? "Task owner" : "Needs an owner"}</small></div></div><button className="button button--secondary button--full" onClick={() => setAssignOpen((open) => !open)}><UserPlus size={16} />Assign task</button>{assignOpen && <form onSubmit={assignTask} className="assign-form"><label><span>User ID</span><input name="assignee_id" type="number" min="1" required placeholder="e.g. 12" /></label><button className="button button--primary button--full" disabled={working}>Assign</button></form>}</section><section><span className="eyebrow">Priority</span><strong className={`priority-value priority-value--${(task.priority ?? "low").toLowerCase()}`}>{titleCase(task.priority ?? "Low")}</strong></section></aside></div>{editing && <TaskEditorModal editor={{ mode: "edit", task }} projects={projects} onClose={() => setEditing(false)} onSubmit={async (event) => { event.preventDefault(); const form = new FormData(event.currentTarget); try { const rawDueDate = String(form.get("due_date") ?? ""); const updated = await request<Task>(`/tasks/update/${task.project_id}/${task.id}`, { method: "PUT", body: JSON.stringify({ title: String(form.get("title")), description: String(form.get("description")), priority: String(form.get("priority")), due_date: rawDueDate ? new Date(rawDueDate).toISOString() : null }) }); onUpdate({ ...task, ...updated }); success("Task updated."); setEditing(false); await onRefresh(); } catch (caught) { notifyError(caught instanceof Error ? caught.message : "Unable to update task."); } }} />}</Modal>;
}

function dateTimeInputValue(value: string) { return new Date(value).toISOString().slice(0, 16); }
