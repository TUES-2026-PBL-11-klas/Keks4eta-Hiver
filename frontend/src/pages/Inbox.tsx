import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { messageService, type Conversation } from "@/lib/services";
import { paths } from "@/constants/routes";
import { Avatar, Card, EmptyState, Spinner } from "@/components/ui";
import { ChatIcon } from "@/components/icons";
import s from "./Inbox.module.css";

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min}m`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h`;
  const days = Math.floor(hr / 24);
  if (days < 7) return `${days}d`;
  return new Date(iso).toLocaleDateString();
}

export default function Inbox() {
  const [items, setItems] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const data = await messageService.conversations();
        if (active) setItems(data);
      } catch (e) {
        if (active) setError((e as Error).message);
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    // Keep the inbox reasonably fresh while it's open.
    const t = window.setInterval(load, 15000);
    return () => {
      active = false;
      window.clearInterval(t);
    };
  }, []);

  if (loading) {
    return (
      <div className="page-wrap" style={{ display: "grid", placeItems: "center", minHeight: "50vh" }}>
        <Spinner />
      </div>
    );
  }

  return (
    <div className="page-wrap-narrow">
      <header className={s.head}>
        <h1 className={s.title}>Inbox</h1>
        <p className={s.lede}>Your conversations with clients and hivers.</p>
      </header>

      {error && (
        <EmptyState icon={<ChatIcon size={28} />} title="Couldn't load your inbox">
          {error}
        </EmptyState>
      )}

      {!error && items.length === 0 && (
        <EmptyState icon={<ChatIcon size={28} />} title="No conversations yet">
          Chats open up once an offer is accepted on a task.
        </EmptyState>
      )}

      {items.length > 0 && (
        <div className={s.list}>
          {items.map((c) => (
            <Link key={c.task_id} to={paths.task(c.task_id)} className={s.rowLink}>
              <Card hover className={s.row}>
                <Avatar name={c.other_user_name} src={c.other_user_avatar} size={48} />
                <div className={s.body}>
                  <div className={s.topLine}>
                    <span className={s.name}>{c.other_user_name}</span>
                    <span className={s.time}>{timeAgo(c.last_at)}</span>
                  </div>
                  <span className={s.task}>{c.task_title}</span>
                  <span className={`${s.preview} ${c.unread > 0 ? s.unreadPreview : ""}`}>
                    {c.last_message}
                  </span>
                </div>
                {c.unread > 0 && <span className={s.badge}>{c.unread}</span>}
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
