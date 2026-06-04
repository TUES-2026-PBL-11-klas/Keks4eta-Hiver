import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { favoriteService } from "@/lib/services";
import { paths } from "@/constants/routes";
import { TaskCard } from "@/components/TaskCard";
import { FavoriteButton } from "@/components/FavoriteButton";
import { useFavorites } from "@/context/FavoritesContext";
import { Avatar, Badge, Card, EmptyState, Spinner, Stars } from "@/components/ui";
import { Hexagon, HeartIcon } from "@/components/icons";
import type { HiverProfile, TaskSummary } from "@/types";
import s from "./Favorites.module.css";

export default function Favorites() {
  const { isFavorited } = useFavorites();
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [hivers, setHivers] = useState<HiverProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    Promise.all([favoriteService.tasks(), favoriteService.hivers()])
      .then(([t, h]) => {
        if (!active) return;
        setTasks(t);
        setHivers(h);
      })
      .catch((e) => active && setError((e as Error).message))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  // Reflect un-saves made on this page without a refetch: only show items still
  // marked saved in the live favorites set.
  const shownTasks = tasks.filter((t) => isFavorited("task", t.id));
  const shownHivers = hivers.filter((h) => isFavorited("hiver", h.user_id));

  if (loading) {
    return (
      <div className="page-wrap" style={{ display: "grid", placeItems: "center", minHeight: "50vh" }}>
        <Spinner />
      </div>
    );
  }

  const empty = shownTasks.length === 0 && shownHivers.length === 0;

  return (
    <div className="page-wrap">
      <header className={s.head}>
        <h1 className={s.title}>Saved</h1>
        <p className={s.lede}>Tasks and hivers you've kept for later.</p>
      </header>

      {error && (
        <EmptyState icon={<Hexagon size={28} />} title="Couldn't load your saved items">
          {error}
        </EmptyState>
      )}

      {!error && empty && (
        <EmptyState
          icon={<HeartIcon size={28} />}
          title="Nothing saved yet"
        >
          Tap the heart on any task or hiver to save it here.
        </EmptyState>
      )}

      {shownTasks.length > 0 && (
        <>
          <h2 className={s.section}>Tasks ({shownTasks.length})</h2>
          <div className={s.taskGrid}>
            {shownTasks.map((t) => <TaskCard key={t.id} task={t} />)}
          </div>
        </>
      )}

      {shownHivers.length > 0 && (
        <>
          <h2 className={s.section}>Hivers ({shownHivers.length})</h2>
          <div className={s.hiverGrid}>
            {shownHivers.map((h) => (
              <Link key={h.user_id} to={paths.hiver(h.user_id)} style={{ display: "block", height: "100%" }}>
                <Card hover className={s.hiver} style={{ position: "relative" }}>
                  <FavoriteButton type="hiver" id={h.user_id} className={s.hiverHeart} />
                  <Avatar name={h.full_name} src={h.avatar_url} size={56} />
                  <div className={s.info}>
                    <span className={s.name}>{h.full_name}</span>
                    <div className={s.statRow}>
                      <Stars value={h.avg_rating} size={14} />
                      <Badge tone="muted">{h.level}</Badge>
                    </div>
                    <span className={s.dist}>{h.completed_tasks} jobs done</span>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
