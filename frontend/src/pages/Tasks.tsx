import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { APIProvider, Map, AdvancedMarker, Pin, useMap } from "@vis.gl/react-google-maps";
import { taskService } from "@/lib/services";
import { paths, VERTICALS } from "@/constants/routes";
import { TaskCard } from "@/components/TaskCard";
import { Button, EmptyState, Skeleton } from "@/components/ui";
import { Reveal } from "@/components/Reveal";
import { BoltIcon, Hexagon, PinIcon, SearchIcon } from "@/components/icons";
import type { Paginated, TaskSummary, Vertical } from "@/types";
import s from "./Tasks.module.css";

const cx = (...c: (string | false)[]) => c.filter(Boolean).join(" ");

// Map of TASKS to do (not hivers) — the discovery view for people looking for work.
const DEFAULT_COORDS = { lat: 42.6977, lng: 23.3219 }; // central Sofia
// Treat an empty/whitespace key as "no key" so a blank VITE_GOOGLE_MAPS_KEY falls back to OSM.
const MAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_KEY?.trim() || undefined;
const MAP_ID = import.meta.env.VITE_GOOGLE_MAPS_MAP_ID || "DEMO_MAP_ID";

type SortKey = "recent" | "distance" | "budget";

function Recenter({ coords }: { coords: { lat: number; lng: number } }) {
  const map = useMap();
  useEffect(() => {
    if (map) map.panTo(coords);
  }, [map, coords]);
  return null;
}

export default function Tasks() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Applied filters (drive the query). Free-text + budget apply on submit;
  // category / urgent / sort / radius / location apply immediately.
  // Seed the category from ?vertical= so Home's category cards land here pre-filtered.
  const [vertical, setVertical] = useState<Vertical | "">(() => {
    const v = searchParams.get("vertical");
    return VERTICALS.some((x) => x.value === v) ? (v as Vertical) : "";
  });
  const [urgentOnly, setUrgentOnly] = useState(false);
  const [sort, setSort] = useState<SortKey>("recent");
  const [radius, setRadius] = useState(10);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [appliedQ, setAppliedQ] = useState("");
  const [appliedMin, setAppliedMin] = useState("");
  const [appliedMax, setAppliedMax] = useState("");
  const [page, setPage] = useState(1);

  // Pending form inputs.
  const [q, setQ] = useState("");
  const [minBudget, setMinBudget] = useState("");
  const [maxBudget, setMaxBudget] = useState("");

  const [data, setData] = useState<Paginated<TaskSummary> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    taskService
      .search({
        status: "open",
        vertical: vertical || undefined,
        is_urgent: urgentOnly || undefined,
        q: appliedQ || undefined,
        min_budget: appliedMin ? Number(appliedMin) : undefined,
        max_budget: appliedMax ? Number(appliedMax) : undefined,
        lat: coords?.lat,
        lng: coords?.lng,
        radius_km: coords ? radius : undefined,
        sort,
        page,
        page_size: 12,
      })
      .then((res) => active && setData(res))
      .catch((e) => active && setError((e as Error).message))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [vertical, urgentOnly, sort, radius, coords, appliedQ, appliedMin, appliedMax, page]);

  function pickVertical(v: Vertical | "") {
    setVertical(v);
    setPage(1);
  }
  function toggleUrgent() {
    setUrgentOnly((u) => !u);
    setPage(1);
  }
  function applyFilters(e: FormEvent) {
    e.preventDefault();
    setAppliedQ(q.trim());
    setAppliedMin(minBudget);
    setAppliedMax(maxBudget);
    setPage(1);
  }
  function useMyLocation() {
    if (!navigator.geolocation) {
      setError("Geolocation isn't available in this browser.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        if (sort === "recent") setSort("distance");
        setPage(1);
      },
      () => setError("Couldn't get your location."),
    );
  }

  const items = data?.items ?? [];
  const pinnable = items.filter((t) => t.latitude != null && t.longitude != null);
  const mapCenter = coords ?? DEFAULT_COORDS;

  // Keyless OSM fallback bbox (used when there is no Google Maps key).
  const latDelta = radius / 111;
  const lngDelta = radius / (111 * Math.cos((mapCenter.lat * Math.PI) / 180));
  const bbox = [
    mapCenter.lng - lngDelta,
    mapCenter.lat - latDelta,
    mapCenter.lng + lngDelta,
    mapCenter.lat + latDelta,
  ].join(",");
  const osmSrc =
    `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}` +
    `&layer=mapnik&marker=${mapCenter.lat},${mapCenter.lng}`;

  return (
    <div className="page-wrap">
      <header className={s.head}>
        <p className={s.eyebrow}>Marketplace</p>
        <h1 className={s.title}>Find tasks</h1>
        <p className={s.count}>
          {loading
            ? "Searching…"
            : `${data?.total ?? 0} open task${data?.total === 1 ? "" : "s"}${coords ? ` within ${radius} km` : ""}`}
        </p>
      </header>

      <div className={s.toolbar}>
        <form className={s.searchRow} onSubmit={applyFilters}>
          <input
            className={s.searchInput}
            placeholder="Search tasks — e.g. plumbing, math tutor, move sofa…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <input
            className={s.budgetInput}
            type="number"
            min={0}
            placeholder="Min BGN"
            value={minBudget}
            onChange={(e) => setMinBudget(e.target.value)}
          />
          <input
            className={s.budgetInput}
            type="number"
            min={0}
            placeholder="Max BGN"
            value={maxBudget}
            onChange={(e) => setMaxBudget(e.target.value)}
          />
          <Button type="submit" size="md">
            <SearchIcon size={16} /> Search
          </Button>
        </form>

        <div className={s.controls}>
          <select
            className={s.select}
            value={sort}
            onChange={(e) => { setSort(e.target.value as SortKey); setPage(1); }}
          >
            <option value="recent">Newest first</option>
            <option value="distance">Nearest first</option>
            <option value="budget">Highest budget</option>
          </select>
          <select
            className={s.select}
            value={radius}
            onChange={(e) => { setRadius(Number(e.target.value)); setPage(1); }}
            disabled={!coords}
            title={coords ? undefined : "Use your location to filter by radius"}
          >
            {[2, 5, 10, 15, 20, 50].map((r) => (
              <option key={r} value={r}>{r} km</option>
            ))}
          </select>
          <Button variant="secondary" size="sm" onClick={useMyLocation}>
            <PinIcon size={15} /> {coords ? "Update location" : "Near me"}
          </Button>
          {coords && (
            <button
              type="button"
              className={s.chip}
              onClick={() => { setCoords(null); setPage(1); }}
            >
              Clear location
            </button>
          )}
        </div>
      </div>

      <div className={s.filters}>
        <button className={cx(s.chip, !vertical && s.chipOn)} onClick={() => pickVertical("")}>
          All
        </button>
        {VERTICALS.map((v) => (
          <button
            key={v.value}
            className={cx(s.chip, vertical === v.value && s.chipOn)}
            onClick={() => pickVertical(v.value)}
          >
            {v.label}
          </button>
        ))}
        <span className={s.divider} />
        <button className={cx(s.chip, urgentOnly && s.chipOn)} onClick={toggleUrgent}>
          <BoltIcon size={14} /> Urgent
        </button>
      </div>

      <div className={s.mapWrap}>
        {MAPS_KEY ? (
          <APIProvider apiKey={MAPS_KEY}>
            <Map
              className={s.map}
              mapId={MAP_ID}
              defaultCenter={mapCenter}
              defaultZoom={12}
              gestureHandling="greedy"
              clickableIcons={false}
            >
              <Recenter coords={mapCenter} />
              {coords && (
                <AdvancedMarker position={coords} title="Your location">
                  <div className={s.meDot} />
                </AdvancedMarker>
              )}
              {pinnable.map((t) => (
                <AdvancedMarker
                  key={t.id}
                  position={{ lat: t.latitude as number, lng: t.longitude as number }}
                  title={t.title}
                  onClick={() => navigate(paths.task(t.id))}
                >
                  <Pin
                    background={t.is_urgent ? "#c8462f" : "#EE7F22"}
                    glyphColor="#fff"
                    borderColor="#fff"
                  />
                </AdvancedMarker>
              ))}
            </Map>
          </APIProvider>
        ) : (
          <iframe
            title="Tasks area map"
            className={s.map}
            src={osmSrc}
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
          />
        )}
      </div>

      {loading && (
        <div className={s.grid}>
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className={s.skel} height={120} radius={22} />
          ))}
        </div>
      )}

      {!loading && error && (
        <EmptyState icon={<Hexagon size={28} />} title="Couldn't load tasks">
          {error}
        </EmptyState>
      )}

      {!loading && !error && items.length === 0 && (
        <EmptyState icon={<Hexagon size={28} fill="currentColor" />} title="The hive's quiet here">
          No open tasks match these filters yet — try widening your radius, clearing filters, or check back soon.
        </EmptyState>
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <div className={s.grid}>
            {items.map((task, i) => (
              <Reveal key={task.id} delay={Math.min(i, 6) * 0.04}>
                <TaskCard task={task} />
              </Reveal>
            ))}
          </div>

          {data!.total > data!.page_size && (
            <div className={s.pager}>
              <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Previous
              </Button>
              <span>Page {data!.page} of {Math.max(1, Math.ceil(data!.total / data!.page_size))}</span>
              <Button
                variant="secondary"
                size="sm"
                disabled={page * data!.page_size >= data!.total}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
