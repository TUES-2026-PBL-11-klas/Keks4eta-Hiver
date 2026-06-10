import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { APIProvider } from "@vis.gl/react-google-maps";
import { taskService } from "@/lib/services";
import { paths, VERTICALS } from "@/constants/routes";
import { Button } from "@/components/ui";
import { BoltIcon } from "@/components/icons";
import { VERTICAL_ICON } from "@/components/verticalIcons";
import { AddressAutocomplete } from "@/components/AddressAutocomplete";
import type { Vertical } from "@/types";
import s from "./PostTask.module.css";

// Treat an empty/whitespace key as "no key" so a blank VITE_GOOGLE_MAPS_KEY falls back to a plain input.
const MAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_KEY?.trim() || undefined;

// Vertical-specific "smart" questions. The keyed answers the backend *requires*
// per vertical (home→property_type, learn→subject, tech→device_type) live here;
// omitting them is what used to make POST /tasks 500.
type SmartField = {
  key: string;
  label: string;
  required?: boolean;
  placeholder?: string;
  options?: string[];
};

const SMART_FIELDS: Partial<Record<Vertical, SmartField[]>> = {
  home: [
    {
      key: "property_type",
      label: "Property type",
      required: true,
      options: ["Apartment", "House", "Office", "Garden", "Other"],
    },
  ],
  learn: [
    {
      key: "subject",
      label: "Subject",
      required: true,
      placeholder: "e.g. Mathematics, English, Piano",
    },
  ],
  tech: [
    {
      key: "device_type",
      label: "Device type",
      required: true,
      options: ["Phone", "Laptop", "Desktop", "Tablet", "Smart home", "Other"],
    },
  ],
};

export default function PostTask() {
  const navigate = useNavigate();
  const [vertical, setVertical] = useState<Vertical>("home");
  const [subcategory, setSubcategory] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [budgetMin, setBudgetMin] = useState("");
  const [budgetMax, setBudgetMax] = useState("");
  const [smartAnswers, setSmartAnswers] = useState<Record<string, string>>({});
  const [location, setLocation] = useState("");
  // Coordinates captured when the user picks a Places suggestion (null when typed freehand).
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [urgent, setUrgent] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const smartFields = SMART_FIELDS[vertical] ?? [];

  // Inline budget guard — a max below the min is invalid (mirrors the API rule).
  const budgetInvalid =
    budgetMin !== "" && budgetMax !== "" && Number(budgetMax) < Number(budgetMin);

  function pickVertical(v: Vertical) {
    setVertical(v);
    setSmartAnswers({}); // answers are vertical-specific; drop stale keys
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (budgetInvalid) {
      setError("Maximum budget cannot be lower than the minimum.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      const task = await taskService.create({
        vertical,
        subcategory,
        title,
        description,
        smart_answers: smartAnswers,
        is_urgent: urgent,
        budget_min: budgetMin ? Number(budgetMin) : null,
        budget_max: budgetMax ? Number(budgetMax) : null,
        latitude: lat,
        longitude: lng,
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
                  onClick={() => pickVertical(v.value)}
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

        {smartFields.map((f) => (
          <div className={s.field} key={f.key}>
            <label className={s.label} htmlFor={`sa-${f.key}`}>{f.label}</label>
            {f.options ? (
              <select
                id={`sa-${f.key}`}
                className={s.input}
                value={smartAnswers[f.key] ?? ""}
                required={f.required}
                onChange={(e) =>
                  setSmartAnswers((prev) => ({ ...prev, [f.key]: e.target.value }))
                }
              >
                <option value="" disabled>Select…</option>
                {f.options.map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            ) : (
              <input
                id={`sa-${f.key}`}
                className={s.input}
                value={smartAnswers[f.key] ?? ""}
                required={f.required}
                placeholder={f.placeholder}
                onChange={(e) =>
                  setSmartAnswers((prev) => ({ ...prev, [f.key]: e.target.value }))
                }
              />
            )}
          </div>
        ))}

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
              onChange={(e) => setBudgetMax(e.target.value)} placeholder="Optional"
              aria-invalid={budgetInvalid} />
          </div>
        </div>
        {budgetInvalid && (
          <p className={s.error}>Maximum budget cannot be lower than the minimum.</p>
        )}

        <div className={s.field}>
          <label className={s.label} htmlFor="loc">Location</label>
          {MAPS_KEY ? (
            <APIProvider apiKey={MAPS_KEY}>
              <AddressAutocomplete
                id="loc"
                className={s.input}
                placeholder="Start typing an address…"
                value={location}
                onChange={(t) => {
                  // Freehand edit invalidates any previously picked coordinates.
                  setLocation(t);
                  setLat(null);
                  setLng(null);
                }}
                onPick={(p) => {
                  setLocation(p.display);
                  setLat(p.latitude);
                  setLng(p.longitude);
                }}
              />
            </APIProvider>
          ) : (
            <input id="loc" className={s.input} value={location}
              onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Lozenets, Sofia" />
          )}
        </div>

        <label className={s.toggle}>
          <input type="checkbox" checked={urgent} onChange={(e) => setUrgent(e.target.checked)} />
          <span className={s.toggleText}>
            <strong><BoltIcon size={14} /> Mark as urgent</strong>
            <span>Highlight this task so hivers see it first.</span>
          </span>
        </label>

        <Button type="submit" size="lg" disabled={busy || budgetInvalid}>
          {busy ? "Posting…" : "Post task"}
        </Button>
      </form>
    </div>
  );
}
