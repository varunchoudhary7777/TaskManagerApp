import { Bell, ClipboardList, FileClock, FolderKanban, LayoutDashboard, LogOut, Menu, Plus, Settings, ShieldCheck, UsersRound, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { createNotificationSocket, request } from "../lib/api";
import { formatRelativeTime, titleCase } from "../lib/format";
import type { Notification } from "../types/api";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";

const primaryItems = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/projects", label: "Projects", icon: FolderKanban },
  { to: "/tasks", label: "My tasks", icon: ClipboardList },
  { to: "/teams", label: "Teams", icon: UsersRound },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const { error, success } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [notificationOpen, setNotificationOpen] = useState(false);

  const loadNotifications = useCallback(async () => {
    try {
      setNotifications(await request<Notification[]>("/notifications/", { query: { limit: 12, unread_only: false } }));
    } catch {
      // Notifications must never block the rest of the workspace.
    }
  }, []);

  useEffect(() => { void loadNotifications(); }, [loadNotifications, location.pathname]);
  useEffect(() => {
    const socket = createNotificationSocket((message) => {
      const payload = message as { type?: string; title?: string; message?: string };
      if (payload.type === "notification") {
        success(payload.title ? `${payload.title}: ${payload.message ?? ""}` : "You have a new notification.");
        void loadNotifications();
      }
    });
    return () => socket?.close();
  }, [loadNotifications, success]);

  const unreadCount = notifications.filter((item) => !item.read_at).length;
  const markRead = async (notification: Notification) => {
    if (notification.read_at) return;
    try {
      await request(`/notifications/${notification.id}/read`, { method: "PATCH" });
      setNotifications((items) => items.map((item) => item.id === notification.id ? { ...item, read_at: new Date().toISOString() } : item));
    } catch (caught) {
      error(caught instanceof Error ? caught.message : "Unable to update notification.");
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };
  const closeMobile = () => setMobileOpen(false);

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileOpen ? "sidebar--open" : ""}`}>
        <div className="brand"><span className="brand__mark">T</span><span>Taskflow</span><button className="icon-button sidebar__close" onClick={closeMobile}><X size={20} /></button></div>
        <button className="create-button" onClick={() => { navigate("/projects?new=1"); closeMobile(); }}><Plus size={18} /> New project</button>
        <nav aria-label="Main navigation">
          <p className="nav-label">Workspace</p>
          {primaryItems.map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} onClick={closeMobile} className={({ isActive }) => `nav-item ${isActive ? "nav-item--active" : ""}`}><Icon size={18} />{label}</NavLink>)}
          {user?.role.toLowerCase() === "admin" && <><p className="nav-label">Control</p><NavLink to="/audit-log" onClick={closeMobile} className={({ isActive }) => `nav-item ${isActive ? "nav-item--active" : ""}`}><FileClock size={18} />Audit log</NavLink></>}
        </nav>
        <div className="sidebar__bottom"><NavLink to="/settings" onClick={closeMobile} className={({ isActive }) => `nav-item ${isActive ? "nav-item--active" : ""}`}><Settings size={18} />Settings</NavLink><button className="nav-item nav-item--button" onClick={handleLogout}><LogOut size={18} />Sign out</button></div>
      </aside>
      {mobileOpen && <button className="sidebar-scrim" onClick={closeMobile} aria-label="Close navigation" />}
      <main className="main-content">
        <header className="topbar">
          <button className="icon-button menu-button" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={21} /></button>
          <div className="topbar__spacer" />
          <div className="notification-wrap">
            <button className="icon-button notification-button" onClick={() => setNotificationOpen((open) => !open)} aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ""}`}><Bell size={20} />{unreadCount > 0 && <span className="notification-count">{unreadCount > 9 ? "9+" : unreadCount}</span>}</button>
            {notificationOpen && <section className="notification-panel"><header><div><strong>Notifications</strong><span>{unreadCount} unread</span></div><button className="text-button" onClick={() => void loadNotifications()}>Refresh</button></header>{notifications.length ? <ul>{notifications.map((notification) => <li key={notification.id}><button className={!notification.read_at ? "notification-item notification-item--unread" : "notification-item"} onClick={() => void markRead(notification)}><span className="notification-dot" /><span><strong>{notification.title}</strong><small>{notification.message}</small><time>{formatRelativeTime(notification.created_at)}</time></span></button></li>)}</ul> : <p className="notification-empty">You are all caught up.</p>}</section>}
          </div>
          <div className="profile-chip"><span className="avatar">{user?.full_name.slice(0, 1).toUpperCase()}</span><span><strong>{user?.full_name}</strong><small><ShieldCheck size={12} /> {titleCase(user?.role)}</small></span></div>
        </header>
        <div className="page-container"><Outlet /></div>
      </main>
    </div>
  );
}
