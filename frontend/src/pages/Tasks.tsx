import type { CSSProperties } from "react";
import { useFetch } from "@/hooks/useFetch";
import type { Task } from "@/types";
import { PinIcon, WalletIcon, BoltIcon, Hexagon } from "@/components/icons";
import styles from "./Tasks.module.css";

const d = (ms: number): CSSProperties => ({ ["--d"]: `${ms}ms` } as CSSProperties);

const STATUS_LABEL: Record<Task["status"], string> = {
  open: "Open",
  in_progress: "In progress",
  completed: "Completed",
  cancelled: "Cancelled",
};

function budget(task: Task): string | null {
  if (task.budget_min == null && task.budget_max == null) return null;
  if (task.budget_min != null && task.budget_max != null)
    return `${task.budget_min}–${task.budget_max} BGN`;
  return `${task.budget_min ?? task.budget_max} BGN`;
}

export default function Tasks() {
  const { data, loading, error } = useFetch<Task[]>("/tasks");

  return (
    <div className={styles.page}>
      <header className={styles.head}>
        <p className={styles.eyebrow}>Marketplace</p>
        <h1 className={styles.title}>Open tasks</h1>
        <p className={styles.count}>
          {data ? `${data.length} task${data.length === 1 ? "" : "s"} nearby` : "Finding tasks near you…"}
        </p>
      </header>

      {loading && (
        <div className={styles.list}>
          {[0, 1, 2].map((i) => (
            <div key={i} className={`${styles.card} ${styles.skeleton}`} aria-hidden="true" />
          ))}
        </div>
      )}

      {error && (
        <div className={styles.notice}>
          <p className={styles.noticeTitle}>Couldn't load tasks</p>
          <p className={styles.noticeBody}>{error}</p>
        </div>
      )}

      {data && data.length === 0 && (
        <div className={styles.empty}>
          <span className={styles.emptyHex}>
            <Hexagon size={30} fill="var(--honey-100)" />
          </span>
          <p className={styles.emptyTitle}>The hive's quiet right now</p>
          <p className={styles.emptyBody}>No open tasks yet — check back soon.</p>
        </div>
      )}

      {data && data.length > 0 && (
        <div className={styles.list}>
          {data.map((task, i) => {
            const b = budget(task);
            return (
              <article key={task.id} className={`${styles.card} rise`} style={d(i * 60)}>
                <span className={styles.glyph} aria-hidden="true">
                  {task.vertical.charAt(0).toUpperCase()}
                </span>

                <div className={styles.cardMain}>
                  <div className={styles.cardTop}>
                    <h2 className={styles.cardTitle}>{task.subcategory}</h2>
                    {task.is_urgent && (
                      <span className={styles.urgent}>
                        <BoltIcon size={12} /> Urgent
                      </span>
                    )}
                  </div>

                  <p className={styles.vertical}>{task.vertical}</p>

                  <div className={styles.meta}>
                    {task.location_display && (
                      <span className={styles.metaItem}>
                        <PinIcon size={14} /> {task.location_display}
                      </span>
                    )}
                    {b && (
                      <span className={styles.metaItem}>
                        <WalletIcon size={14} /> {b}
                      </span>
                    )}
                  </div>

                  <span className={`${styles.status} ${styles[task.status]}`}>
                    {STATUS_LABEL[task.status]}
                  </span>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
