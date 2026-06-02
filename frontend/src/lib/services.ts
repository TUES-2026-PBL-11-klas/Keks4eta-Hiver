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
  register: (body: { full_name: string; email: string; password: string; role: string }) =>
    api.post<TokenResponse>("/auth/register", body),
  me: () => api.get<Me>("/users/me"),
};

export interface TaskSearchParams {
  vertical?: Vertical;
  status?: TaskStatus;
  is_urgent?: boolean;
  min_budget?: number;
  max_budget?: number;
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
