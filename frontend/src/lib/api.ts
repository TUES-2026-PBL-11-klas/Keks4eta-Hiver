import type { TokenResponse } from "@/types";

// Vite proxies /api -> backend; VITE_API_BASE can override for prod builds.
const BASE_URL = (import.meta.env.VITE_API_BASE as string | undefined) ?? "/api/v1";

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

// ── Token storage ───────────────────────────────────────────────────────────
export const tokens = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set({ access_token, refresh_token }: TokenResponse) {
    localStorage.setItem(ACCESS_KEY, access_token);
    localStorage.setItem(REFRESH_KEY, refresh_token);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export class ApiRequestError extends Error {
  status: number;
  code?: string;
  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
  }
}

// A single in-flight refresh shared by concurrent 401s.
let refreshing: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const refresh_token = tokens.refresh;
  if (!refresh_token) return false;
  if (!refreshing) {
    refreshing = fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token }),
    })
      .then(async (res) => {
        if (!res.ok) return false;
        tokens.set((await res.json()) as TokenResponse);
        return true;
      })
      .catch(() => false)
      .finally(() => {
        refreshing = null;
      });
  }
  return refreshing;
}

interface RequestOptions extends RequestInit {
  /** internal: prevents refresh recursion */
  _retried?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { _retried, ...init } = options;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  const access = tokens.access;
  if (access) headers["Authorization"] = `Bearer ${access}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers });

  // Try a transparent refresh-and-retry exactly once on 401.
  if (res.status === 401 && !_retried && tokens.refresh) {
    if (await tryRefresh()) {
      return request<T>(path, { ...options, _retried: true });
    }
    tokens.clear();
  }

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiRequestError(
      body?.message ?? body?.detail ?? res.statusText,
      res.status,
      body?.code,
    );
  }

  // 204 / empty bodies
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

// Multipart upload — must NOT set Content-Type (browser adds the boundary).
async function upload<T>(
  path: string,
  formData: FormData,
  options: RequestOptions = {},
): Promise<T> {
  const { _retried } = options;
  const headers: Record<string, string> = {};
  const access = tokens.access;
  if (access) headers["Authorization"] = `Bearer ${access}`;

  const res = await fetch(`${BASE_URL}${path}`, { method: "POST", body: formData, headers });

  if (res.status === 401 && !_retried && tokens.refresh) {
    if (await tryRefresh()) return upload<T>(path, formData, { ...options, _retried: true });
    tokens.clear();
  }

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiRequestError(
      body?.message ?? body?.detail ?? res.statusText,
      res.status,
      body?.code,
    );
  }
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body == null ? undefined : JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body == null ? undefined : JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  upload: <T>(path: string, formData: FormData) => upload<T>(path, formData),
};

/** Absolute URL for browser navigations (OAuth redirects bypass fetch/proxy). */
export function apiUrl(path: string): string {
  return `${BASE_URL}${path}`;
}

/** ws:// (or wss://) URL for a backend path, honouring VITE_API_BASE. */
export function wsUrl(path: string): string {
  if (BASE_URL.startsWith("http")) {
    return `${BASE_URL.replace(/^http/, "ws")}${path}`;
  }
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}${BASE_URL}${path}`;
}
