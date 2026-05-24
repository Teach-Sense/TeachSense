import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // sends HTTP-only cookies automatically
  headers: { "Content-Type": "application/json" },
});

// ─── Auth ────────────────────────────────────────────────
export const authAPI = {
  login: (email: string, password: string) =>
    api.post("/api/auth/login/", { email, password }),

  register: (name: string, email: string, password: string) =>
    api.post("/api/auth/register/", { name, email, password }),

  logout: () => api.post("/api/auth/logout/"),

  getProfile: () => api.get("/api/auth/profile/"),

  updateProfile: (data: { name?: string; email?: string }) =>
    api.put("/api/auth/profile/", data),

  changePassword: (old_password: string, new_password: string) =>
    api.post("/api/auth/change-password/", { old_password, new_password }),
};

// ─── Sessions ────────────────────────────────────────────
export const sessionsAPI = {
  getAll: () => api.get("/api/sessions/"),

  getOne: (id: number) => api.get(`/api/sessions/${id}/`),

  create: (title: string) => api.post("/api/sessions/", { title }),

  update: (id: number, data: { title?: string; status?: string }) =>
    api.put(`/api/sessions/${id}/`, data),

  delete: (id: number) => api.delete(`/api/sessions/${id}/`),
};

// ─── Transcripts ─────────────────────────────────────────
export const transcriptsAPI = {
  getAll: (sessionId: number) =>
    api.get(`/api/transcripts/sessions/${sessionId}/transcripts/`),

  getOne: (transcriptId: number) =>
    api.get(`/api/transcripts/${transcriptId}/`),

  create: (sessionId: number, content: string) =>
    api.post(`/api/transcripts/sessions/${sessionId}/transcripts/`, { content }),
};

// ─── Questions ───────────────────────────────────────────
export const questionsAPI = {
  getAll: (sessionId: number) =>
    api.get(`/api/questions/sessions/${sessionId}/questions/`),

  getOne: (questionId: number) =>
    api.get(`/api/questions/${questionId}/`),
};

// ─── Responses ───────────────────────────────────────────
export const responsesAPI = {
  getBySession: (sessionId: number) =>
    api.get(`/api/responses/sessions/${sessionId}/responses/`),

  getByQuestion: (sessionId: number, questionId: number) =>
    api.get(
      `/api/responses/sessions/${sessionId}/questions/${questionId}/responses/`
    ),

  create: (sessionId: number, questionId: number, text: string) =>
    api.post(
      `/api/responses/sessions/${sessionId}/questions/${questionId}/responses/`,
      { text }
    ),

  update: (responseId: number, text: string) =>
    api.put(`/api/responses/${responseId}/`, { text }),

  delete: (responseId: number) =>
    api.delete(`/api/responses/${responseId}/`),
};

// ─── Analytics ───────────────────────────────────────────
export const analyticsAPI = {
  getSession: (sessionId: number) =>
    api.get(`/api/analytics/api/sessions/${sessionId}/`),
};

// ─── Dashboard ───────────────────────────────────────────
export const dashboardAPI = {
  getOverview: () => api.get("/api/dashboards/overview/"),
};

// ─── Health ──────────────────────────────────────────────
export const healthAPI = {
  check: () => api.get("/api/health/"),
};

export default api;