import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";
import styles from "./Input.module.css";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

const Input = forwardRef<HTMLInputElement, Props>(function Input(
  { label, leftIcon, rightIcon, className = "", id, ...rest },
  ref
) {
  return (
    <label className={styles.field} htmlFor={id}>
      {label && <span className={styles.label}>{label}</span>}
      <span className={styles.box}>
        {leftIcon && <span className={styles.left}>{leftIcon}</span>}
        <input
          ref={ref}
          id={id}
          className={`${styles.input} ${leftIcon ? styles.hasLeft : ""} ${className}`}
          {...rest}
        />
        {rightIcon && <span className={styles.right}>{rightIcon}</span>}
      </span>
    </label>
  );
});

export default Input;
