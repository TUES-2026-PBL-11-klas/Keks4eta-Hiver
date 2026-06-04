import { api } from "@/lib/api";
import type {
  ClientProfile,
  CreateOfferBody,
  CreateTaskBody,
  HiverProfile,
  HiverSearchResult,
  Me,
  Offer,
  Paginated,
  Review,
  SubmitReviewBody,
  TaskDetail,
  TaskStatus,
  TaskSummary,
  TokenResponse,
  UpdateMeBody,
  Vertical,
} from "@/types";

function qs(params: Record<string, unknown>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const authService = {
  login: (email: string, password: string) =>
    api.post<TokenResponse>("/auth/login", { email, password }),
  register: (body: { full_name: string; email: string; password: string }) =>
    api.post<TokenResponse>("/auth/register", body),
  me: () => api.get<Me>("/users/me"),
};

export interface TaskSearchParams {
  vertical?: Vertical;
  status?: TaskStatus;
  is_urgent?: boolean;
  min_budget?: number;
  max_budget?: number;
  /** Free-text over title / description / subcategory. */
  q?: string;
  /** Geo radius search — all three needed together. */
  lat?: number;
  lng?: number;
  radius_km?: number;
  /** "recent" (default) | "distance" | "budget". */
  sort?: "recent" | "distance" | "budget";
  page?: number;
  page_size?: number;
}

export const taskService = {
  search: (params: TaskSearchParams = {}) =>
    api.get<Paginated<TaskSummary>>(`/tasks/search${qs({ ...params })}`),
  get: (id: string) => api.get<TaskDetail>(`/tasks/${id}`),
  create: (body: CreateTaskBody) => api.post<TaskDetail>("/tasks", body),
  myTasks: (page = 1, page_size = 20) =>
    api.get<Paginated<TaskSummary>>(`/tasks${qs({ page, page_size })}`),
  start: (id: string) => api.post<TaskDetail>(`/tasks/${id}/start`),
  complete: (id: string) => api.post<TaskDetail>(`/tasks/${id}/complete`),
  cancel: (id: string) => api.post<TaskDetail>(`/tasks/${id}/cancel`),
  uploadImage: (id: string, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.upload<TaskDetail>(`/tasks/${id}/images`, fd);
  },
};

export const offerService = {
  forTask: (taskId: string) => api.get<Offer[]>(`/tasks/${taskId}/offers`),
  submit: (taskId: string, body: CreateOfferBody) =>
    api.post<Offer>(`/tasks/${taskId}/offers`, body),
  accept: (taskId: string, offerId: string) =>
    api.post<Offer>(`/tasks/${taskId}/offers/${offerId}/accept`),
};

export const reviewService = {
  forTask: (taskId: string, onlyRevealed = true) =>
    api.get<Review[]>(`/tasks/${taskId}/reviews${qs({ only_revealed: onlyRevealed })}`),
  submit: (taskId: string, body: SubmitReviewBody) =>
    api.post<Review>(`/tasks/${taskId}/reviews`, body),
  forUser: (userId: string) => api.get<Review[]>(`/users/${userId}/reviews`),
};

export const userService = {
  hiverProfile: (id: string) => api.get<HiverProfile>(`/users/hivers/${id}`),
  clientProfile: (id: string) => api.get<ClientProfile>(`/users/clients/${id}`),
  nearbyHivers: (params: {
    lat: number;
    lng: number;
    radius_km?: number;
    vertical?: Vertical;
  }) => api.get<HiverSearchResult[]>(`/users/hivers/nearby${qs({ ...params })}`),
  setAvailability: (is_available_now: boolean) =>
    api.patch<HiverProfile>("/users/hivers/me/availability", { is_available_now }),
  /** Edit own profile (partial). Returns the refreshed unified `Me`. */
  updateMe: (body: UpdateMeBody) => api.patch<Me>("/users/me", body),
  uploadAvatar: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.upload<Me>("/users/me/avatar", fd);
  },
};

export interface Boost {
  id: string;
  hiver_id: string;
  vertical: string | null;
  expires_at: string;
  created_at: string;
  is_active: boolean;
  price_bgn: number;
}

export const boostService = {
  mine: () => api.get<Boost | null>("/users/hivers/me/boost"),
  buy: (vertical?: Vertical) =>
    api.post<Boost>("/users/hivers/me/boost", { vertical: vertical ?? null }),
};

export interface Escrow {
  task_id: string;
  status: "held" | "released" | "refunded" | "disputed";
  gross_amount: number;
  platform_fee: number;
  hiver_payout: number;
  created_at: string;
  released_at: string | null;
  refunded_at: string | null;
}

export const paymentService = {
  getEscrow: (taskId: string) => api.get<Escrow | null>(`/payments/tasks/${taskId}`),
  releaseEscrow: (taskId: string) =>
    api.post<{ status: string; hiver_payout: number }>(`/payments/tasks/${taskId}/release`),
};

export interface AppNotification {
  id: string;
  title: string;
  body: string;
  data: Record<string, unknown> | null;
  is_read: boolean;
  sent_at: string;
}

export const notificationService = {
  list: (onlyUnread = false) =>
    api.get<AppNotification[]>(`/notifications${qs({ only_unread: onlyUnread })}`),
  unreadCount: () => api.get<{ unread: number }>("/notifications/unread_count"),
  markRead: (id: string) => api.post<{ ok: boolean }>(`/notifications/${id}/read`),
  markAllRead: () => api.post<{ marked: number }>("/notifications/read-all"),
};

export interface ChatMessage {
  id: string;
  task_id: string;
  sender_id: string;
  content: string;
  is_read: boolean;
  created_at: string;
}

export const messageService = {
  list: (taskId: string) => api.get<ChatMessage[]>(`/tasks/${taskId}/messages`),
  send: (taskId: string, content: string) =>
    api.post<ChatMessage>(`/tasks/${taskId}/messages`, { content }),
};

export interface Dispute {
  id: string;
  task_id: string;
  opened_by_id: string;
  reason: string;
  status: "open" | "resolved" | "refunded";
  admin_note: string | null;
  created_at: string;
  resolved_at: string | null;
}

export const disputeService = {
  get: (taskId: string) => api.get<Dispute | null>(`/tasks/${taskId}/disputes`),
  open: (taskId: string, reason: string) =>
    api.post<Dispute>(`/tasks/${taskId}/disputes`, { reason }),
  resolve: (taskId: string, note?: string) =>
    api.post<Dispute>(`/tasks/${taskId}/disputes/resolve`, { note }),
};
