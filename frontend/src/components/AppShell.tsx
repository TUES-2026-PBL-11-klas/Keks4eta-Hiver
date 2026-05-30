import { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { ROUTES } from "@/constants/routes";
import {
  HomeIcon,
  SearchIcon,
  UserIcon,
  PlusIcon,
} from "@/components/icons";
import logo from "@/assets/logo.svg";
import styles from "./AppShell.module.css";

type Props = { children: ReactNode };

const TABS = [
  { to: ROUTES.HOME, label: "Home", Icon: HomeIcon },
  { to: ROUTES.TASKS, label: "Browse", Icon: SearchIcon },
] as const;

const TABS_RIGHT = [
  { to: ROUTES.PROFILE, label: "Profile", Icon: UserIcon },
] as const;

export default function AppShell({ children }: Props) {
  const { pathname } = useLocation();
  const isAuth = pathname === ROUTES.LOGIN || pathname === ROUTES.REGISTER;
  const showChrome = !isAuth;

  return (
    <div className={styles.field}>
      <div className={styles.device}>
        {showChrome && (
          <header className={styles.topbar}>
            <Link to={ROUTES.HOME} className={styles.brand}>
              <img src={logo} alt="" width={28} height={28} className={styles.brandMark} />
              <span className={styles.brandWord}>Hiver</span>
            </Link>
            <span className={styles.locChip}>
              <span className={styles.locDot} />
              Sofia
            </span>
          </header>
        )}

        <main className={styles.viewport}>{children}</main>

        {showChrome && (
          <nav className={styles.tabbar} aria-label="Primary">
            {TABS.map(({ to, label, Icon }) => (
              <Link
                key={to}
                to={to}
                className={`${styles.tab} ${pathname === to ? styles.tabActive : ""}`}
              >
                <Icon size={22} />
                <span>{label}</span>
              </Link>
            ))}

            <Link to={ROUTES.REGISTER} className={styles.post} aria-label="Post a task">
              <span className={styles.postHex}>
                <PlusIcon size={22} />
              </span>
              <span className={styles.postLabel}>Post</span>
            </Link>

            {TABS_RIGHT.map(({ to, label, Icon }) => (
              <Link
                key={to}
                to={to}
                className={`${styles.tab} ${pathname === to ? styles.tabActive : ""}`}
              >
                <Icon size={22} />
                <span>{label}</span>
              </Link>
            ))}
          </nav>
        )}
      </div>
    </div>
  );
}
