export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "client" | "hiver";
  avatar_url?: string;
}

export interface Task {
  id: string;
  vertical: string;
  subcategory: string;
  status: "open" | "in_progress" | "completed" | "cancelled";
  budget_min?: number;
  budget_max?: number;
  is_urgent: boolean;
  location_display?: string;
  created_at: string;
}

export interface Offer {
  id: string;
  task_id: string;
  hiver_id: string;
  price: number;
  message: string;
  status: "pending" | "accepted" | "rejected";
  created_at: string;
}

export interface ApiError {
  error: string;
  message: string;
}
