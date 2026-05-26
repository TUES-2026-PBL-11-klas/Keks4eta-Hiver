import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import PageFrame from '../components/PageFrame';
import Logo from '../components/Logo';
import styles from './Loading.module.css';

export default function Loading() {
  const navigate = useNavigate();

  useEffect(() => {
    const t = setTimeout(() => navigate('/roles'), 1800);
    return () => clearTimeout(t);
  }, [navigate]);

  return (
    <PageFrame>
      <div className={styles.page}>
        <div className={styles.topArc}>
          <h1 className={styles.brand}>Hiver</h1>
        </div>
        <div className={styles.center}>
          <Logo size={140} />
          <p className={styles.welcome}>Welcome...</p>
        </div>
        <div className={styles.bottomArc}>
          <div className={styles.dots} />
        </div>
      </div>
    </PageFrame>
  );
}