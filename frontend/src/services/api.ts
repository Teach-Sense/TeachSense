import axios from "axios";
import type { LecturerInfo } from "../types/session";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach token to every request automatically
api.interceptors.request.use((config) => {
  const info: LecturerInfo | null = JSON.parse(
    localStorage.getItem("lecturerInfo") || "null"
  );
  if (info?.access) {
    config.headers.Authorization = `Bearer ${info.access}`;
  }
  return config;
});

// Auto-refresh token on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const info: LecturerInfo | null = JSON.parse(
          localStorage.getItem("lecturerInfo") || "null"
        );
        const { data } = await axios.post(`${API_BASE_URL}/api/auth/token/refresh/`, {
          refresh: info?.refresh,
        });
        const updated = { ...info, access: data.access };
        localStorage.setItem("lecturerInfo", JSON.stringify(updated));
        original.headers.Authorization = `Bearer ${data.access}`;
        return api(original);
      } catch {
        localStorage.removeItem("lecturerInfo");
        window.location.href = "/";
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth ────────────────────────────────────────────────
export const fetchSampleData = async () => {
  const response = await api.get('/api/'); // adjust endpoint as needed
  return response.data;
};

export const authAPI = {
  login: (email: string, password: string) =>
    api.post("/api/auth/login/", { email, password }),

  register: (name: string, email: string, password: string, password_confirm: string) =>
    api.post("/api/auth/register/", { name, email, password, password_confirm }),

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

  getOne: (responseId: number) =>
    api.get(`/api/responses/${responseId}/`),

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