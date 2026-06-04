import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";
import { Spinner } from "@/components/ui";
import type { ReactNode } from "react";

/** Gate a route behind authentication. Unified accounts can do everything, so
 *  there is no per-role gating anymore — only "are you signed in?". */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ display: "grid", placeItems: "center", minHeight: "60vh" }}>
        <Spinner />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace state={{ from: location.pathname }} />;
  }

  return <>{children}</>;
}
