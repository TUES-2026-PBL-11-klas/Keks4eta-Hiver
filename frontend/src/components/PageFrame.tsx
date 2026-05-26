import { ReactNode } from 'react';
import styles from 'PageFrame.module.css';

type Props = { children: ReactNode };

export default function PageFrame({ children }: Props) {
  return (
    <div className={styles.outer}>
      <div className={styles.phone}>{children}</div>
    </div>
  );
}