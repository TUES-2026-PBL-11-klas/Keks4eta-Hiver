import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { apiUrl, tokens } from "@/lib/api";
import { authService } from "@/lib/services";
import type { Me, Role, TokenResponse } from "@/types";

interface AuthContextValue {
  user: Me | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (body: {
    full_name: string;
    email: string;
    password: string;
    role: Role;
  }) => Promise<void>;
  loginWithProvider: (provider: "google" | "facebook", role?: Role) => void;
  setSession: (t: TokenResponse) => Promise<void>;
  refresh: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  const hydrate = useCallback(async () => {
    if (!tokens.access) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setUser(await authService.me());
    } catch {
      tokens.clear();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  const login = useCallback(async (email: string, password: string) => {
    tokens.set(await authService.login(email, password));
    setUser(await authService.me());
  }, []);

  const register = useCallback(
    async (body: { full_name: string; email: string; password: string; role: Role }) => {
      tokens.set(await authService.register(body));
      setUser(await authService.me());
    },
    [],
  );

  const setSession = useCallback(async (t: TokenResponse) => {
    tokens.set(t);
    setUser(await authService.me());
  }, []);

  const loginWithProvider = useCallback((provider: "google" | "facebook", role: Role = "client") => {
    // Full-page navigation: the provider redirects the browser back to /auth/callback.
    window.location.href = apiUrl(`/auth/oauth/${provider}/login?role=${role}`);
  }, []);

  const refresh = useCallback(async () => {
    if (tokens.access) setUser(await authService.me());
  }, []);

  const logout = useCallback(() => {
    tokens.clear();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      isAuthenticated: !!user,
      login,
      register,
      loginWithProvider,
      setSession,
      refresh,
      logout,
    }),
    [user, loading, login, register, loginWithProvider, setSession, refresh, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
