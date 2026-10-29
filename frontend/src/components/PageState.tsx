import { AlertCircle, Inbox, LoaderCircle } from "lucide-react";

export function LoadingState({ label = "Loading workspace…" }: { label?: string }) {
  return <div className="page-state"><LoaderCircle className="spin" size={28} /><p>{label}</p></div>;
}

export function EmptyState({ title, detail, action }: { title: string; detail: string; action?: React.ReactNode }) {
  return <div className="empty-state"><Inbox size={30} /><h3>{title}</h3><p>{detail}</p>{action}</div>;
}

export function ErrorState({ error, retry }: { error: string; retry?: () => void }) {
  return <div className="error-state"><AlertCircle size={20} /><div><strong>Could not load this view</strong><p>{error}</p></div>{retry && <button className="button button--secondary" onClick={retry}>Try again</button>}</div>;
}
