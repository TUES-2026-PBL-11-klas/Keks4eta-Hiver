import { useNavigate } from 'react-router-dom';
import PageFrame from '../components/PageFrame';
import Logo from '../components/Logo';
import Button from '../components/Button';
import styles from './Home.module.css';

export default function Home() {
  const navigate = useNavigate();

  return (
    <PageFrame>
      <div className={styles.page}>
        <div className={styles.whiteCircle}>
          <h1 className={styles.brand}>Hiver</h1>
          <Logo size={130} />
          <p className={styles.tagline}>
            Help is just around<br />the corner. Get the<br />perfect fix.
          </p>
        </div>

        <div className={styles.dotsArea} />

        <div className={styles.actions}>
          <Button variant="outline" onClick={() => navigate('/register')}>
            Create Account
          </Button>
          <Button variant="primary" onClick={() => navigate('/login')}>
            Log In
          </Button>
        </div>
      </div>
    </PageFrame>
  );
}