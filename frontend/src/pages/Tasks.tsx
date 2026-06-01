import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { taskService } from "@/lib/services";
import { VERTICALS } from "@/constants/routes";
import { TaskCard } from "@/components/TaskCard";
import { Button, EmptyState, Skeleton } from "@/components/ui";
import { Reveal } from "@/components/Reveal";
import { BoltIcon, Hexagon } from "@/components/icons";
import type { Paginated, TaskSummary, Vertical } from "@/types";
import s from "./Tasks.module.css";

const cx = (...c: (string | false)[]) => c.filter(Boolean).join(" ");

export default function Tasks() {
  const [params, setParams] = useSearchParams();
  const vertical = (params.get("vertical") as Vertical | null) ?? undefined;
  const urgentOnly = params.get("urgent") === "1";
  const [page, setPage] = useState(1);

  const [data, setData] = useState<Paginated<TaskSummary> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    taskService
      .search({ vertical, is_urgent: urgentOnly || undefined, page, page_size: 12 })
      .then((res) => active && setData(res))
      .catch((e) => active && setError((e as Error).message))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [vertical, urgentOnly, page]);

  function setVertical(v?: Vertical) {
    const next = new URLSearchParams(params);
    if (v) next.set("vertical", v);
    else next.delete("vertical");
    setParams(next);
    setPage(1);
  }

  function toggleUrgent() {
    const next = new URLSearchParams(params);
    if (urgentOnly) next.delete("urgent");
    else next.set("urgent", "1");
    setParams(next);
    setPage(1);
  }

  const items = data?.items ?? [];

  return (
    <div className="page-wrap">
      <header className={s.head}>
        <p className={s.eyebrow}>Marketplace</p>
        <h1 className={s.title}>Open tasks</h1>
        <p className={s.count}>
          {loading ? "Finding tasks near you…" : `${data?.total ?? 0} task${data?.total === 1 ? "" : "s"} found`}
        </p>
      </header>

      <div className={s.filters}>
        <button className={cx(s.chip, !vertical && s.chipOn)} onClick={() => setVertical(undefined)}>
          All
        </button>
        {VERTICALS.map((v) => (
          <button
            key={v.value}
            className={cx(s.chip, vertical === v.value && s.chipOn)}
            onClick={() => setVertical(v.value)}
          >
            {v.label}
          </button>
        ))}
        <span className={s.divider} />
        <button className={cx(s.chip, urgentOnly && s.chipOn)} onClick={toggleUrgent}>
          <BoltIcon size={14} /> Urgent
        </button>
      </div>

      {loading && (
        <div className={s.grid}>
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className={s.skel} height={120} radius={22} />
          ))}
        </div>
      )}

      {!loading && error && (
        <EmptyState icon={<Hexagon size={28} />} title="Couldn't load tasks">
          {error}
        </EmptyState>
      )}

      {!loading && !error && items.length === 0 && (
        <EmptyState icon={<Hexagon size={28} fill="currentColor" />} title="The hive's quiet here">
          No open tasks match these filters yet — try clearing them or check back soon.
        </EmptyState>
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <div className={s.grid}>
            {items.map((task, i) => (
              <Reveal key={task.id} delay={Math.min(i, 6) * 0.04}>
                <TaskCard task={task} />
              </Reveal>
            ))}
          </div>

          {(data!.total > data!.page_size) && (
            <div className={s.pager}>
              <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Previous
              </Button>
              <span>Page {data!.page} of {Math.max(1, Math.ceil(data!.total / data!.page_size))}</span>
              <Button
                variant="secondary"
                size="sm"
                disabled={page * data!.page_size >= data!.total}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
