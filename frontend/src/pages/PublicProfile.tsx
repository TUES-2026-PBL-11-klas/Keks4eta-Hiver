import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { reviewService, userService } from "@/lib/services";
import { Avatar, Badge, Card, EmptyState, Spinner, Stars } from "@/components/ui";
import { Hexagon } from "@/components/icons";
import type { ClientProfile, HiverProfile, Review } from "@/types";
import s from "./PublicProfile.module.css";

export default function PublicProfile({ kind }: { kind: "hiver" | "client" }) {
  const { id = "" } = useParams();
  const [profile, setProfile] = useState<HiverProfile | ClientProfile | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    const fetchProfile =
      kind === "hiver" ? userService.hiverProfile(id) : userService.clientProfile(id);
    Promise.all([fetchProfile, reviewService.forUser(id).catch(() => [] as Review[])])
      .then(([p, r]) => {
        if (!active) return;
        setProfile(p);
        setReviews(r);
      })
      .catch((e) => active && setError((e as Error).message))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [id, kind]);

  if (loading) {
    return (
      <div className="page-wrap-narrow" style={{ display: "grid", placeItems: "center", minHeight: "50vh" }}>
        <Spinner />
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="page-wrap-narrow">
        <EmptyState icon={<Hexagon size={28} />} title="Profile not found">{error}</EmptyState>
      </div>
    );
  }

  const isHiver = kind === "hiver";
  const hiver = isHiver ? (profile as HiverProfile) : null;
  const client = !isHiver ? (profile as ClientProfile) : null;
  const rating = hiver ? hiver.avg_rating : client!.rating_as_client;

  return (
    <div className="page-wrap-narrow">
      <section className={s.header}>
        <Avatar name={profile.full_name} src={profile.avatar_url} size={96} />
        <div className={s.meta}>
          <h1 className={s.name}>{profile.full_name}</h1>
          <div className={s.statRow}>
            <Stars value={rating} />
            <Badge tone="honey">{isHiver ? hiver!.level : "client"}</Badge>
          </div>
          {hiver?.bio && <p className={s.bio}>{hiver.bio}</p>}
        </div>
      </section>

      <Card>
        <div className={s.stats}>
          {isHiver ? (
            <>
              <div className={s.stat}><span className={s.statValue}>{hiver!.completed_tasks}</span><span className={s.statLabel}>Jobs done</span></div>
              <div className={s.stat}><span className={s.statValue}>{hiver!.xp_points}</span><span className={s.statLabel}>XP</span></div>
              <div className={s.stat}><span className={s.statValue}>{hiver!.review_count}</span><span className={s.statLabel}>Reviews</span></div>
            </>
          ) : (
            <>
              <div className={s.stat}><span className={s.statValue}>{client!.total_tasks}</span><span className={s.statLabel}>Tasks posted</span></div>
              <div className={s.stat}><span className={s.statValue}>{client!.review_count}</span><span className={s.statLabel}>Reviews</span></div>
            </>
          )}
        </div>
        {hiver && hiver.skills.length > 0 && (
          <div className={s.skills}>
            {hiver.skills.map((sk) => <Badge key={sk}>{sk}</Badge>)}
          </div>
        )}
      </Card>

      <h2 className={s.sectionTitle}>Reviews ({reviews.length})</h2>
      {reviews.length === 0 ? (
        <EmptyState icon={<Hexagon size={24} fill="currentColor" />} title="No reviews yet">
          Reviews appear here once completed tasks are rated.
        </EmptyState>
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          {reviews.map((r) => (
            <Card key={r.id} className={s.review}>
              <div className={s.reviewTop}>
                <Stars value={r.rating} />
                <span className={s.date}>{new Date(r.created_at).toLocaleDateString()}</span>
              </div>
              <p className={s.reviewComment}>{r.comment}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
