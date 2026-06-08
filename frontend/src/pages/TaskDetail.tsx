import { useCallback, useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { ROUTES, paths } from "@/constants/routes";
import {
  disputeService,
  messageService,
  offerService,
  paymentService,
  reviewService,
  taskService,
  userService,
  type ChatMessage,
  type Dispute,
  type Escrow,
} from "@/lib/services";
import { budgetLabel } from "@/lib/format";
import { tokens, wsUrl } from "@/lib/api";
import { VERTICAL_ICON } from "@/components/verticalIcons";
import { Avatar, Badge, Button, Card, EmptyState, Spinner, Stars } from "@/components/ui";
import { Modal } from "@/components/Modal";
import { FavoriteButton } from "@/components/FavoriteButton";
import {
  ArrowLeftIcon,
  PinIcon,
  WalletIcon,
  ClockIcon,
  BoltIcon,
  StarIcon,
  Hexagon,
} from "@/components/icons";
import type { Offer, Review, TaskDetail as TaskDetailT } from "@/types";
import s from "./TaskDetail.module.css";

export default function TaskDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  const [task, setTask] = useState<TaskDetailT | null>(null);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [escrow, setEscrow] = useState<Escrow | null>(null);
  const [dispute, setDispute] = useState<Dispute | null>(null);
  const [disputeOpen, setDisputeOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  const [offerOpen, setOfferOpen] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatBusy, setChatBusy] = useState(false);
  const chatLogRef = useRef<HTMLDivElement>(null);
  const [uploadingImg, setUploadingImg] = useState(false);
  // The other party in the chat, so the user can see who they're talking to.
  const [partner, setPartner] = useState<{ name: string; avatar?: string | null; to: string } | null>(null);

  const isOwner = !!user && task?.client_id === user.id;
  const isAssignedHiver = !!user && task?.hiver_id === user.id;
  // Unified accounts: any signed-in user can act as a hiver (the "own task"
  // case is excluded at each call site via !isOwner, and on the backend).
  const isHiver = !!user;
  // Chat opens once a hiver is assigned, between the client and that hiver only.
  const canChat = (isOwner || isAssignedHiver) && !!task?.hiver_id;

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const t = await taskService.get(id);
      setTask(t);
      const [rev] = await Promise.all([
        reviewService.forTask(id).catch(() => [] as Review[]),
      ]);
      setReviews(rev);
      // Offers are visible to the owning client only.
      if (user && t.client_id === user.id) {
        setOffers(await offerService.forTask(id).catch(() => []));
      }
      // Escrow + dispute are visible to the owning client and the assigned hiver.
      if (user && (t.client_id === user.id || t.hiver_id === user.id)) {
        const [esc, dsp] = await Promise.all([
          paymentService.getEscrow(id).catch(() => null),
          disputeService.get(id).catch(() => null),
        ]);
        setEscrow(esc);
        setDispute(dsp);
      } else {
        setEscrow(null);
        setDispute(null);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [id, user]);

  useEffect(() => {
    void load();
  }, [load]);

  const loadMessages = useCallback(async () => {
    if (!canChat || !id) return;
    try {
      setMessages(await messageService.list(id));
    } catch {
      /* ignore transient errors while polling */
    }
  }, [canChat, id]);

  // Poll the thread every 10s while the chat is open (fallback + reconciler).
  useEffect(() => {
    if (!canChat) return;
    void loadMessages();
    const t = window.setInterval(loadMessages, 10000);
    return () => window.clearInterval(t);
  }, [canChat, loadMessages]);

  // Live updates over WebSocket — sending still goes through REST, which
  // broadcasts to this socket; we just append what arrives (deduped by id).
  useEffect(() => {
    if (!canChat || !id || !tokens.access) return;
    const ws = new WebSocket(wsUrl(`/tasks/${id}/ws?token=${tokens.access}`));
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data) as ChatMessage;
        setMessages((prev) =>
          prev.some((m) => m.id === msg.id) ? prev : [...prev, msg],
        );
      } catch {
        /* ignore malformed frames */
      }
    };
    return () => ws.close();
  }, [canChat, id]);

  // Resolve the chat partner (the party that isn't me) so we can show their name.
  useEffect(() => {
    if (!canChat || !task || !user) {
      setPartner(null);
      return;
    }
    let active = true;
    const fetch =
      isOwner && task.hiver_id
        ? userService
            .hiverProfile(task.hiver_id)
            .then((h) => ({ name: h.full_name, avatar: h.avatar_url, to: paths.hiver(h.user_id) }))
        : userService
            .clientProfile(task.client_id)
            .then((c) => ({ name: c.full_name, avatar: c.avatar_url, to: paths.client(c.user_id) }));
    fetch.then((p) => active && setPartner(p)).catch(() => active && setPartner(null));
    return () => {
      active = false;
    };
  }, [canChat, task, user, isOwner]);

  // Keep the chat scrolled to the newest message.
  useEffect(() => {
    const el = chatLogRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  async function sendMessage(e: FormEvent) {
    e.preventDefault();
    const text = chatInput.trim();
    if (!text || !id) return;
    setChatBusy(true);
    try {
      await messageService.send(id, text);
      setChatInput("");
      await loadMessages();
    } catch (err) {
      setActionError((err as Error).message);
    } finally {
      setChatBusy(false);
    }
  }

  async function onPickImage(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-selecting the same file
    if (!file) return;
    setUploadingImg(true);
    setActionError("");
    try {
      await taskService.uploadImage(id, file);
      await load();
    } catch (err) {
      setActionError((err as Error).message);
    } finally {
      setUploadingImg(false);
    }
  }

  async function removeImage(url: string) {
    if (!id) return;
    setActionError("");
    try {
      await taskService.removeImage(id, url);
      await load();
    } catch (err) {
      setActionError((err as Error).message);
    }
  }

  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    setActionError("");
    try {
      await fn();
      await load();
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="page-wrap" style={{ display: "grid", placeItems: "center", minHeight: "50vh" }}>
        <Spinner />
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="page-wrap">
        <EmptyState icon={<Hexagon size={28} />} title="Task not found"
          action={<Button variant="secondary" onClick={() => navigate(ROUTES.TASKS)}>Back to tasks</Button>}>
          {error || "This task may have been removed."}
        </EmptyState>
      </div>
    );
  }

  const Icon = VERTICAL_ICON[task.vertical] ?? VERTICAL_ICON.home;
  const b = budgetLabel(task);
  const answers = Object.entries(task.smart_answers ?? {});

  return (
    <div className="page-wrap">
      <button
        type="button"
        className={s.back}
        style={{ background: "none", border: 0, padding: 0, font: "inherit", cursor: "pointer" }}
        onClick={() => (window.history.length > 1 ? navigate(-1) : navigate(ROUTES.TASKS))}
      >
        <ArrowLeftIcon size={16} /> Back
      </button>

      <div className={s.layout}>
        {/* ── Main ─────────────────────────────────────────────── */}
        <div>
          <div className={s.headRow}>
            <span className={s.glyph}><Icon size={26} /></span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <h1 className={s.title}>{task.title}</h1>
              <p className={s.sub}>{task.vertical} · {task.subcategory}</p>
            </div>
            {!isOwner && <FavoriteButton type="task" id={task.id} size={22} />}
          </div>

          <div className={s.badges}>
            <Badge tone={task.status === "open" ? "honey" : task.status === "completed" ? "success" : "info"}>
              {task.status.replace("_", " ")}
            </Badge>
            {task.is_featured && <Badge tone="honey"><StarIcon size={11} filled /> Featured</Badge>}
            {task.is_urgent && <Badge tone="error"><BoltIcon size={11} /> Urgent</Badge>}
          </div>

          <div className={s.metaGrid}>
            <div>
              <div className={s.metaLabel}>Budget</div>
              <div className={s.metaValue}><WalletIcon size={16} /> {b ?? "Open"}</div>
            </div>
            <div>
              <div className={s.metaLabel}>Location</div>
              <div className={s.metaValue}><PinIcon size={16} /> {task.location_display ?? "—"}</div>
            </div>
            <div>
              <div className={s.metaLabel}>Posted</div>
              <div className={s.metaValue}>
                <ClockIcon size={16} /> {new Date(task.created_at).toLocaleDateString()}
              </div>
            </div>
          </div>

          <h2 className={s.sectionTitle}>Description</h2>
          <p className={s.desc}>{task.description}</p>

          {answers.length > 0 && (
            <>
              <h2 className={s.sectionTitle}>Details</h2>
              <div className={s.answers}>
                {answers.map(([k, v]) => (
                  <div key={k} className={s.answer}>
                    <span className={s.answerKey}>{k.replace(/_/g, " ")}</span>
                    <span className={s.answerVal}>{String(v)}</span>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Photos */}
          {(task.image_urls.length > 0 || isOwner) && (
            <>
              <div className={s.photoHead}>
                <h2 className={s.sectionTitle} style={{ margin: 0 }}>Photos</h2>
                {isOwner && (
                  <label className={s.addPhoto}>
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/webp,image/gif"
                      hidden
                      disabled={uploadingImg}
                      onChange={onPickImage}
                    />
                    {uploadingImg ? "Uploading…" : "+ Add photo"}
                  </label>
                )}
              </div>
              {task.image_urls.length > 0 ? (
                <div className={s.gallery}>
                  {task.image_urls.map((url) => (
                    <a key={url} href={url} target="_blank" rel="noreferrer" className={s.thumb}>
                      <img src={url} alt="Task" loading="lazy" />
                      {isOwner && (
                        <button
                          type="button"
                          aria-label="Remove photo"
                          className={s.thumbRemove}
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            void removeImage(url);
                          }}
                        >
                          ×
                        </button>
                      )}
                    </a>
                  ))}
                </div>
              ) : (
                <p className={s.hint} style={{ textAlign: "left" }}>
                  Add photos to help hivers understand the job.
                </p>
              )}
            </>
          )}

          {/* Messages — client + assigned hiver */}
          {canChat && (
            <>
              <h2 className={s.sectionTitle}>Messages</h2>
              <Card className={s.chatCard}>
                {partner && (
                  <Link
                    to={partner.to}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      padding: "10px 12px",
                      borderBottom: "1px solid var(--line)",
                      color: "var(--ink-700)",
                      fontWeight: 600,
                    }}
                  >
                    <Avatar name={partner.name} src={partner.avatar} size={28} />
                    {partner.name}
                  </Link>
                )}
                <div className={s.chatLog} ref={chatLogRef}>
                  {messages.length === 0 ? (
                    <p className={s.hint} style={{ textAlign: "center", margin: "auto" }}>
                      No messages yet. Say hello 👋
                    </p>
                  ) : (
                    messages.map((m) => (
                      <div
                        key={m.id}
                        className={`${s.msgRow} ${m.sender_id === user?.id ? s.msgMine : ""}`}
                      >
                        <span className={s.msgBubble}>{m.content}</span>
                        <span className={s.msgTime}>
                          {new Date(m.created_at).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                    ))
                  )}
                </div>
                <form className={s.chatForm} onSubmit={sendMessage}>
                  <input
                    className={s.input}
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Type a message…"
                    maxLength={1000}
                  />
                  <Button type="submit" size="sm" disabled={chatBusy || !chatInput.trim()}>
                    Send
                  </Button>
                </form>
              </Card>
            </>
          )}

          {/* Reviews */}
          {reviews.length > 0 && (
            <>
              <h2 className={s.sectionTitle}>Reviews</h2>
              <div style={{ display: "grid", gap: 12 }}>
                {reviews.map((r) => (
                  <Card key={r.id} className={s.review}>
                    <div className={s.reviewTop}>
                      <Stars value={r.rating} />
                      <span className={s.offerHours}>{new Date(r.created_at).toLocaleDateString()}</span>
                    </div>
                    <p className={s.reviewComment}>{r.comment}</p>
                  </Card>
                ))}
              </div>
            </>
          )}
        </div>

        {/* ── Side panel ────────────────────────────────────────── */}
        <aside className={s.panel}>
          <Card>
            <div className={s.actions}>
              {actionError && <p className={s.error}>{actionError}</p>}

              {!isAuthenticated && (
                <>
                  <Button onClick={() => navigate(ROUTES.LOGIN)}>Sign in to respond</Button>
                  <p className={s.hint}>Sign in as a hiver to make an offer.</p>
                </>
              )}

              {isHiver && !isOwner && task.status === "open" && (
                <Button onClick={() => setOfferOpen(true)} disabled={busy}>
                  Make an offer
                </Button>
              )}

              {isAssignedHiver && task.status === "accepted" && (
                <Button onClick={() => run(() => taskService.start(task.id))} disabled={busy}>
                  Start task
                </Button>
              )}

              {isOwner && task.status === "in_progress" && (
                <Button onClick={() => run(() => taskService.complete(task.id))} disabled={busy}>
                  Mark complete
                </Button>
              )}

              {isOwner && task.status === "completed" && (
                <Button onClick={() => run(() => paymentService.releaseEscrow(task.id))} disabled={busy}>
                  Release escrow
                </Button>
              )}

              {task.status === "completed" && (isOwner || isAssignedHiver) && (
                <Button variant="secondary" onClick={() => setReviewOpen(true)} disabled={busy}>
                  <StarIcon size={16} /> Leave a review
                </Button>
              )}

              {dispute?.status === "open" && isOwner && (
                <Button onClick={() => run(() => disputeService.resolve(task.id))} disabled={busy}>
                  Release payment &amp; close dispute
                </Button>
              )}
              {dispute?.status === "open" && isAssignedHiver && (
                <Button onClick={() => run(() => disputeService.resolve(task.id))} disabled={busy}>
                  Refund client &amp; close dispute
                </Button>
              )}

              {(isOwner || isAssignedHiver) && escrow?.status === "held" && !dispute && (
                <Button variant="ghost" onClick={() => setDisputeOpen(true)} disabled={busy}>
                  Report a problem
                </Button>
              )}

              {isOwner && (task.status === "open" || task.status === "accepted") && (
                <Button
                  variant="secondary"
                  onClick={() => run(() => taskService.boost(task.id))}
                  disabled={busy}
                >
                  <StarIcon size={16} filled={task.is_featured} />
                  {task.is_featured ? "Extend boost · 3 BGN" : "Boost task · 3 BGN"}
                </Button>
              )}

              {isOwner && task.status !== "completed" && task.status !== "cancelled" && task.status !== "disputed" && (
                <Button variant="ghost" onClick={() => run(() => taskService.cancel(task.id))} disabled={busy}>
                  Cancel task
                </Button>
              )}
            </div>
          </Card>

          {/* Escrow status — client + assigned hiver */}
          {escrow && (isOwner || isAssignedHiver) && (
            <Card>
              <h2 className={s.sectionTitle} style={{ marginTop: 0 }}>Escrow</h2>
              <div style={{ marginBottom: 12 }}>
                <Badge
                  tone={
                    escrow.status === "released" ? "success"
                    : escrow.status === "refunded" ? "info"
                    : escrow.status === "disputed" ? "error"
                    : "honey"
                  }
                >
                  {escrow.status}
                </Badge>
              </div>
              <div className={s.metaGrid} style={{ gridTemplateColumns: "1fr 1fr" }}>
                <div>
                  <div className={s.metaLabel}>Total held</div>
                  <div className={s.metaValue}>{escrow.gross_amount} BGN</div>
                </div>
                <div>
                  <div className={s.metaLabel}>Hiver payout</div>
                  <div className={s.metaValue}>{escrow.hiver_payout} BGN</div>
                </div>
              </div>
              <p className={s.hint} style={{ textAlign: "left", marginTop: 8 }}>
                {escrow.status === "held" && "Funds are held safely until the client confirms the task is done."}
                {escrow.status === "released" && `Released to the hiver (after a ${escrow.platform_fee} BGN platform fee).`}
                {escrow.status === "refunded" && "Refunded to the client after cancellation."}
                {escrow.status === "disputed" && "Locked while a dispute is being reviewed."}
              </p>
            </Card>
          )}

          {/* Dispute — participants */}
          {dispute && (
            <Card>
              <h2 className={s.sectionTitle} style={{ marginTop: 0 }}>Dispute</h2>
              <div style={{ marginBottom: 10 }}>
                <Badge
                  tone={
                    dispute.status === "open" ? "error"
                    : dispute.status === "resolved" ? "success"
                    : "info"
                  }
                >
                  {dispute.status === "resolved"
                    ? "resolved · paid"
                    : dispute.status === "refunded"
                      ? "resolved · refunded"
                      : "open"}
                </Badge>
              </div>
              <p className={s.metaLabel}>Reason</p>
              <p className={s.offerMsg}>{dispute.reason}</p>
              {dispute.admin_note && (
                <>
                  <p className={s.metaLabel} style={{ marginTop: 8 }}>Note</p>
                  <p className={s.offerMsg}>{dispute.admin_note}</p>
                </>
              )}
            </Card>
          )}

          {/* Offers — owner only */}
          {isOwner && (
            <Card>
              <h2 className={s.sectionTitle} style={{ marginTop: 0 }}>
                Offers ({offers.length})
              </h2>
              {offers.length === 0 ? (
                <p className={s.hint}>No offers yet. Hivers will appear here as they bid.</p>
              ) : (
                <div style={{ display: "grid", gap: 16 }}>
                  {offers.map((o) => (
                    <div key={o.id} className={s.offer}>
                      <div className={s.offerHead}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <Avatar name="Hiver" size={34} />
                          <span className={s.offerPrice}>{o.price} BGN</span>
                        </div>
                        <span className={s.offerHours}>~{o.estimated_hours}h</span>
                      </div>
                      <p className={s.offerMsg}>{o.message}</p>
                      {task.status === "open" && (
                        <Button
                          size="sm"
                          onClick={() => run(() => offerService.accept(task.id, o.id))}
                          disabled={busy}
                        >
                          Accept offer
                        </Button>
                      )}
                      {o.status === "accepted" && <Badge tone="success">Accepted</Badge>}
                      <Link to={paths.hiver(o.hiver_id)} className={s.hint} style={{ textAlign: "left" }}>
                        View hiver profile
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )}
        </aside>
      </div>

      {/* ── Offer modal ──────────────────────────────────────────── */}
      <OfferModal
        open={offerOpen}
        onClose={() => setOfferOpen(false)}
        onSubmit={async (body) => {
          await offerService.submit(task.id, body);
          setOfferOpen(false);
          await load();
        }}
      />

      {/* ── Review modal ─────────────────────────────────────────── */}
      <ReviewModal
        open={reviewOpen}
        onClose={() => setReviewOpen(false)}
        onSubmit={async (body) => {
          await reviewService.submit(task.id, body);
          setReviewOpen(false);
          await load();
        }}
      />

      {/* ── Dispute modal ────────────────────────────────────────── */}
      <DisputeModal
        open={disputeOpen}
        onClose={() => setDisputeOpen(false)}
        onSubmit={async (reason) => {
          await disputeService.open(task.id, reason);
          setDisputeOpen(false);
          await load();
        }}
      />
    </div>
  );
}

// ── Offer form modal ──────────────────────────────────────────────────────────
function OfferModal({
  open,
  onClose,
  onSubmit,
}: {
  open: boolean;
  onClose: () => void;
  onSubmit: (b: { price: number; message: string; estimated_hours: number }) => Promise<void>;
}) {
  const [price, setPrice] = useState("");
  const [hours, setHours] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await onSubmit({ price: Number(price), estimated_hours: Number(hours), message });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Make an offer">
      <form className={s.form} onSubmit={submit}>
        {error && <p className={s.error}>{error}</p>}
        <div className={s.field}>
          <label className={s.label}>Your price (BGN)</label>
          <input className={s.input} type="number" min={1} value={price}
            onChange={(e) => setPrice(e.target.value)} required />
        </div>
        <div className={s.field}>
          <label className={s.label}>Estimated hours</label>
          <input className={s.input} type="number" min={0.5} step={0.5} value={hours}
            onChange={(e) => setHours(e.target.value)} required />
        </div>
        <div className={s.field}>
          <label className={s.label}>Message to the client</label>
          <textarea className={s.textarea} value={message}
            onChange={(e) => setMessage(e.target.value)} placeholder="Introduce yourself and how you'll help…" required />
        </div>
        <Button type="submit" block disabled={busy}>{busy ? "Sending…" : "Submit offer"}</Button>
      </form>
    </Modal>
  );
}

// ── Review form modal ─────────────────────────────────────────────────────────
function ReviewModal({
  open,
  onClose,
  onSubmit,
}: {
  open: boolean;
  onClose: () => void;
  onSubmit: (b: { rating: number; comment: string }) => Promise<void>;
}) {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await onSubmit({ rating, comment });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Leave a review">
      <form className={s.form} onSubmit={submit}>
        {error && <p className={s.error}>{error}</p>}
        <div className={s.field}>
          <label className={s.label}>Rating</label>
          <div className={s.starPick}>
            {[1, 2, 3, 4, 5].map((n) => (
              <button type="button" key={n} className={`${s.starBtn} ${n <= rating ? s.starOn : ""}`}
                onClick={() => setRating(n)} aria-label={`${n} stars`}>
                <StarIcon size={28} filled={n <= rating} />
              </button>
            ))}
          </div>
        </div>
        <div className={s.field}>
          <label className={s.label}>Comment</label>
          <textarea className={s.textarea} value={comment} minLength={3}
            onChange={(e) => setComment(e.target.value)} placeholder="How did it go?" required />
        </div>
        <Button type="submit" block disabled={busy}>{busy ? "Submitting…" : "Submit review"}</Button>
      </form>
    </Modal>
  );
}

// ── Dispute form modal ────────────────────────────────────────────────────────
function DisputeModal({
  open,
  onClose,
  onSubmit,
}: {
  open: boolean;
  onClose: () => void;
  onSubmit: (reason: string) => Promise<void>;
}) {
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await onSubmit(reason);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Report a problem">
      <form className={s.form} onSubmit={submit}>
        {error && <p className={s.error}>{error}</p>}
        <p className={s.hint} style={{ textAlign: "left" }}>
          Opening a dispute locks the escrow until it&rsquo;s resolved. The other party is notified.
        </p>
        <div className={s.field}>
          <label className={s.label}>What went wrong?</label>
          <textarea
            className={s.textarea}
            value={reason}
            minLength={3}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Describe the issue…"
            required
          />
        </div>
        <Button type="submit" block disabled={busy}>
          {busy ? "Submitting…" : "Open dispute"}
        </Button>
      </form>
    </Modal>
  );
}
