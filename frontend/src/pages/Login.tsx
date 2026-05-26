import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import PageFrame from '../components/PageFrame';
import Logo from '../components/Logo';
import Input from '../components/Input';
import Button from '../components/Button';
import styles from './Auth.module.css';

export default function Login() {
  const navigate = useNavigate();
  const [showPwd, setShowPwd] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    navigate('/loading');
  };

  return (
    <PageFrame>
      <div className={styles.page}>
        <div className={styles.topArc}>
          <button className={styles.backBtn} onClick={() => navigate(-1)}>←</button>
          <h1 className={styles.brand}>Hiver</h1>
        </div>

        <div className={styles.content}>
          <h2 className={styles.heading}>
            Log In to your <span className={styles.headingAccent}>account</span>
          </h2>
          <p className={styles.subheading}>Lorem Ipsum de la aracounter</p>

          <div className={styles.logoWrap}>
            <Logo size={120} />
          </div>

          <form onSubmit={handleLogin} style={{ width: '100%' }}>
            <div className={styles.formGroup}>
              <Input type="email" placeholder="Enter Email" required />
              <Input
                type={showPwd ? 'text' : 'password'}
                placeholder="Enter Password"
                required
                rightIcon={
                  <span
                    onClick={() => setShowPwd((v) => !v)}
                    style={{ pointerEvents: 'auto', cursor: 'pointer' }}
                  >
                    {showPwd ? '🙈' : '👁️'}
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

            <Button variant="primary" type="submit">Log In</Button>
          </form>

          <div className={styles.divider}>
            <span>Or LogIn with</span>
            <span className={styles.googleIcon}>G</span>
          </div>
          <div className={styles.dividerLine} />

          <p className={styles.bottomLink}>
            Don't have an account?{' '}
            <a onClick={() => navigate('/register')}>Register</a>
          </p>
        </div>

        <div className={styles.bottomArc}>
          <div className={styles.bottomDots} />
        </div>
      </div>
    </PageFrame>
  );
}