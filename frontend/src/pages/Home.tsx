import { Link } from "react-router-dom";
import { ROUTES } from "@/constants/routes";
import PageFrame from "@/components/PageFrame";
import Logo from "@/components/Logo";
import styles from "./Home.module.css";

const VERTICALS = [
  { icon: "🏠", label: "Home" },
  { icon: "📚", label: "Learn" },
  { icon: "🔧", label: "Fix" },
  { icon: "🚗", label: "Move" },
  { icon: "💻", label: "Tech" },
  { icon: "🌿", label: "Garden" },
];

export default function Home() {
  return (
    <PageFrame>
      {/* Hero — B's orange splash style */}
      <section className={styles.hero}>
        <div className={styles.heroInner}>
          <h1 className={styles.brand}>Hiver</h1>
          <Logo size={100} />
          <p className={styles.tagline}>
            Help is just around the corner.<br />Get the perfect fix.
          </p>
        </div>
        <div className={styles.heroActions}>
          <Link to={ROUTES.REGISTER} className={styles.btnPrimary}>Post a task</Link>
          <Link to={ROUTES.LOGIN} className={styles.btnOutline}>Sign in</Link>
        </div>
      </section>

      {/* Verticals grid — A's content */}
      <section className={styles.verticals}>
        <h2>What do you need?</h2>
        <div className={styles.grid}>
          {VERTICALS.map(({ icon, label }) => (
            <Link to={ROUTES.TASKS} key={label} className={styles.verticalCard}>
              <span className={styles.icon}>{icon}</span>
              <span>{label}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* How it works — A's content */}
      <section className={styles.howItWorks}>
        <h2>How it works</h2>
        <div className={styles.steps}>
          <div className={styles.step}>
            <span className={styles.stepNum}>1</span>
            <div>
              <h3>Post a task</h3>
              <p>Describe what you need and set a budget.</p>
            </div>
          </div>
          <div className={styles.step}>
            <span className={styles.stepNum}>2</span>
            <div>
              <h3>Choose a hiver</h3>
              <p>Review offers and pick the best match.</p>
            </div>
          </div>
          <div className={styles.step}>
            <span className={styles.stepNum}>3</span>
            <div>
              <h3>Pay securely</h3>
              <p>Funds held in escrow — released only when done.</p>
            </div>
          </div>
        </div>
      </section>
    </PageFrame>
  );
}
