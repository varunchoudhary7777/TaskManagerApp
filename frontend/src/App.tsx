import { Navigate, Route, Routes } from "react-router-dom";
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

export function App() {
  return <Routes>
    <Route path="/login" element={<PublicOnly><LoginPage /></PublicOnly>} />
    <Route element={<ProtectedRoutes />}>
      <Route index element={<DashboardPage />} />
      <Route path="projects" element={<ProjectsPage />} />
      <Route path="tasks" element={<TasksPage />} />
      <Route path="teams" element={<TeamsPage />} />
      <Route path="audit-log" element={<AuditLogPage />} />
      <Route path="settings" element={<SettingsPage />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>;
}
