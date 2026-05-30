import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "@/constants/routes";
import logo from "@/assets/logo.svg";
import styles from "./Loading.module.css";

export default function Loading() {
  const navigate = useNavigate();

  useEffect(() => {
    const t = setTimeout(() => navigate(ROUTES.HOME), 1800);
    return () => clearTimeout(t);
  }, [navigate]);

  return (
    <div className={styles.page}>
      <div className={styles.texture} />
      <div className={styles.center}>
        <img src={logo} alt="Hiver" className={styles.logo} />
        <span className={styles.word}>Hiver</span>
        <span className={styles.tagline}>Help is just around the corner</span>
        <div className={styles.dots}>
          <i /><i /><i />
        </div>
      </div>
    </div>
  );
}
