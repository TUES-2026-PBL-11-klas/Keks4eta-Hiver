import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { taskService } from "@/lib/services";
import { paths, VERTICALS } from "@/constants/routes";
import { Button } from "@/components/ui";
import { BoltIcon } from "@/components/icons";
import { VERTICAL_ICON } from "@/components/verticalIcons";
import type { Vertical } from "@/types";
import s from "./PostTask.module.css";

export default function PostTask() {
  const navigate = useNavigate();
  const [vertical, setVertical] = useState<Vertical>("home");
  const [subcategory, setSubcategory] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [budgetMin, setBudgetMin] = useState("");
  const [budgetMax, setBudgetMax] = useState("");
  const [location, setLocation] = useState("");
  const [urgent, setUrgent] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const task = await taskService.create({
        vertical,
        subcategory,
        title,
        description,
        is_urgent: urgent,
        budget_min: budgetMin ? Number(budgetMin) : null,
        budget_max: budgetMax ? Number(budgetMax) : null,
        location_display: location || null,
      });
      navigate(paths.task(task.id));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page-wrap-narrow">
      <header className={s.head}>
        <h1 className={s.title}>Post a task</h1>
        <p className={s.lede}>Tell us what you need and start receiving offers.</p>
      </header>

      <form className={s.form} onSubmit={submit}>
        {error && <p className={s.error}>{error}</p>}

        <div className={s.field}>
          <span className={s.label}>Category</span>
          <div className={s.verticalGrid}>
            {VERTICALS.map((v) => {
              const Icon = VERTICAL_ICON[v.value];
              return (
                <button
                  type="button"
                  key={v.value}
                  className={`${s.vBtn} ${vertical === v.value ? s.vOn : ""}`}
                  onClick={() => setVertical(v.value)}
                >
                  <Icon size={22} />
                  <span className={s.vName}>{v.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className={s.field}>
          <label className={s.label} htmlFor="sub">Subcategory</label>
          <input id="sub" className={s.input} value={subcategory}
            onChange={(e) => setSubcategory(e.target.value)} placeholder="e.g. Deep cleaning" required />
        </div>

        <div className={s.field}>
          <label className={s.label} htmlFor="title">Title</label>
          <input id="title" className={s.input} value={title}
            onChange={(e) => setTitle(e.target.value)} placeholder="Short summary of the job" required />
        </div>

        <div className={s.field}>
          <label className={s.label} htmlFor="desc">Description</label>
          <textarea id="desc" className={s.textarea} value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the task, any requirements, and timing…" required />
        </div>

        <div className={s.row}>
          <div className={s.field}>
            <label className={s.label} htmlFor="bmin">Budget min (BGN)</label>
            <input id="bmin" className={s.input} type="number" min={0} value={budgetMin}
              onChange={(e) => setBudgetMin(e.target.value)} placeholder="Optional" />
          </div>
          <div className={s.field}>
            <label className={s.label} htmlFor="bmax">Budget max (BGN)</label>
            <input id="bmax" className={s.input} type="number" min={0} value={budgetMax}
              onChange={(e) => setBudgetMax(e.target.value)} placeholder="Optional" />
          </div>
        </div>

        <div className={s.field}>
          <label className={s.label} htmlFor="loc">Location</label>
          <input id="loc" className={s.input} value={location}
            onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Lozenets, Sofia" />
        </div>

        <label className={s.toggle}>
          <input type="checkbox" checked={urgent} onChange={(e) => setUrgent(e.target.checked)} />
          <span className={s.toggleText}>
            <strong><BoltIcon size={14} /> Mark as urgent</strong>
            <span>Highlight this task so hivers see it first.</span>
          </span>
        </label>

        <Button type="submit" size="lg" disabled={busy}>
          {busy ? "Posting…" : "Post task"}
        </Button>
      </form>
    </div>
  );
}
