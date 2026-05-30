import { useNavigate, Link } from "react-router-dom";
import { useFetch } from "@/hooks/useFetch";
import type { User } from "@/types";
import { ROUTES } from "@/constants/routes";
import { ShieldIcon, SearchIcon, ArrowRightIcon } from "@/components/icons";
import styles from "./Profile.module.css";

const ROLE_COPY: Record<User["role"], { label: string; blurb: string }> = {
  client: { label: "Client", blurb: "You post tasks and hire hivers." },
  hiver: { label: "Hiver", blurb: "You make offers and earn." },
};

export default function Profile() {
  const navigate = useNavigate();
  const { data, loading, error } = useFetch<User>("/users/me");

  function signOut() {
    localStorage.removeItem("access_token");
    navigate(ROUTES.LOGIN);
  }

  if (loading)
    return (
      <div className={styles.page}>
        <div className={`${styles.hexAvatar} ${styles.pulse}`} />
        <p className={styles.state}>Loading your profile…</p>
      </div>
    );

  if (error)
    return (
      <div className={styles.page}>
        <div className={styles.notice}>
          <p className={styles.noticeTitle}>Couldn't load profile</p>
          <p className={styles.noticeBody}>{error}</p>
          <Link to={ROUTES.LOGIN} className={styles.noticeLink}>Sign in again</Link>
        </div>
      </div>
    );

  if (!data)
    return (
      <div className={styles.page}>
        <div className={styles.notice}>
          <p className={styles.noticeTitle}>You're not signed in</p>
          <Link to={ROUTES.LOGIN} className={styles.noticeLink}>Go to sign in</Link>
        </div>
      </div>
    );

  const role = ROLE_COPY[data.role];

  return (
    <div className={styles.page}>
      <section className={styles.header}>
        <div className={styles.hexAvatar}>
          {data.avatar_url ? (
            <img src={data.avatar_url} alt={data.full_name} />
          ) : (
            <span>{data.full_name.charAt(0).toUpperCase()}</span>
          )}
        </div>
        <h1 className={styles.name}>{data.full_name}</h1>
        <p className={styles.email}>{data.email}</p>
        <span className={`${styles.role} ${styles[data.role]}`}>{role.label}</span>
      </section>

      <p className={styles.roleBlurb}>{role.blurb}</p>

      <section className={styles.tiles}>
        <Link to={ROUTES.TASKS} className={styles.tile}>
          <span className={styles.tileIcon}><SearchIcon size={20} /></span>
          <span className={styles.tileText}>
            <strong>Browse tasks</strong>
            <em>Find work or hire help</em>
          </span>
          <ArrowRightIcon size={18} className={styles.tileArrow} />
        </Link>

        <div className={styles.tile}>
          <span className={styles.tileIcon}><ShieldIcon size={20} /></span>
          <span className={styles.tileText}>
            <strong>Escrow protected</strong>
            <em>Payments held until tasks complete</em>
          </span>
        </div>
      </section>

      <button className={styles.signout} onClick={signOut}>Sign out</button>
    </div>
  );
}
