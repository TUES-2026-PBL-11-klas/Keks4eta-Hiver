import { Link } from "react-router-dom";
import { paths } from "@/constants/routes";
import { Badge, Card } from "@/components/ui";
import { PinIcon, WalletIcon, BoltIcon } from "@/components/icons";
import { VERTICAL_ICON } from "@/components/verticalIcons";
import { budgetLabel } from "@/lib/format";
import type { TaskStatus, TaskSummary } from "@/types";
import s from "./TaskCard.module.css";

const STATUS_LABEL: Record<TaskStatus, string> = {
  open: "Open",
  accepted: "Accepted",
  in_progress: "In progress",
  completed: "Completed",
  cancelled: "Cancelled",
  disputed: "Disputed",
};

const STATUS_TONE: Record<TaskStatus, "honey" | "info" | "success" | "error" | "muted"> = {
  open: "honey",
  accepted: "info",
  in_progress: "info",
  completed: "success",
  cancelled: "muted",
  disputed: "error",
};

export function TaskCard({ task }: { task: TaskSummary }) {
  const Icon = VERTICAL_ICON[task.vertical] ?? VERTICAL_ICON.home;
  const b = budgetLabel(task);
  return (
    <Link to={paths.task(task.id)} style={{ display: "block", height: "100%" }}>
      <Card hover className={s.card}>
        <span className={s.glyph} aria-hidden="true">
          <Icon size={22} />
        </span>
        <div className={s.main}>
          <div className={s.top}>
            <h3 className={s.title}>{task.title}</h3>
            {task.is_urgent && (
              <Badge tone="error">
                <BoltIcon size={11} /> Urgent
              </Badge>
            )}
          </div>
          <span className={s.sub}>{task.vertical} · {task.subcategory}</span>
          <div className={s.meta}>
            {task.location_display && (
              <span className={s.metaItem}>
                <PinIcon size={14} /> {task.location_display}
              </span>
            )}
            {b && (
              <span className={s.metaItem}>
                <WalletIcon size={14} /> {b}
              </span>
            )}
          </div>
          <div className={s.foot}>
            <Badge tone={STATUS_TONE[task.status]}>{STATUS_LABEL[task.status]}</Badge>
          </div>
        </div>
      </Card>
    </Link>
  );
}
