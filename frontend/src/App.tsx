import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import AppShell from "@/components/AppShell";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ROUTES } from "@/constants/routes";

import Home from "@/pages/Home";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import AuthCallback from "@/pages/AuthCallback";
import Tasks from "@/pages/Tasks";
import TaskDetail from "@/pages/TaskDetail";
import PostTask from "@/pages/PostTask";
import Dashboard from "@/pages/Dashboard";
import NearbyHivers from "@/pages/NearbyHivers";
import Profile from "@/pages/Profile";
import PublicProfile from "@/pages/PublicProfile";

function Animated({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

export default function App() {
  const location = useLocation();
  return (
    <AppShell>
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path={ROUTES.HOME} element={<Animated><Home /></Animated>} />
          <Route path={ROUTES.LOGIN} element={<Login />} />
          <Route path={ROUTES.REGISTER} element={<Register />} />
          <Route path={ROUTES.AUTH_CALLBACK} element={<AuthCallback />} />

          <Route path={ROUTES.TASKS} element={<Animated><Tasks /></Animated>} />
          <Route path={ROUTES.TASK_DETAIL} element={<Animated><TaskDetail /></Animated>} />
          <Route path={ROUTES.HIVERS} element={<Animated><NearbyHivers /></Animated>} />
          <Route path={ROUTES.HIVER_PROFILE} element={<Animated><PublicProfile kind="hiver" /></Animated>} />
          <Route path={ROUTES.CLIENT_PROFILE} element={<Animated><PublicProfile kind="client" /></Animated>} />

          <Route
            path={ROUTES.POST_TASK}
            element={
              <ProtectedRoute>
                <Animated><PostTask /></Animated>
              </ProtectedRoute>
            }
          />
          <Route
            path={ROUTES.DASHBOARD}
            element={
              <ProtectedRoute>
                <Animated><Dashboard /></Animated>
              </ProtectedRoute>
            }
          />
          <Route
            path={ROUTES.PROFILE}
            element={
              <ProtectedRoute>
                <Animated><Profile /></Animated>
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to={ROUTES.HOME} replace />} />
        </Routes>
      </AnimatePresence>
    </AppShell>
  );
}
