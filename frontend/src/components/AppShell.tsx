import { type ReactNode, type ReactElement } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ROUTES } from "@/constants/routes";
import { useAuth } from "@/context/AuthContext";
import { Avatar, Button } from "@/components/ui";
import NotificationBell from "@/components/NotificationBell";
import {
  HomeIcon,
  SearchIcon,
  UserIcon,
  PlusIcon,
  PinIcon,
  GridIcon,
  HeartIcon,
  ChatIcon,
} from "@/components/icons";
import logo from "@/assets/logo.svg";
import s from "./AppShell.module.css";

type Props = { children: ReactNode };

const cx = (...c: (string | false | undefined)[]) => c.filter(Boolean).join(" ");

interface NavItem {
  to: string;
  label: string;
  Icon: (p: { size?: number }) => ReactElement;
}

export default function AppShell({ children }: Props) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  const isAuthPage =
    pathname === ROUTES.LOGIN ||
    pathname === ROUTES.REGISTER ||
    pathname === ROUTES.AUTH_CALLBACK;

  // Auth pages render edge-to-edge with no chrome.
  if (isAuthPage) return <>{children}</>;

  const isActive = (to: string) =>
    to === ROUTES.HOME ? pathname === to : pathname.startsWith(to);

  // Role-aware primary navigation.
  const nav: NavItem[] = [
    { to: ROUTES.HOME, label: "Home", Icon: HomeIcon },
    { to: ROUTES.TASKS, label: "Browse", Icon: SearchIcon },
    { to: ROUTES.HIVERS, label: "Hivers", Icon: PinIcon },
  ];
  if (isAuthenticated) {
    nav.push({ to: ROUTES.DASHBOARD, label: "Dashboard", Icon: GridIcon });
    nav.push({ to: ROUTES.INBOX, label: "Inbox", Icon: ChatIcon });
    nav.push({ to: ROUTES.FAVORITES, label: "Saved", Icon: HeartIcon });
  }

  // Unified accounts can both post and work, so the primary CTA is always
  // "Post" once signed in ("Find work" lives in the Browse nav item).
  const cta = isAuthenticated
    ? { to: ROUTES.POST_TASK, label: "Post" }
    : { to: ROUTES.REGISTER, label: "Join" };

  const profileTo = isAuthenticated ? ROUTES.PROFILE : ROUTES.LOGIN;

  return (
    <div className={s.shell}>
      {/* ── Desktop sidebar ───────────────────────────────────────── */}
      <aside className={s.sidebar}>
        <Link to={ROUTES.HOME} className={s.sideBrand}>
          <img src={logo} alt="" width={32} height={32} />
          <span className={s.brandWord}>Hiver</span>
        </Link>

        <nav className={s.sideNav} aria-label="Primary">
          {nav.map(({ to, label, Icon }) => (
            <Link key={to} to={to} className={cx(s.sideLink, isActive(to) && s.active)}>
              <Icon size={21} />
              <span>{label}</span>
            </Link>
          ))}
        </nav>

        <div className={s.sideCta}>
          <Button block onClick={() => navigate(cta.to)}>
            {cta.label === "Post" && <PlusIcon size={18} />}
            {cta.label}
          </Button>
        </div>

        <div className={s.sideFoot}>
          <Link to={profileTo} className={s.userChip}>
            <Avatar name={user?.full_name ?? "Guest"} src={user?.avatar_url} size={40} />
            <span className={s.userMeta}>
              <span className={s.userName}>{user?.full_name ?? "Sign in"}</span>
              <span className={s.userRole}>{user ? "Member" : "guest"}</span>
            </span>
          </Link>
        </div>
      </aside>

      {/* ── Main column ───────────────────────────────────────────── */}
      <div className={s.main}>
        <header className={s.topbar}>
          <Link to={ROUTES.HOME} className={s.topBrand}>
            <img src={logo} alt="" width={28} height={28} />
            <span className={s.topBrandWord}>Hiver</span>
          </Link>

          <nav className={s.topNav} aria-label="Primary">
            {nav.map(({ to, label }) => (
              <Link key={to} to={to} className={cx(s.topNavLink, isActive(to) && s.active)}>
                {label}
              </Link>
            ))}
          </nav>

          <span className={s.locChip}>
            <span className={s.locDot} />
            Sofia
          </span>

          <span className={s.spacer} />

          <div className={s.topActions}>
            {isAuthenticated ? (
              <>
                <NotificationBell />
                <Link to={ROUTES.PROFILE} className={cx(s.iconBtn, s.avatarBtn)} aria-label="Profile">
                  <Avatar name={user?.full_name ?? "U"} src={user?.avatar_url} size={42} />
                </Link>
              </>
            ) : (
              <>
                <Link to={ROUTES.LOGIN} className={s.iconBtn} aria-label="Sign in">
                  <UserIcon size={20} />
                </Link>
                <Button size="sm" onClick={() => navigate(ROUTES.REGISTER)}>
                  Join
                </Button>
              </>
            )}
          </div>
        </header>

        <main className={s.viewport}>{children}</main>
      </div>

      {/* ── Phone bottom tab bar ──────────────────────────────────── */}
      <nav className={s.tabbar} aria-label="Primary">
        <Link to={ROUTES.HOME} className={cx(s.tab, isActive(ROUTES.HOME) && s.active)}>
          <HomeIcon size={22} />
          <span>Home</span>
        </Link>
        <Link to={ROUTES.TASKS} className={cx(s.tab, isActive(ROUTES.TASKS) && s.active)}>
          <SearchIcon size={22} />
          <span>Browse</span>
        </Link>

        <Link to={cta.to} className={s.post} aria-label={cta.label}>
          <span className={s.postHex}>
            <PlusIcon size={22} />
          </span>
          <span className={s.postLabel}>{cta.label}</span>
        </Link>

        <Link to={ROUTES.HIVERS} className={cx(s.tab, isActive(ROUTES.HIVERS) && s.active)}>
          <PinIcon size={22} />
          <span>Hivers</span>
        </Link>
        <Link to={profileTo} className={cx(s.tab, isActive(profileTo) && s.active)}>
          <UserIcon size={22} />
          <span>{isAuthenticated ? "Profile" : "Sign in"}</span>
        </Link>
      </nav>
    </div>
  );
}
