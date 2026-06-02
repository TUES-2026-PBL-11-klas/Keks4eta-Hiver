import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { notificationService, type AppNotification } from "@/lib/services";
import { paths } from "@/constants/routes";
import s from "./NotificationBell.module.css";

function BellIcon({ size = 20 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  );
}

export default function NotificationBell() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const [items, setItems] = useState<AppNotification[]>([]);
  const ref = useRef<HTMLDivElement>(null);

  const refreshCount = useCallback(async () => {
    try {
      setUnread((await notificationService.unreadCount()).unread);
    } catch {
      /* offline / not signed in — leave count as-is */
    }
  }, []);

  // Poll the unread count every 20s while signed in.
  useEffect(() => {
    if (!isAuthenticated) {
      setUnread(0);
      return;
    }
    void refreshCount();
    const id = window.setInterval(refreshCount, 20000);
    return () => window.clearInterval(id);
  }, [isAuthenticated, refreshCount]);

  // Close the panel on an outside click.
  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next) {
      try {
        setItems(await notificationService.list());
      } catch {
        setItems([]);
      }
    }
  }

  async function onItemClick(n: AppNotification) {
    if (!n.is_read) {
      try {
        await notificationService.markRead(n.id);
      } catch {
        /* ignore */
      }
      setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)));
      void refreshCount();
    }
    const taskId = n.data?.task_id as string | undefined;
    setOpen(false);
    if (taskId) navigate(paths.task(taskId));
  }

  async function markAll() {
    try {
      await notificationService.markAllRead();
    } catch {
      /* ignore */
    }
    setItems((prev) => prev.map((x) => ({ ...x, is_read: true })));
    setUnread(0);
  }

  if (!isAuthenticated) return null;

  return (
    <div className={s.wrap} ref={ref}>
      <button className={s.bell} onClick={toggle} aria-label="Notifications" aria-haspopup="menu">
        <BellIcon size={20} />
        {unread > 0 && <span className={s.badge}>{unread > 9 ? "9+" : unread}</span>}
      </button>

      {open && (
        <div className={s.panel} role="menu">
          <div className={s.head}>
            <span>Notifications</span>
            {items.some((n) => !n.is_read) && (
              <button className={s.markAll} onClick={markAll}>
                Mark all read
              </button>
            )}
          </div>

          {items.length === 0 ? (
            <p className={s.empty}>You&rsquo;re all caught up.</p>
          ) : (
            <ul className={s.list}>
              {items.map((n) => (
                <li key={n.id}>
                  <button
                    className={`${s.item} ${n.is_read ? "" : s.unread}`}
                    onClick={() => onItemClick(n)}
                  >
                    <span className={s.itemTitle}>{n.title}</span>
                    <span className={s.itemBody}>{n.body}</span>
                    <span className={s.itemTime}>{new Date(n.sent_at).toLocaleString()}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
