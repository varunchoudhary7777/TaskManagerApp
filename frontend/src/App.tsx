import { Link, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { LoadingState } from "./components/PageState";
import { useAuth } from "./contexts/AuthContext";
import { AuditLogPage } from "./pages/AuditLogPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TasksPage } from "./pages/TasksPage";
import { TeamsPage } from "./pages/TeamsPage";

function ProtectedRoutes() {
  const { user, loading } = useAuth();
  if (loading) return <LoadingState label="Restoring your workspace…" />;
  if (!user) return <Navigate to="/login" replace />;
  return <AppShell />;
}

function PublicOnly({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingState label="Loading…" />;
  return user ? <Navigate to="/" replace /> : children;
}

function AdminOnlyRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingState label="Checking access…" />;

  if (user?.role.toLowerCase() !== "admin") {
    return <section className="page-heading">
      <div>
        <p className="eyebrow">Restricted area</p>
        <h1>Audit log access is limited</h1>
        <p>Your current role does not have permission to view workspace audit events.</p>
      </div>
      <Link className="button button--secondary" to="/">Return to overview</Link>
    </section>;
  }

  return children;
}

export function App() {
  return <Routes>
    <Route path="/login" element={<PublicOnly><LoginPage /></PublicOnly>} />
    <Route element={<ProtectedRoutes />}>
      <Route index element={<DashboardPage />} />
      <Route path="projects" element={<ProjectsPage />} />
      <Route path="tasks" element={<TasksPage />} />
      <Route path="teams" element={<TeamsPage />} />
      <Route path="audit-log" element={<AdminOnlyRoute><AuditLogPage /></AdminOnlyRoute>} />
      <Route path="settings" element={<SettingsPage />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>;
}
