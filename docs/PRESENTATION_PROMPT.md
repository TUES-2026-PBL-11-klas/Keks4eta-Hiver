# Presentation prompt — paste into Claude (Artifacts)

Copy everything between the lines into Claude and let it build the artifact. It produces a polished,
self-contained **HTML slide presentation** about the Hiver product + system, with an **architecture
chart**, a **database diagram**, and **icons** throughout. It intentionally does **not** mention
school subjects or grading — it reads like a product + engineering showcase.

---

Build me a **single self-contained HTML file** (inline CSS + JS, no external build step) that is a
**slide-deck presentation** for a product called **Hiver**. It must look like a premium startup +
engineering showcase: clean, modern, confident. Use **embedded SVG diagrams** (or Mermaid via CDN) for
the architecture and database slides, and a consistent **icon set** (inline SVG icons, e.g. Lucide-style)
on every slide. Make it keyboard-navigable (← / → arrows) with a slide counter, a subtle progress bar,
and smooth transitions. Mobile-responsive. No external images.

**Visual identity ("The Hive"):**
- Colours: honey/amber accent `#EE7F22`, deep navy ink `#00224F`, warm paper background `#FBEFE0`,
  white cards. Use honey sparingly for emphasis.
- Fonts (Google Fonts CDN): **Fraunces** for headings, **Hanken Grotesk** for body, **Space Mono** for
  labels/numbers/code.
- Motif: subtle **hexagon / honeycomb** accents. Generous whitespace, rounded cards, soft shadows.

**What Hiver is (use this content):** a two-sided **local-services marketplace**. People post everyday
real-world tasks — cleaning, tutoring, tech help, moving, pet/child care, event help — and nearby
vetted helpers ("hivers") bid on them. The client picks an offer, pays into **escrow**, the hiver does
the job, and funds release on completion. Every account is **both** a client and a hiver. Trust comes
from **two-way blind reviews**, **escrow-protected payments**, **map-based discovery**, and **in-app
chat**. Tagline: *"Real help. Nearby. With trust built in."*

**Build these slides (≈15):**
1. **Title** — "Hiver — real help, nearby, with trust built in." Hexagon motif, tagline, a row of
   category icons (home, tutoring, tech, moving, care, events).
2. **The problem** — finding trustworthy local help is fragmented (scattered groups/ads), no reputation,
   no payment protection, no way to see who's nearby. Use 4 icon cards.
3. **The solution** — one app: post a task → nearby helpers bid → pay into escrow → chat → done → review.
   A clean value statement + 3–4 icon highlights (reputation, escrow, proximity, chat).
4. **How it works** — a horizontal **flow diagram** with icons:
   `Post task → Offers → Accept (escrow holds) → Chat → Complete → Release → Reviews`.
5. **Key features** — an icon grid: map discovery + address autocomplete, real-time chat, escrow &
   disputes, paid visibility boosts, favourites, in-app notifications, gamified hiver levels
   (beginner→legend).
6. **Map & location** — proximity search: helpers and tasks shown as pins; "find work within X km";
   real addresses via autocomplete. Stylised map illustration with pins (SVG).
7. **Architecture (CHART — make this great)** — a layered **diagram** showing **Clean Architecture**
   with dependencies pointing inward:
   `HTTP / API layer  →  Application (use cases)  →  Domain (core business rules)`, and
   `Infrastructure (database, payments, storage, maps)` plugging into the Domain via **interfaces
   (ports & adapters)**. Annotate that providers (payments, storage) are swappable adapters. Render as
   concentric rings or stacked layers with arrows + small icons per layer.
8. **Request lifecycle** — a sequence-style mini-diagram: Browser → API → use case → domain rules →
   repository → PostgreSQL, and the response back. Icons + arrows.
9. **Data model (CHART — make this great)** — an **entity-relationship diagram** of the core tables and
   relationships: **User** (→ Client / Hiver), **Task** (has a geo location point), **Offer**,
   **Transaction/Escrow**, **Review**, **Message**, **Dispute**, **Boost**, **Favorite**. Show
   one-to-many / many-to-many links (e.g. Task 1—* Offer; Hiver *—* Skill). Use boxes with key fields +
   connecting lines. Note the geospatial point on Task/Hiver.
10. **Geospatial engine** — PostgreSQL + PostGIS: location stored as geographic points; "find helpers
    within a radius" via an indexed proximity query. A small map-pin + radius illustration.
11. **Trust & payments** — escrow (hold → release / refund), two-way **blind reviews** (revealed only
    when both sides submit), dispute resolution. Shield + handshake icons.
12. **Real-time & messaging** — WebSocket live chat between client and assigned hiver, in-app
    notification feed. Chat-bubble icons + a tiny live-update illustration.
13. **Tech stack** — two columns with **brand-style icons**: Backend (Python · FastAPI · PostgreSQL +
    PostGIS · Redis · SQLAlchemy) and Frontend (React · TypeScript · Vite · Google Maps). Add a
    DevOps/infra strip: Docker · Kubernetes · Prometheus · Grafana · GitHub Actions.
14. **Reliability & observability** — containerised + orchestrated; metrics scraped into Prometheus and
    visualised in a Grafana dashboard (request rate, error rate, latency); rate-limiting + JWT auth.
    Small gauge/graph icons.
15. **Roadmap & close** — what's next (real card payments, mobile push, admin console, native mobile
    app) and a confident closing line + the tagline. Hexagon flourish.

**Requirements:** real, rendered diagrams on slides 4, 7, 8, 9 (not just bullet lists) — use inline SVG
or Mermaid. Every slide has at least one icon. Keep copy tight (headlines + short bullets). One
cohesive style across all slides. Output the **complete HTML in a single artifact** I can open in a
browser and present full-screen.

---

> Tip: if you'd rather have a Canva deck instead of an HTML artifact, there's a separate
> `docs/CANVA_DECK_PROMPT.md`. This prompt is the product-only version (no subject framing) and asks
> for rendered architecture + database diagrams.
