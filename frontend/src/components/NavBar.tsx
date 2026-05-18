import { Link, useLocation } from "react-router-dom";
import { ROUTES } from "@/constants/routes";
import styles from "./NavBar.module.css";

export default function NavBar() {
  const { pathname } = useLocation();

  return (
    <nav className={styles.nav}>
      <Link to={ROUTES.HOME} className={styles.brand}>
        Hiver
      </Link>
      <div className={styles.links}>
        <Link to={ROUTES.TASKS} className={pathname === ROUTES.TASKS ? styles.active : ""}>
          Tasks
        </Link>
        <Link to={ROUTES.PROFILE} className={pathname === ROUTES.PROFILE ? styles.active : ""}>
          Profile
        </Link>
        <Link to={ROUTES.LOGIN} className={styles.cta}>
          Sign in
        </Link>
      </div>
    </nav>
  );
}
