export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  REGISTER: "/register",
  AUTH_CALLBACK: "/auth/callback",
  TASKS: "/tasks",
  TASK_DETAIL: "/tasks/:id",
  POST_TASK: "/post",
  DASHBOARD: "/dashboard",
  HIVERS: "/hivers",
  FAVORITES: "/saved",
  PROFILE: "/profile",
  SETTINGS: "/settings",
  HIVER_PROFILE: "/hivers/:id",
  CLIENT_PROFILE: "/clients/:id",
} as const;

// Path builders for parameterized routes.
export const paths = {
  task: (id: string) => `/tasks/${id}`,
  hiver: (id: string) => `/hivers/${id}`,
  client: (id: string) => `/clients/${id}`,
};

export const VERTICALS = [
  { value: "home", label: "Home", blurb: "Cleaning, repairs, moving help" },
  { value: "learn", label: "Learn", blurb: "Tutoring & lessons" },
  { value: "tech", label: "Tech", blurb: "Devices, setup, support" },
  { value: "care", label: "Care", blurb: "Pets, kids, seniors" },
  { value: "move", label: "Move", blurb: "Transport & delivery" },
  { value: "events", label: "Events", blurb: "Help hosting & catering" },
] as const;
