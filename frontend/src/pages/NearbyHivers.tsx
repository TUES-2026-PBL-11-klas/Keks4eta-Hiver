import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { APIProvider, Map, AdvancedMarker, Pin, useMap } from "@vis.gl/react-google-maps";
import { userService } from "@/lib/services";
import { paths, VERTICALS } from "@/constants/routes";
import { Avatar, Badge, Button, Card, EmptyState, Skeleton, Stars } from "@/components/ui";
import { Reveal } from "@/components/Reveal";
import { PinIcon, Hexagon } from "@/components/icons";
import type { HiverSearchResult, Vertical } from "@/types";
import s from "./NearbyHivers.module.css";

// Default to central Sofia until the user shares their location.
const DEFAULT_COORDS = { lat: 42.6977, lng: 23.3219 };
const MAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_KEY;
const MAP_ID = import.meta.env.VITE_GOOGLE_MAPS_MAP_ID || "DEMO_MAP_ID";

// Pans the map whenever the search coordinates change (e.g. "Use my location").
function Recenter({ coords }: { coords: { lat: number; lng: number } }) {
  const map = useMap();
  useEffect(() => {
    if (map) map.panTo(coords);
  }, [map, coords]);
  return null;
}

export default function NearbyHivers() {
  const navigate = useNavigate();
  const [coords, setCoords] = useState(DEFAULT_COORDS);
  const [radius, setRadius] = useState(10);
  const [vertical, setVertical] = useState<Vertical | "">("");
  const [hivers, setHivers] = useState<HiverSearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    userService
      .nearbyHivers({
        lat: coords.lat,
        lng: coords.lng,
        radius_km: radius,
        vertical: vertical || undefined,
      })
      .then(setHivers)
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, [coords, radius, vertical]);

  useEffect(() => {
    load();
  }, [load]);

  function useMyLocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setError("Couldn't get your location — showing Sofia."),
    );
  }

  // Keyless fallback: a free OpenStreetMap embed (bbox + center marker), used when
  // VITE_GOOGLE_MAPS_KEY is not set so the page still works for teammates without a key.
  const latDelta = radius / 111;
  const lngDelta = radius / (111 * Math.cos((coords.lat * Math.PI) / 180));
  const bbox = [
    coords.lng - lngDelta,
    coords.lat - latDelta,
    coords.lng + lngDelta,
    coords.lat + latDelta,
  ].join(",");
  const osmSrc =
    `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}` +
    `&layer=mapnik&marker=${coords.lat},${coords.lng}`;

  const pinnable = hivers.filter((h) => h.latitude != null && h.longitude != null);

  return (
    <div className="page-wrap">
      <header className={s.head}>
        <div>
          <h1 className={s.title}>Hivers near you</h1>
          <p className={s.lede}>Available helpers within {radius} km.</p>
        </div>
        <Button variant="secondary" size="sm" onClick={useMyLocation}>
          <PinIcon size={16} /> Use my location
        </Button>
      </header>

      <div className={s.controls}>
        <select
          className={s.select}
          value={vertical}
          onChange={(e) => setVertical(e.target.value as Vertical | "")}
        >
          <option value="">All categories</option>
          {VERTICALS.map((v) => (
            <option key={v.value} value={v.value}>{v.label}</option>
          ))}
        </select>
        <select className={s.select} value={radius} onChange={(e) => setRadius(Number(e.target.value))}>
          {[2, 5, 10, 15, 20].map((r) => (
            <option key={r} value={r}>{r} km</option>
          ))}
        </select>
      </div>

      <div className={s.mapWrap}>
        {MAPS_KEY ? (
          <APIProvider apiKey={MAPS_KEY}>
            <Map
              className={s.map}
              mapId={MAP_ID}
              defaultCenter={coords}
              defaultZoom={12}
              gestureHandling="greedy"
              clickableIcons={false}
            >
              <Recenter coords={coords} />
              {/* "You are here" — the search center. */}
              <AdvancedMarker position={coords} title="Search center">
                <div className={s.meDot} />
              </AdvancedMarker>
              {pinnable.map((h) => (
                <AdvancedMarker
                  key={h.user_id}
                  position={{ lat: h.latitude as number, lng: h.longitude as number }}
                  title={h.full_name}
                  onClick={() => navigate(paths.hiver(h.user_id))}
                >
                  <Pin
                    background={h.is_boosted ? "#FBBC04" : "#1B1B1F"}
                    glyphColor={h.is_boosted ? "#1B1B1F" : "#FBBC04"}
                    borderColor={h.is_boosted ? "#1B1B1F" : "#FBBC04"}
                  />
                </AdvancedMarker>
              ))}
            </Map>
          </APIProvider>
        ) : (
          <iframe
            title="Search area map"
            className={s.map}
            src={osmSrc}
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
          />
        )}
      </div>

      {loading && (
        <div className={s.grid}>
          {[0, 1, 2, 3].map((i) => <Skeleton key={i} height={92} radius={22} />)}
        </div>
      )}

      {!loading && error && (
        <EmptyState icon={<Hexagon size={28} />} title="Couldn't load hivers">{error}</EmptyState>
      )}

      {!loading && !error && hivers.length === 0 && (
        <EmptyState icon={<Hexagon size={28} fill="currentColor" />} title="No hivers available here">
          Try a larger radius or a different category.
        </EmptyState>
      )}

      {!loading && !error && hivers.length > 0 && (
        <div className={s.grid}>
          {hivers.map((h, i) => (
            <Reveal key={h.user_id} delay={Math.min(i, 6) * 0.04}>
              <Link to={paths.hiver(h.user_id)} style={{ display: "block", height: "100%" }}>
                <Card hover className={s.hiver}>
                  <Avatar name={h.full_name} src={h.avatar_url} size={56} />
                  <div className={s.info}>
                    <span className={s.name}>{h.full_name}</span>
                    <div className={s.statRow}>
                      <Stars value={h.avg_rating} size={14} />
                      <Badge tone="muted">{h.level}</Badge>
                      {h.is_boosted && <Badge tone="honey">★ Boosted</Badge>}
                    </div>
                    <div className={s.statRow}>
                      {h.is_available_now && <span className={s.dot} />}
                      <span className={s.dist}>
                        {h.distance_km != null ? `${h.distance_km.toFixed(1)} km away` : `${h.completed_tasks} jobs done`}
                      </span>
                    </div>
                  </div>
                </Card>
              </Link>
            </Reveal>
          ))}
        </div>
      )}
    </div>
  );
}
