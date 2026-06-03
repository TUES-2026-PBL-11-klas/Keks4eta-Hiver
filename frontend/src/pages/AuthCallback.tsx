import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";
import { Spinner } from "@/components/ui";
import logo from "@/assets/logo.svg";

/**
 * Landing route for the OAuth round-trip. The backend redirects here with
 * tokens in the URL fragment: /auth/callback#access_token=...&refresh_token=...
 */
export default function AuthCallback() {
  const navigate = useNavigate();
  const { setSession } = useAuth();
  const [error, setError] = useState(false);
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    const access_token = hash.get("access_token");
    const refresh_token = hash.get("refresh_token");

    if (!access_token || !refresh_token) {
      setError(true);
      const t = setTimeout(() => navigate(ROUTES.LOGIN, { replace: true }), 1600);
      return () => clearTimeout(t);
    }

    // Strip tokens from the address bar immediately.
    window.history.replaceState(null, "", window.location.pathname);

    setSession({ access_token, refresh_token, token_type: "bearer" })
      .then(() => navigate(ROUTES.DASHBOARD, { replace: true }))
      .catch(() => {
        setError(true);
        setTimeout(() => navigate(ROUTES.LOGIN, { replace: true }), 1600);
      });
  }, [navigate, setSession]);

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", gap: 18 }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
        <img src={logo} alt="Hiver" width={64} height={64} />
        {error ? (
          <p className="muted">Couldn’t complete sign-in. Redirecting…</p>
        ) : (
          <>
            <Spinner />
            <p className="muted">Signing you in…</p>
          </>
        )}
      </div>
    </div>
  );
}
