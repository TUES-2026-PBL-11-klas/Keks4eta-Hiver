import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
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

export default function Register() {
  const navigate = useNavigate();
  const { register, loginWithProvider } = useAuth();
  const [fullName, setFullName] = useState("");
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
      await register({ full_name: fullName, email, password });
      navigate(ROUTES.DASHBOARD, { replace: true });
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
          <h1 className={styles.title}>Join the hive</h1>
          <p className={styles.lede}>One account to both hire and earn — switch anytime.</p>

          {error && <p className={styles.error}>{error}</p>}

          <form onSubmit={handleSubmit} className={styles.form}>
            <Input
              id="name"
              label="Full name"
              type="text"
              placeholder="Maria Ivanova"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
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
              placeholder="At least 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
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
              {loading ? "Creating…" : "Create account"}
            </button>
          </form>

          <div className={styles.divider}><span>or sign up with</span></div>

          <div className={styles.socialRow}>
            <button type="button" className={styles.social} onClick={() => loginWithProvider("google")}>
              <GoogleIcon size={18} /> Google
            </button>
            <button type="button" className={styles.social} onClick={() => loginWithProvider("facebook")}>
              <FacebookIcon size={18} /> Facebook
            </button>
          </div>

          <p className={styles.foot}>
            Already registered? <Link to={ROUTES.LOGIN}>Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
