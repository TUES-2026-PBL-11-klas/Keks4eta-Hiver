import { useFetch } from "@/hooks/useFetch";
import type { Task } from "@/types";
import SectionCard from "@/components/SectionCard";
import styles from "./Tasks.module.css";

export default function Tasks() {
  const { data, loading, error } = useFetch<Task[]>("/tasks");

  return (
    <main className={styles.main}>
      <h1 className={styles.heading}>Open Tasks</h1>

      {loading && <p className={styles.state}>Loading tasks...</p>}
      {error && <p className={styles.error}>{error}</p>}

      {data && data.length === 0 && (
        <p className={styles.state}>No open tasks yet.</p>
      )}

      <div className={styles.grid}>
        {data?.map((task) => (
          <SectionCard key={task.id} title={task.subcategory}>
            <div className={styles.meta}>
              <span className={styles.vertical}>{task.vertical}</span>
              {task.is_urgent && <span className={styles.urgent}>Urgent</span>}
            </div>
            {task.location_display && (
              <p className={styles.location}>📍 {task.location_display}</p>
            )}
            {(task.budget_min || task.budget_max) && (
              <p className={styles.budget}>
                💰 {task.budget_min ?? "?"} – {task.budget_max ?? "?"} BGN
              </p>
            )}
            <span className={`${styles.status} ${styles[task.status]}`}>
              {task.status}
            </span>
          </SectionCard>
        ))}
      </div>
    </main>
  );
}
