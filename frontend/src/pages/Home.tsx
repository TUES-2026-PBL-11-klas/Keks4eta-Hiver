import { Link } from "react-router-dom";
import { ROUTES } from "@/constants/routes";
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
    <main className={styles.main}>
      <section className={styles.hero}>
        <h1 className={styles.headline}>
          Find a <span>hiver</span> for anything
        </h1>
        <p className={styles.sub}>
          Post a task, get offers from skilled locals, pay only when done.
        </p>
        <div className={styles.actions}>
          <Link to={ROUTES.REGISTER} className={styles.btnPrimary}>
            Post a task
          </Link>
          <Link to={ROUTES.TASKS} className={styles.btnOutline}>
            Browse tasks
          </Link>
        </div>
      </section>

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

      <section className={styles.howItWorks}>
        <h2>How it works</h2>
        <div className={styles.steps}>
          <div className={styles.step}>
            <span className={styles.stepNum}>1</span>
            <h3>Post a task</h3>
            <p>Describe what you need and set a budget.</p>
          </div>
          <div className={styles.step}>
            <span className={styles.stepNum}>2</span>
            <h3>Choose a hiver</h3>
            <p>Review offers and pick the best match.</p>
          </div>
          <div className={styles.step}>
            <span className={styles.stepNum}>3</span>
            <h3>Pay securely</h3>
            <p>Funds held in escrow — released only when done.</p>
          </div>
        </div>
      </section>
    </main>
  );
}
