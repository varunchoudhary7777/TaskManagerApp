export type Role = "ADMIN" | "MANAGER" | "DEVELOPER" | string;
export type ProjectStatus = "planning" | "active" | "completed" | "archived" | string;
export type TaskStatus = "TODO" | "IN_PROGRESS" | "COMPLETED" | "todo" | "in_progress" | "completed" | string;

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  created_at: string;
}

export interface Team {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

export interface Project {
  id: number;
  name: string;
  description: string;
  status: ProjectStatus;
  team_id: number;
  created_by_id: number;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: number;
  title: string;
  description: string;
  project_id: number;
  assignee_id: number | null;
  created_by_id: number;
  created_at: string;
  updated_at: string;
  // Added by the recommended TaskResponse schema upgrade. The UI safely falls back
  // when it is connected to the current API schema.
  status?: TaskStatus;
  priority?: "LOW" | "MEDIUM" | "HIGH" | "low" | "medium" | "high" | string | null;
  due_date?: string | null;
}

export interface Comment {
  id: number;
  content: string;
  task_id: number;
  author_id: number;
  created_at: string;
  updated_at: string;
}

export interface Attachment {
  id: number;
  task_id: number;
  uploaded_by_id: number | null;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export interface Notification {
  id: number;
  user_id: number;
  actor_id: number | null;
  notification_type: string;
  title: string;
  message: string;
  resource_id: number;
  details: Record<string, unknown> | null;
  read_at: string | null;
  created_at: string;
}

export interface DashboardSummary {
  scope: string;
  scope_label: string;
  scope_description: string;
  visible_team_count: number;
  active_projects: number;
  total_tasks: number;
  todo_tasks: number;
  in_progress_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  unassigned_tasks: number;
  generated_at: string;
  recent_projects: Project[];
  upcoming_tasks: Task[];
}

export interface AuditLog {
  id: number;
  actor_id: number | null;
  action: string;
  resource_type: string;
  resource_id: number;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface ApiErrorShape {
  detail?: string;
  errors?: Array<{ field: string; message: string }>;
}
