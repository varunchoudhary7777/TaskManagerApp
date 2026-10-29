import { ArrowRight, Check, Eye, EyeOff, FolderKanban, ShieldCheck, UsersRound } from "lucide-react";
import { FormEvent, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";

export function LoginPage() {
  const { login, register } = useAuth();
  const { error } = useToast();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    const email = String(values.get("email") ?? "");
    const password = String(values.get("password") ?? "");
    const fullName = String(values.get("full_name") ?? "");
    setSubmitting(true);
    try {
      if (mode === "login") await login({ email, password });
      else await register({ email, password, full_name: fullName });
    } catch (caught) {
      error(caught instanceof Error ? caught.message : "Unable to authenticate. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return <main className="auth-layout">
    <section className="auth-marketing">
      <div className="auth-marketing__brand"><span className="brand__mark">T</span> Taskflow</div>
      <div className="auth-marketing__copy"><p className="eyebrow">Clarity for busy teams</p><h1>Turn plans into work that ships.</h1><p>A focused workspace for the projects, people, and decisions that move your team forward.</p></div>
      <div className="auth-feature-list"><div><span><FolderKanban size={19} /></span><p><strong>One calm workspace</strong><small>See projects, tasks, files, and conversations in context.</small></p></div><div><span><UsersRound size={19} /></span><p><strong>Built for accountable teams</strong><small>Permissions and audit history make every change traceable.</small></p></div><div><span><ShieldCheck size={19} /></span><p><strong>Secure by default</strong><small>JWT sessions, refresh rotation, and role-aware access.</small></p></div></div>
    </section>
    <section className="auth-panel">
      <div className="auth-card"><div className="auth-card__heading"><p className="eyebrow">{mode === "login" ? "Welcome back" : "Get started"}</p><h2>{mode === "login" ? "Sign in to Taskflow" : "Create your workspace account"}</h2><p>{mode === "login" ? "Use your work email to continue." : "You will start with Developer access. An Admin can change roles later."}</p></div>
        <form onSubmit={submit} className="form-stack">
          {mode === "register" && <label><span>Full name</span><input required minLength={2} maxLength={100} name="full_name" placeholder="Aarav Sharma" autoComplete="name" /></label>}
          <label><span>Work email</span><input required name="email" type="email" placeholder="you@company.com" autoComplete="email" /></label>
          <label><span>Password</span><div className="password-input"><input required minLength={mode === "register" ? 8 : 1} name="password" type={showPassword ? "text" : "password"} placeholder="••••••••" autoComplete={mode === "login" ? "current-password" : "new-password"} /><button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></label>
          <button className="button button--primary button--full" disabled={submitting}>{submitting ? "Please wait…" : mode === "login" ? <>Sign in <ArrowRight size={18} /></> : <>Create account <ArrowRight size={18} /></>}</button>
        </form>
        <div className="auth-switch"><span>{mode === "login" ? "New to Taskflow?" : "Already have an account?"}</span><button onClick={() => setMode((current) => current === "login" ? "register" : "login")}>{mode === "login" ? "Create an account" : "Sign in instead"}</button></div>
        {mode === "register" && <p className="auth-note"><Check size={15} /> Passwords need at least 8 characters.</p>}
      </div>
    </section>
  </main>;
}
