import { useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { useNavigate } from "react-router-dom";
import { APIProvider } from "@vis.gl/react-google-maps";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";
import { userService } from "@/lib/services";
import { Avatar, Button, Card } from "@/components/ui";
import { ArrowLeftIcon, CloseIcon } from "@/components/icons";
import { AddressAutocomplete } from "@/components/AddressAutocomplete";
import type { UpdateMeBody } from "@/types";
import s from "./Settings.module.css";

// Treat an empty/whitespace key as "no key" so a blank VITE_GOOGLE_MAPS_KEY falls back to a plain input.
const MAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_KEY?.trim() || undefined;
// Mirrors the WorkRadius value object's allowed tiers (backend rejects others).
const RADII = [1, 2, 5, 10, 15, 20];
const MAX_SKILLS = 12;

export default function Settings() {
  const navigate = useNavigate();
  const { user, refresh } = useAuth();

  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [bio, setBio] = useState(user?.bio ?? "");
  const [skills, setSkills] = useState<string[]>(user?.skills ?? []);
  const [skillDraft, setSkillDraft] = useState("");
  const [radius, setRadius] = useState<number>(user?.work_radius_km ?? 5);
  const [location, setLocation] = useState(user?.location_display ?? "");
  const [lat, setLat] = useState<number | null>(user?.latitude ?? null);
  const [lng, setLng] = useState<number | null>(user?.longitude ?? null);

  const [saving, setSaving] = useState(false);
  const [avatarBusy, setAvatarBusy] = useState(false);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  if (!user) return null; // guarded by ProtectedRoute

  function addSkill(raw: string) {
    const name = raw.trim();
    if (!name) return;
    setSkills((prev) =>
      prev.length >= MAX_SKILLS || prev.some((p) => p.toLowerCase() === name.toLowerCase())
        ? prev
        : [...prev, name],
    );
    setSkillDraft("");
  }

  function onSkillKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addSkill(skillDraft);
    } else if (e.key === "Backspace" && !skillDraft && skills.length) {
      setSkills((prev) => prev.slice(0, -1));
    }
  }

  async function onAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-picking the same file
    if (!file) return;
    setError("");
    setOk("");
    setAvatarBusy(true);
    try {
      await userService.uploadAvatar(file);
      await refresh();
      setOk("Photo updated.");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setAvatarBusy(false);
    }
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setOk("");
    // Commit any skill still sitting in the input.
    const finalSkills = skillDraft.trim()
      ? [...skills, skillDraft.trim()].slice(0, MAX_SKILLS)
      : skills;
    setSaving(true);
    try {
      const body: UpdateMeBody = {
        full_name: fullName.trim(),
        phone: phone.trim(),
        bio,
        skills: finalSkills,
        work_radius_km: radius,
      };
      // Only send coordinates when we actually have a picked point — otherwise
      // the stored location is left untouched (matches the PATCH semantics).
      if (lat != null && lng != null) {
        body.latitude = lat;
        body.longitude = lng;
        body.location_display = location || null;
      }
      await userService.updateMe(body);
      await refresh();
      setSkills(finalSkills);
      // Saving should leave the edit menu — return to the profile (which now shows the changes).
      navigate(ROUTES.PROFILE);
      return;
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page-wrap-narrow">
      <header className={s.head}>
        <Button variant="ghost" size="sm" onClick={() => navigate(ROUTES.PROFILE)}>
          <ArrowLeftIcon size={16} /> Back to profile
        </Button>
        <h1 className={s.title}>Edit profile</h1>
        <p className={s.lede}>Update how you appear to clients and hivers.</p>
      </header>

      <form className={s.form} onSubmit={submit}>
        {error && <p className={s.error}>{error}</p>}
        {ok && <p className={s.ok}>{ok}</p>}

        {/* ── Photo ───────────────────────────────────────────── */}
        <Card>
          <div className={s.avatarRow}>
            <Avatar name={user.full_name} src={user.avatar_url} size={72} />
            <div className={s.avatarMeta}>
              <span className={s.label}>Profile photo</span>
              <span className={s.hint}>JPEG, PNG, WebP or GIF · up to 3 MB</span>
              <div>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  disabled={avatarBusy}
                  onClick={() => fileRef.current?.click()}
                >
                  {avatarBusy ? "Uploading…" : "Change photo"}
                </Button>
              </div>
              <input
                ref={fileRef}
                type="file"
                accept="image/png,image/jpeg,image/webp,image/gif"
                className={s.hiddenFile}
                onChange={onAvatarChange}
              />
            </div>
          </div>
        </Card>

        {/* ── Basics ──────────────────────────────────────────── */}
        <section className={s.section}>
          <h2 className={s.sectionTitle}>Basics</h2>
          <div className={s.row}>
            <div className={s.field}>
              <label className={s.label} htmlFor="name">Full name</label>
              <input id="name" className={s.input} value={fullName}
                onChange={(e) => setFullName(e.target.value)} required maxLength={120} />
            </div>
            <div className={s.field}>
              <label className={s.label} htmlFor="phone">Phone</label>
              <input id="phone" className={s.input} value={phone}
                onChange={(e) => setPhone(e.target.value)} placeholder="Optional" maxLength={40} />
            </div>
          </div>
          <div className={s.field}>
            <label className={s.label} htmlFor="bio">About you</label>
            <textarea id="bio" className={s.textarea} value={bio}
              onChange={(e) => setBio(e.target.value)} maxLength={1000}
              placeholder="A short intro clients see on your hiver profile…" />
          </div>
        </section>

        {/* ── Work ────────────────────────────────────────────── */}
        <section className={s.section}>
          <h2 className={s.sectionTitle}>Work as a hiver</h2>

          <div className={s.field}>
            <label className={s.label} htmlFor="skill">Skills</label>
            <div className={s.tags}>
              {skills.map((sk) => (
                <span key={sk} className={s.tag}>
                  {sk}
                  <button type="button" className={s.tagX} aria-label={`Remove ${sk}`}
                    onClick={() => setSkills((prev) => prev.filter((p) => p !== sk))}>
                    <CloseIcon size={12} />
                  </button>
                </span>
              ))}
              <input
                id="skill"
                className={s.tagInput}
                value={skillDraft}
                onChange={(e) => setSkillDraft(e.target.value)}
                onKeyDown={onSkillKey}
                onBlur={() => addSkill(skillDraft)}
                placeholder={skills.length ? "Add another…" : "e.g. Plumbing, Tutoring"}
              />
            </div>
            <span className={s.hint}>Press Enter or comma to add. Up to {MAX_SKILLS}.</span>
          </div>

          <div className={s.row}>
            <div className={s.field}>
              <label className={s.label} htmlFor="radius">Work radius</label>
              <select id="radius" className={s.select} value={radius}
                onChange={(e) => setRadius(Number(e.target.value))}>
                {RADII.map((r) => (
                  <option key={r} value={r}>{r} km</option>
                ))}
              </select>
            </div>
            <div className={s.field}>
              <label className={s.label} htmlFor="loc">Base location</label>
              {MAPS_KEY ? (
                <APIProvider apiKey={MAPS_KEY}>
                  <AddressAutocomplete
                    id="loc"
                    className={s.input}
                    placeholder="Start typing an address…"
                    value={location}
                    onChange={(t) => {
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
          </div>
          <span className={s.hint}>
            Your base location and radius decide which nearby tasks and clients can find you.
          </span>
        </section>

        <div className={s.actions}>
          <Button type="submit" size="lg" disabled={saving}>
            {saving ? "Saving…" : "Save changes"}
          </Button>
          <Button type="button" variant="ghost" onClick={() => navigate(ROUTES.PROFILE)}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
