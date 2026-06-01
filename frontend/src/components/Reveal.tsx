import { motion, useReducedMotion } from "framer-motion";
import type { CSSProperties, ReactNode } from "react";

type Props = {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  /** stagger delay in seconds */
  delay?: number;
  /** travel distance in px */
  y?: number;
  once?: boolean;
};

/**
 * Scroll-into-view reveal. Fades + lifts children when they enter the viewport.
 * Respects prefers-reduced-motion (renders static, fully visible).
 */
export function Reveal({ children, className, style, delay = 0, y = 18, once = true }: Props) {
  const reduce = useReducedMotion();
  if (reduce) {
    return (
      <div className={className} style={style}>
        {children}
      </div>
    );
  }
  return (
    <motion.div
      className={className}
      style={style}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once, margin: "0px 0px -10% 0px" }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
