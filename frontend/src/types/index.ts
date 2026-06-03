// ── Shared enums ────────────────────────────────────────────────────────────
export type Role = "client" | "hiver";

export type Vertical = "home" | "learn" | "tech" | "care" | "move" | "events";

export type TaskStatus =
  | "open"
  | "accepted"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "disputed";

export type OfferStatus = "pending" | "accepted" | "rejected";

// ── Auth ──────────────────────────────────────────────────────────────────
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/** Current authenticated user — unified shape returned by GET /users/me. */
export interface Me {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  phone?: string | null;
  avatar_url?: string | null;
  is_oauth: boolean;
  // hiver-only
  bio?: string | null;
  level?: string | null;
  xp_points?: number | null;
  avg_rating?: number | null;
  completed_tasks?: number | null;
  is_available_now?: boolean | null;
  work_radius_km?: number | null;
  skills?: string[];
  // client-only
  rating_as_client?: number | null;
  total_tasks?: number | null;
  review_count?: number | null;
}

// ── Tasks ───────────────────────────────────────────────────────────────────
export interface TaskSummary {
  id: string;
  vertical: Vertical;
  subcategory: string;
  title: string;
  status: TaskStatus;
  is_urgent: boolean;
  budget_min?: number | null;
  budget_max?: number | null;
  location_display?: string | null;
  created_at: string;
}

export interface TaskDetail extends TaskSummary {
  description: string;
  client_id: string;
  hiver_id?: string | null;
  smart_answers: Record<string, unknown>;
  image_urls: string[];
  expires_at?: string | null;
  updated_at: string;
}

export interface CreateTaskBody {
  vertical: Vertical;
  subcategory: string;
  title: string;
  description: string;
  smart_answers?: Record<string, unknown>;
  is_urgent?: boolean;
  budget_min?: number | null;
  budget_max?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  location_display?: string | null;
  image_urls?: string[];
}

// ── Offers ──────────────────────────────────────────────────────────────────
export interface Offer {
  id: string;
  task_id: string;
  hiver_id: string;
  price: number;
  message: string;
  estimated_hours: number;
  status: OfferStatus;
  created_at: string;
}

export interface CreateOfferBody {
  price: number;
  message: string;
  estimated_hours: number;
}

// ── Reviews ───────────────────────────────────────────────────────────────
export interface Review {
  id: string;
  task_id: string;
  reviewer_id: string;
  reviewee_id: string;
  rating: number;
  comment: string;
  is_revealed: boolean;
  created_at: string;
}

export interface SubmitReviewBody {
  rating: number;
  comment: string;
}

// ── Users / profiles ────────────────────────────────────────────────────────
export interface HiverSearchResult {
  user_id: string;
  full_name: string;
  avatar_url?: string | null;
  avg_rating: number;
  level: string;
  completed_tasks: number;
  is_available_now: boolean;
  work_radius_km: number;
  latitude?: number | null;
  longitude?: number | null;
  distance_km?: number | null;
  is_boosted?: boolean;
}

export interface HiverProfile {
  user_id: string;
  full_name: string;
  email: string;
  avatar_url?: string | null;
  bio: string;
  level: string;
  xp_points: number;
  avg_rating: number;
  completed_tasks: number;
  review_count: number;
  is_available_now: boolean;
  work_radius_km: number;
  skills: string[];
  is_boosted?: boolean;
}

export interface ClientProfile {
  user_id: string;
  full_name: string;
  email: string;
  avatar_url?: string | null;
  rating_as_client: number;
  total_tasks: number;
  review_count: number;
}

// ── Generic ─────────────────────────────────────────────────────────────────
export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiError {
  error?: string;
  message: string;
  code?: string;
}
