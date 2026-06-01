import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";
import { taskService, userService } from "@/lib/services";
import { TaskCard } from "@/components/TaskCard";
import { Button, Card, EmptyState, Spinner, Stars } from "@/components/ui";
import { Reveal } from "@/components/Reveal";
import { BoltIcon, PlusIcon, Hexagon } from "@/components/icons";
import type { TaskSummary } from "@/types";
import s from "./Dashboard.module.css";

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();

  if (user?.role === "hiver") return <HiverDashboard />;
  return <ClientDashboard navigate={navigate} />;
}

function ClientDashboard({ navigate }: { navigate: ReturnType<typeof useNavigate> }) {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    taskService
      .myTasks(1, 50)
      .then((res) => active && setTasks(res.items))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="page-wrap">
      <header className={s.head}>
        <div>
          <h1 className={s.greeting}>Hi, {user?.full_name?.split(" ")[0]} 👋</h1>
          <p className={s.subtitle}>Manage the tasks you've posted.</p>
        </div>
        <Button onClick={() => navigate(ROUTES.POST_TASK)}>
          <PlusIcon size={18} /> Post a task
        </Button>
      </header>

      <Card>
        <div className={s.stats}>
          <div className={s.stat}>
            <span className={s.statValue}>{user?.total_tasks ?? 0}</span>
            <span className={s.statLabel}>Tasks posted</span>
          </div>
          <div className={s.stat}>
            <span className={s.statValue}>
              <Stars value={user?.rating_as_client ?? 5} size={18} />
            </span>
            <span className={s.statLabel}>Your rating</span>
          </div>
          <div className={s.stat}>
            <span className={s.statValue}>{user?.review_count ?? 0}</span>
            <span className={s.statLabel}>Reviews</span>
          </div>
        </div>
      </Card>

      <h2 className={s.sectionTitle}>Your tasks</h2>
      {loading ? (
        <div style={{ display: "grid", placeItems: "center", padding: 48 }}><Spinner /></div>
      ) : tasks.length === 0 ? (
        <EmptyState
          icon={<Hexagon size={28} fill="currentColor" />}
          title="No tasks yet"
          action={<Button onClick={() => navigate(ROUTES.POST_TASK)}>Post your first task</Button>}
        >
          Post a task and trusted hivers nearby will start sending offers.
        </EmptyState>
      ) : (
        <div className={s.grid}>
          {tasks.map((t, i) => (
            <Reveal key={t.id} delay={Math.min(i, 6) * 0.04}>
              <TaskCard task={t} />
            </Reveal>
          ))}
        </div>
      )}
    </div>
  );
}

function HiverDashboard() {
  const { user, refresh } = useAuth();
  const [available, setAvailable] = useState(!!user?.is_available_now);
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  async function toggle() {
    const next = !available;
    setAvailable(next);
    setSaving(true);
    try {
      await userService.setAvailability(next);
      await refresh();
    } catch {
      setAvailable(!next); // revert on failure
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page-wrap">
      <header className={s.head}>
        <div>
          <h1 className={s.greeting}>Hi, {user?.full_name?.split(" ")[0]} 👋</h1>
          <p className={s.subtitle}>Your hiver workspace.</p>
        </div>
        <Button onClick={() => navigate(ROUTES.TASKS)}>Find work</Button>
      </header>

      <Card>
        <div className={s.stats}>
          <div className={s.stat}>
            <span className={s.statValue}>
              <Stars value={user?.avg_rating ?? 0} size={18} />
            </span>
            <span className={s.statLabel}>Avg rating</span>
          </div>
          <div className={s.stat}>
            <span className={s.statValue}>{user?.completed_tasks ?? 0}</span>
            <span className={s.statLabel}>Jobs done</span>
          </div>
          <div className={s.stat}>
            <span className={s.statValue}>{user?.xp_points ?? 0}</span>
            <span className={s.statLabel}>XP · {user?.level}</span>
          </div>
        </div>
      </Card>

      <h2 className={s.sectionTitle}>Availability</h2>
      <Card>
        <div className={s.availRow}>
          <div className={s.availText}>
            <strong>{available ? "Available for work" : "Not available"}</strong>
            <span>{available ? "You'll show up in nearby searches." : "Turn on to appear in client searches."}</span>
          </div>
          <label className={s.switch}>
            <input type="checkbox" checked={available} onChange={toggle} disabled={saving} />
            <span className={s.slider} />
          </label>
        </div>
      </Card>

      <h2 className={s.sectionTitle}>Get more work</h2>
      <Card>
        <p className="muted" style={{ marginBottom: 16 }}>
          <BoltIcon size={15} /> Browse open tasks and send offers to win jobs. Higher ratings and more
          completed jobs unlock lower commission.
        </p>
        <Button variant="secondary" onClick={() => navigate(ROUTES.TASKS)}>Browse open tasks</Button>
      </Card>
    </div>
  );
}
