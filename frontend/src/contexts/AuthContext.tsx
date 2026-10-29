import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { clearTokens, getTokens, request, saveTokens } from "../lib/api";
import type { TokenPair, User } from "../types/api";

type LoginInput = { email: string; password: string };
type RegisterInput = LoginInput & { full_name: string };
type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (input: LoginInput) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshProfile = useCallback(async () => {
    const profile = await request<User>("/auth/me");
    setUser(profile);
  }, []);

  useEffect(() => {
    if (!getTokens()) {
      setLoading(false);
      return;
    }
    refreshProfile().catch(() => clearTokens()).finally(() => setLoading(false));
  }, [refreshProfile]);

  const login = useCallback(async (input: LoginInput) => {
    const tokens = await request<TokenPair>("/auth/login", { method: "POST", body: JSON.stringify(input) });
    saveTokens(tokens);
    await refreshProfile();
  }, [refreshProfile]);

  const register = useCallback(async (input: RegisterInput) => {
    await request<User>("/auth/register", { method: "POST", body: JSON.stringify(input) });
    await login({ email: input.email, password: input.password });
  }, [login]);

  const logout = useCallback(async () => {
    const tokens = getTokens();
    try {
      if (tokens?.refresh_token) await request<void>("/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token: tokens.refresh_token }) });
    } finally {
      clearTokens();
      setUser(null);
    }
  }, []);

  const value = useMemo(() => ({ user, loading, login, register, logout, refreshProfile }), [user, loading, login, register, logout, refreshProfile]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
