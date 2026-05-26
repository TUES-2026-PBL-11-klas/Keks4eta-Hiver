import { InputHTMLAttributes, ReactNode } from 'react';
import styles from './Input.module.css';

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  rightIcon?: ReactNode;
}

export default function Input({ rightIcon, className = '', ...rest }: Props) {
  return (
    <div className={styles.wrapper}>
      <input className={`${styles.input} ${className}`} {...rest} />
      {rightIcon && <span className={styles.icon}>{rightIcon}</span>}
    </div>
  );
}