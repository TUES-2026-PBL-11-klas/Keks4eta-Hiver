import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "@/lib/api";
import { ROUTES } from "@/constants/routes";
import styles from "./Auth.module.css";

export default function Register() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"client" | "hiver">("client");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/register", {
        full_name: fullName,
        email,
        password,
        role,
      });
      navigate(ROUTES.LOGIN);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className={styles.main}>
      <form className={styles.card} onSubmit={handleSubmit}>
        <h1 className={styles.title}>Create account</h1>

        {error && <p className={styles.error}>{error}</p>}

        <label className={styles.label}>
          Full name
          <input
            className={styles.input}
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
        </label>

        <label className={styles.label}>
          Email
          <input
            className={styles.input}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>

        <label className={styles.label}>
          Password
          <input
            className={styles.input}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
        </label>

        <label className={styles.label}>
          I am a…
          <select
            className={styles.input}
            value={role}
            onChange={(e) => setRole(e.target.value as "client" | "hiver")}
          >
            <option value="client">Client — I need things done</option>
            <option value="hiver">Hiver — I want to earn</option>
          </select>
        </label>

        <button className={styles.btn} type="submit" disabled={loading}>
          {loading ? "Creating..." : "Create account"}
        </button>

        <p className={styles.footer}>
          Already registered? <Link to={ROUTES.LOGIN}>Sign in</Link>
        </p>
      </form>
    </main>
  );
}
