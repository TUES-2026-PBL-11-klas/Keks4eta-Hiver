import {
  forwardRef,
  type ButtonHTMLAttributes,
  type HTMLAttributes,
  type ReactNode,
} from "react";
import { StarIcon } from "@/components/icons";
import s from "./ui.module.css";

const cx = (...c: (string | false | undefined)[]) => c.filter(Boolean).join(" ");

// ── Button ──────────────────────────────────────────────────────────────────
type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  block?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", size = "md", block, className, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      className={cx(
        s.btn,
        s[variant],
        size === "sm" && s.sm,
        size === "lg" && s.lg,
        block && s.block,
        className,
      )}
      {...rest}
    />
  );
});

// ── Card ──────────────────────────────────────────────────────────────────
interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
}
export function Card({ hover, className, ...rest }: CardProps) {
  return <div className={cx(s.card, hover && s.cardHover, className)} {...rest} />;
}

// ── Badge ───────────────────────────────────────────────────────────────────
type Tone = "default" | "honey" | "success" | "info" | "error" | "muted";
const toneClass: Record<Tone, string | undefined> = {
  default: undefined,
  honey: s.badgeHoney,
  success: s.badgeSuccess,
  info: s.badgeInfo,
  error: s.badgeError,
  muted: s.badgeMuted,
};
export function Badge({
  tone = "default",
  className,
  ...rest
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return <span className={cx(s.badge, toneClass[tone], className)} {...rest} />;
}

// ── Avatar (hex) ──────────────────────────────────────────────────────────────
export function Avatar({
  name,
  src,
  size = 44,
}: {
  name: string;
  src?: string | null;
  size?: number;
}) {
  const initials = name
    .split(" ")
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
  return (
    <span
      className={s.avatar}
      style={{ width: size, height: size, fontSize: size * 0.4 }}
      aria-hidden={!name}
    >
      {src ? <img src={src} alt={name} /> : initials}
    </span>
  );
}

// ── Skeleton ────────────────────────────────────────────────────────────────
export function Skeleton({
  width,
  height = 16,
  radius,
  style,
  ...rest
}: HTMLAttributes<HTMLDivElement> & {
  width?: number | string;
  height?: number | string;
  radius?: number | string;
}) {
  return (
    <div
      className={s.skeleton}
      style={{ width: width ?? "100%", height, borderRadius: radius, ...style }}
      {...rest}
    />
  );
}

// ── Spinner ────────────────────────────────────────────────────────────────
export function Spinner({ className }: { className?: string }) {
  return <span className={cx(s.spinner, className)} role="status" aria-label="Loading" />;
}

// ── Empty / error state ─────────────────────────────────────────────────────
export function EmptyState({
  icon,
  title,
  children,
  action,
}: {
  icon?: ReactNode;
  title: string;
  children?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className={s.empty}>
      {icon && <span className={s.emptyHex}>{icon}</span>}
      <p className={s.emptyTitle}>{title}</p>
      {children && <p className={s.emptyText}>{children}</p>}
      {action}
    </div>
  );
}

// ── Star rating (read-only display) ───────────────────────────────────────────
export function Stars({ value, size = 15 }: { value: number; size?: number }) {
  return (
    <span style={{ display: "inline-flex", gap: 1, color: "var(--honey)" }} aria-label={`${value} out of 5`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <StarIcon key={n} size={size} filled={n <= Math.round(value)} />
      ))}
    </span>
  );
}
