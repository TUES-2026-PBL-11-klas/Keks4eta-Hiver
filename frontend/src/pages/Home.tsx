import type { CSSProperties } from "react";
import { Link } from "react-router-dom";
import { ROUTES } from "@/constants/routes";
import {
  CleanIcon,
  LearnIcon,
  FixIcon,
  MoveIcon,
  TechIcon,
  GardenIcon,
  ArrowRightIcon,
  ShieldIcon,
  Hexagon,
} from "@/components/icons";
import logo from "@/assets/logo.svg";
import styles from "./Home.module.css";

const VERTICALS = [
  { Icon: CleanIcon, label: "Home", hint: "Cleaning & chores" },
  { Icon: LearnIcon, label: "Learn", hint: "Tutoring & lessons" },
  { Icon: FixIcon, label: "Fix", hint: "Repairs & handywork" },
  { Icon: MoveIcon, label: "Move", hint: "Delivery & moving" },
  { Icon: TechIcon, label: "Tech", hint: "Setup & support" },
  { Icon: GardenIcon, label: "Garden", hint: "Outdoor & plants" },
];

const STEPS = [
  { n: "01", title: "Post a task", body: "Describe what you need and name your budget." },
  { n: "02", title: "Choose a hiver", body: "Compare offers and pick the right match." },
  { n: "03", title: "Pay securely", body: "Funds sit in escrow — released only when it's done." },
];

/** Stagger delay as a typed custom property. */
const d = (ms: number): CSSProperties => ({ ["--d"]: `${ms}ms` } as CSSProperties);

export default function Home() {
  return (
    <div className={styles.page}>
      {/* ── Hero ───────────────────────────────────────────────────── */}
      <section className={styles.hero}>
        <div className={styles.heroTexture} />
        <span className={`${styles.kicker} rise`} style={d(40)}>
          <Hexagon size={13} fill="currentColor" /> Local marketplace
        </span>

        <h1 className={`${styles.headline} rise`} style={d(110)}>
          Help is just<br />
          around the <em>corner.</em>
        </h1>

        <p className={`${styles.sub} rise`} style={d(190)}>
          Post a task, get offers from trusted neighbours, and pay only when
          the job's done right.
        </p>

        <div className={`${styles.actions} rise`} style={d(260)}>
          <Link to={ROUTES.REGISTER} className={styles.btnPrimary}>
            Post a task <ArrowRightIcon size={18} />
          </Link>
          <Link to={ROUTES.TASKS} className={styles.btnGhost}>
            Browse tasks
          </Link>
        </div>

        <img src={logo} alt="" className={styles.heroLogo} aria-hidden="true" />
      </section>

      {/* ── Verticals ──────────────────────────────────────────────── */}
      <section className={styles.block}>
        <header className={styles.blockHead}>
          <h2>What do you need?</h2>
          <Link to={ROUTES.TASKS} className={styles.seeAll}>
            See all <ArrowRightIcon size={14} />
          </Link>
        </header>

        <div className={styles.grid}>
          {VERTICALS.map(({ Icon, label, hint }, i) => (
            <Link
              to={ROUTES.TASKS}
              key={label}
              className={`${styles.card} rise`}
              style={d(320 + i * 55)}
            >
              <span className={styles.cardIcon}>
                <Icon size={24} />
              </span>
              <span className={styles.cardLabel}>{label}</span>
              <span className={styles.cardHint}>{hint}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* ── How it works ───────────────────────────────────────────── */}
      <section className={styles.block}>
        <header className={styles.blockHead}>
          <h2>How it works</h2>
        </header>

        <ol className={styles.steps}>
          {STEPS.map(({ n, title, body }) => (
            <li key={n} className={styles.step}>
              <span className={styles.stepNum}>{n}</span>
              <div>
                <h3>{title}</h3>
                <p>{body}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* ── Trust footer ───────────────────────────────────────────── */}
      <section className={styles.trust}>
        <ShieldIcon size={20} />
        <p>
          Every payment is <strong>escrow-protected</strong>. Your money is
          only released when you're happy.
        </p>
      </section>
    </div>
  );
}
