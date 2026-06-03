import { useState, type FormEvent } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";
import Input from "@/components/Input";
import {
  ArrowLeftIcon,
  EyeIcon,
  EyeOffIcon,
  GoogleIcon,
  FacebookIcon,
} from "@/components/icons";
import logo from "@/assets/logo.svg";
import styles from "./Auth.module.css";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, loginWithProvider } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const oauthFailed = new URLSearchParams(location.search).get("error") === "oauth_failed";
  const from = (location.state as { from?: string } | null)?.from ?? ROUTES.DASHBOARD;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.screen}>
      <div className={styles.page}>
        <header className={styles.hero}>
          <div className={styles.heroTexture} />
          <button className={styles.back} type="button" onClick={() => navigate(ROUTES.HOME)} aria-label="Go home">
            <ArrowLeftIcon size={20} />
          </button>
          <img src={logo} alt="Hiver" className={styles.heroLogo} />
          <span className={styles.heroWord}>Hiver</span>
        </header>

        <div className={styles.body}>
          <h1 className={styles.title}>Welcome back</h1>
          <p className={styles.lede}>Sign in to pick up where you left off.</p>

          {(error || oauthFailed) && (
            <p className={styles.error}>
              {error || "Social sign-in didn’t complete. Please try again."}
            </p>
          )}

          <form onSubmit={handleSubmit} className={styles.form}>
            <Input
              id="email"
              label="Email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              id="password"
              label="Password"
              type={showPwd ? "text" : "password"}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              rightIcon={
                <button
                  type="button"
                  onClick={() => setShowPwd((v) => !v)}
                  aria-label={showPwd ? "Hide password" : "Show password"}
                >
                  {showPwd ? <EyeOffIcon size={19} /> : <EyeIcon size={19} />}
                </button>
              }
            />

            <button className={styles.submit} type="submit" disabled={loading}>
              {loading ? "Signing in…" : "Log in"}
            </button>
          </form>

          <div className={styles.divider}><span>or continue with</span></div>

          <div className={styles.socialRow}>
            <button type="button" className={styles.social} onClick={() => loginWithProvider("google")}>
              <GoogleIcon size={18} /> Google
            </button>
            <button type="button" className={styles.social} onClick={() => loginWithProvider("facebook")}>
              <FacebookIcon size={18} /> Facebook
            </button>
          </div>

          <p className={styles.foot}>
            New to Hiver? <Link to={ROUTES.REGISTER}>Create an account</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
