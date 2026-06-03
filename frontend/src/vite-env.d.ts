/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** API base path/URL. Defaults to "/api/v1". */
  readonly VITE_API_BASE?: string;
  /** Google Maps Platform browser key. When unset, maps/autocomplete fall back gracefully. */
  readonly VITE_GOOGLE_MAPS_KEY?: string;
  /** Optional cloud Map ID (required for AdvancedMarker styling). Defaults to "DEMO_MAP_ID". */
  readonly VITE_GOOGLE_MAPS_MAP_ID?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
