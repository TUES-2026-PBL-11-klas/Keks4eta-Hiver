import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "@/lib/api";
import { ROUTES } from "@/constants/routes";
import Input from "@/components/Input";
import { ArrowLeftIcon, EyeIcon, EyeOffIcon, GoogleIcon } from "@/components/icons";
import logo from "@/assets/logo.svg";
import styles from "./Auth.module.css";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api.post<{ access_token: string }>("/auth/login", { email, password });
      localStorage.setItem("access_token", data.access_token);
      navigate(ROUTES.HOME);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <header className={styles.hero}>
        <div className={styles.heroTexture} />
        <button className={styles.back} type="button" onClick={() => navigate(-1)} aria-label="Go back">
          <ArrowLeftIcon size={20} />
        </button>
        <img src={logo} alt="Hiver" className={styles.heroLogo} />
        <span className={styles.heroWord}>Hiver</span>
      </header>

      <div className={styles.body}>
        <h1 className={styles.title}>Welcome back</h1>
        <p className={styles.lede}>Sign in to pick up where you left off.</p>

        {error && <p className={styles.error}>{error}</p>}

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

          <div className={styles.row}>
            <label className={styles.remember}>
              <input type="checkbox" />
              <span>Remember me</span>
            </label>
            <button type="button" className={styles.link}>Forgot password?</button>
          </div>

          <button className={styles.submit} type="submit" disabled={loading}>
            {loading ? "Signing in…" : "Log in"}
          </button>
        </form>

        <div className={styles.divider}><span>or continue with</span></div>

        <button type="button" className={styles.social}>
          <GoogleIcon size={18} /> Google
        </button>

        <p className={styles.foot}>
          New to Hiver? <Link to={ROUTES.REGISTER}>Create an account</Link>
        </p>
      </div>
    </div>
  );
}
