import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "@/lib/api";
import { ROUTES } from "@/constants/routes";
import PageFrame from "@/components/PageFrame";
import Logo from "@/components/Logo";
import Input from "@/components/Input";
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
    <PageFrame>
      <div className={styles.page}>
        <div className={styles.topArc}>
          <button className={styles.backBtn} type="button" onClick={() => navigate(-1)}>←</button>
          <h1 className={styles.brand}>Hiver</h1>
        </div>

        <div className={styles.content}>
          <h2 className={styles.heading}>
            Log In to your <span className={styles.headingAccent}>account</span>
          </h2>

          <div className={styles.logoWrap}>
            <Logo size={100} />
          </div>

          {error && <p className={styles.error}>{error}</p>}

          <form onSubmit={handleSubmit} style={{ width: "100%" }}>
            <div className={styles.formGroup}>
              <Input
                type="email"
                placeholder="Enter Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <Input
                type={showPwd ? "text" : "password"}
                placeholder="Enter Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                rightIcon={
                  <span onClick={() => setShowPwd((v) => !v)} style={{ cursor: "pointer" }}>
                    {showPwd ? "🙈" : "👁️"}
                  </span>
                }
              />
            </div>

            <div className={styles.rowBetween}>
              <span className={styles.remember}>
                <span className={styles.checkbox} /> Remember me
              </span>
              <span className={styles.forgot}>Forgot password?</span>
            </div>

            <button className={styles.btn} type="submit" disabled={loading}>
              {loading ? "Signing in…" : "Log In"}
            </button>
          </form>

          <div className={styles.divider}>
            <span>Or log in with</span>
            <span className={styles.googleIcon}>G</span>
          </div>
          <div className={styles.dividerLine} />

          <p className={styles.bottomLink}>
            Don't have an account? <Link to={ROUTES.REGISTER}>Register</Link>
          </p>
        </div>

        <div className={styles.bottomArc}>
          <div className={styles.bottomDots} />
        </div>
      </div>
    </PageFrame>
  );
}
