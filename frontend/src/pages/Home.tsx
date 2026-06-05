import { Link, useNavigate } from "react-router-dom";
import { ROUTES, VERTICALS } from "@/constants/routes";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui";
import { Reveal } from "@/components/Reveal";
import { ArrowRightIcon, ShieldIcon, Hexagon } from "@/components/icons";
import { VERTICAL_ICON } from "@/components/verticalIcons";
import logo from "@/assets/logo.svg";
import s from "./Home.module.css";

const STEPS = [
  { n: "01", title: "Post a task", body: "Describe what you need and name your budget." },
  { n: "02", title: "Choose a hiver", body: "Compare offers and pick the right match." },
  { n: "03", title: "Pay securely", body: "Funds sit in escrow — released only when it's done." },
];

export default function Home() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const primaryCta = !isAuthenticated
    ? { label: "Get started", to: ROUTES.REGISTER }
    : { label: "Post a task", to: ROUTES.POST_TASK };

  return (
    <div>
      {/* ── Hero ───────────────────────────────────────────────────── */}
      <section className={s.hero}>
        <div className={s.heroTexture} />
        <div className={s.heroInner}>
          <div>
            <span className={s.kicker}>
              <Hexagon size={13} fill="currentColor" /> Local marketplace
            </span>
            <h1 className={s.headline}>
              Help is just<br />around the <em>corner.</em>
            </h1>
            <p className={s.sub}>
              Post a task, get offers from trusted neighbours, and pay only when the job's
              done right.
            </p>
            <div className={s.actions}>
              <Button className={s.btnLight} size="lg" onClick={() => navigate(primaryCta.to)}>
                {primaryCta.label} <ArrowRightIcon size={18} />
              </Button>
              <Button className={s.btnOutline} variant="ghost" size="lg" onClick={() => navigate(ROUTES.TASKS)}>
                Browse tasks
              </Button>
            </div>
          </div>
          <div className={s.heroArt}>
            <img src={logo} alt="" aria-hidden="true" />
          </div>
        </div>
      </section>

      {/* ── Verticals ──────────────────────────────────────────────── */}
      <section className={s.block}>
        <header className={s.blockHead}>
          <h2>What do you need?</h2>
          <Link to={ROUTES.TASKS} className={s.seeAll}>
            See all <ArrowRightIcon size={14} />
          </Link>
        </header>
        <div className={s.grid}>
          {VERTICALS.map(({ value, label, blurb }, i) => {
            const Icon = VERTICAL_ICON[value];
            return (
              <Reveal key={value} delay={i * 0.05}>
                <Link to={`${ROUTES.TASKS}?vertical=${value}`} className={s.vcard}>
                  <span className={s.vIcon}><Icon size={22} /></span>
                  <span className={s.vLabel}>{label}</span>
                  <span className={s.vHint}>{blurb}</span>
                </Link>
              </Reveal>
            );
          })}
        </div>
      </section>

      {/* ── How it works ───────────────────────────────────────────── */}
      <section className={s.block}>
        <header className={s.blockHead}><h2>How it works</h2></header>
        <ol className={s.steps}>
          {STEPS.map(({ n, title, body }, i) => (
            <Reveal key={n} delay={i * 0.08}>
              <li className={s.step}>
                <span className={s.stepNum}>{n}</span>
                <div>
                  <h3>{title}</h3>
                  <p>{body}</p>
                </div>
              </li>
            </Reveal>
          ))}
        </ol>
      </section>

      {/* ── Trust ──────────────────────────────────────────────────── */}
      <Reveal>
        <section className={s.trust}>
          <ShieldIcon size={22} />
          <p>
            Every payment is <strong>escrow-protected</strong>. Your money is only released
            when you're happy with the work.
          </p>
        </section>
      </Reveal>

      {/* ── Final CTA ──────────────────────────────────────────────── */}
      <Reveal>
        <section className={s.cta}>
          <h2>Ready to get it done?</h2>
          <p>Join thousands of neighbours getting help — and earning — across the city.</p>
          <Button className={s.btnLight} size="lg" onClick={() => navigate(primaryCta.to)}>
            {primaryCta.label} <ArrowRightIcon size={18} />
          </Button>
        </section>
      </Reveal>
    </div>
  );
}
