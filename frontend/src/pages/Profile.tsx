import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";
import { boostService, userService, type Boost } from "@/lib/services";
import { Avatar, Badge, Button, Card, Stars } from "@/components/ui";
import { GridIcon, SearchIcon, LogOutIcon, ShieldIcon } from "@/components/icons";
import s from "./Profile.module.css";

export default function Profile() {
  const navigate = useNavigate();
  const { user, logout, refresh } = useAuth();
  const [available, setAvailable] = useState(!!user?.is_available_now);
  const [saving, setSaving] = useState(false);
  const [boost, setBoost] = useState<Boost | null>(null);
  const [boostBusy, setBoostBusy] = useState(false);

  useEffect(() => {
    if (user?.role !== "hiver") return;
    boostService.mine().then(setBoost).catch(() => setBoost(null));
  }, [user?.role]);

  if (!user) return null; // guarded by ProtectedRoute

  const isHiver = user.role === "hiver";

  function signOut() {
    logout();
    navigate(ROUTES.HOME);
  }

  async function toggleAvailability() {
    const next = !available;
    setAvailable(next);
    setSaving(true);
    try {
      await userService.setAvailability(next);
      await refresh();
    } catch {
      setAvailable(!next);
    } finally {
      setSaving(false);
    }
  }

  async function buyBoost() {
    setBoostBusy(true);
    try {
      setBoost(await boostService.buy());
    } finally {
      setBoostBusy(false);
    }
  }

  return (
    <div className="page-wrap-narrow">
      <section className={s.header}>
        <Avatar name={user.full_name} src={user.avatar_url} size={96} />
        <div className={s.headerMeta}>
          <h1 className={s.name}>{user.full_name}</h1>
          <p className={s.email}>{user.email}</p>
          <div className={s.badges}>
            <Badge tone="honey">{user.role}</Badge>
            {isHiver && user.level && <Badge tone="muted">{user.level}</Badge>}
            {user.is_oauth && <Badge tone="info">Social login</Badge>}
          </div>
        </div>
      </section>

      <Card>
        <div className={s.stats}>
          {isHiver ? (
            <>
              <div className={s.stat}>
                <span className={s.statValue}><Stars value={user.avg_rating ?? 0} size={16} /></span>
                <span className={s.statLabel}>Rating</span>
              </div>
              <div className={s.stat}>
                <span className={s.statValue}>{user.completed_tasks ?? 0}</span>
                <span className={s.statLabel}>Jobs done</span>
              </div>
              <div className={s.stat}>
                <span className={s.statValue}>{user.xp_points ?? 0}</span>
                <span className={s.statLabel}>XP</span>
              </div>
            </>
          ) : (
            <>
              <div className={s.stat}>
                <span className={s.statValue}><Stars value={user.rating_as_client ?? 5} size={16} /></span>
                <span className={s.statLabel}>Rating</span>
              </div>
              <div className={s.stat}>
                <span className={s.statValue}>{user.total_tasks ?? 0}</span>
                <span className={s.statLabel}>Tasks posted</span>
              </div>
              <div className={s.stat}>
                <span className={s.statValue}>{user.review_count ?? 0}</span>
                <span className={s.statLabel}>Reviews</span>
              </div>
            </>
          )}
        </div>
        {isHiver && user.skills && user.skills.length > 0 && (
          <div className={s.skills}>
            {user.skills.map((sk) => <Badge key={sk}>{sk}</Badge>)}
          </div>
        )}
      </Card>

      {isHiver && (
        <>
          <h2 className="section-title" style={{ margin: "var(--sp-8) 0 var(--sp-4)" }}>Availability</h2>
          <Card>
            <div className={s.availRow}>
              <div className={s.availText}>
                <strong>{available ? "Available for work" : "Not available"}</strong>
                <span>Toggle whether clients can find you in nearby searches.</span>
              </div>
              <label className={s.switch}>
                <input type="checkbox" checked={available} onChange={toggleAvailability} disabled={saving} />
                <span className={s.slider} />
              </label>
            </div>
          </Card>

          <h2 className="section-title" style={{ margin: "var(--sp-8) 0 var(--sp-4)" }}>Visibility boost</h2>
          <Card>
            <div className={s.availRow}>
              <div className={s.availText}>
                <strong>{boost?.is_active ? "Boosted — you rank first in search" : "Stand out to clients"}</strong>
                <span>
                  {boost?.is_active
                    ? `Active until ${new Date(boost.expires_at).toLocaleDateString()}.`
                    : "Rank above other hivers in nearby searches for 7 days."}
                </span>
              </div>
              {boost?.is_active ? (
                <Badge tone="honey">★ Active</Badge>
              ) : (
                <Button size="sm" onClick={buyBoost} disabled={boostBusy}>
                  {boostBusy ? "…" : "Boost · 5 BGN"}
                </Button>
              )}
            </div>
          </Card>
        </>
      )}

      <div className={s.tiles}>
        <button className={s.tile} onClick={() => navigate(ROUTES.DASHBOARD)}>
          <span className={s.tileIcon}><GridIcon size={20} /></span>
          <span className={s.tileText}>
            <strong>Dashboard</strong>
            <span>{isHiver ? "Your work & stats" : "Your posted tasks"}</span>
          </span>
        </button>
        <button className={s.tile} onClick={() => navigate(ROUTES.TASKS)}>
          <span className={s.tileIcon}><SearchIcon size={20} /></span>
          <span className={s.tileText}>
            <strong>Browse tasks</strong>
            <span>{isHiver ? "Find work" : "See the marketplace"}</span>
          </span>
        </button>
        <div className={s.tile}>
          <span className={s.tileIcon}><ShieldIcon size={20} /></span>
          <span className={s.tileText}>
            <strong>Escrow protected</strong>
            <span>Payments held until tasks complete</span>
          </span>
        </div>
      </div>

      <Button variant="secondary" block className={s.signout} onClick={signOut}>
        <LogOutIcon size={18} /> Sign out
      </Button>
    </div>
  );
}
