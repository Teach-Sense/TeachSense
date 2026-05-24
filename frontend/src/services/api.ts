import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000, // 30 second timeout
});

// Attach access token to every request
api.interceptors.request.use((config) => {
  const access = localStorage.getItem("accessToken");
  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

// Auto-refresh token on 401 + handle error codes
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const errorCode = error.response?.data?.code;
    const status = error.response?.status;

    // Handle token expiry — refresh and retry
    if (status === 401 && !original._retry &&
        (errorCode === "TOKEN_EXPIRED" || errorCode === "TOKEN_INVALID")) {
      original._retry = true;
      try {
        const refresh = localStorage.getItem("refreshToken");
        const { data } = await axios.post(`${API_BASE_URL}/api/auth/refresh/`, { refresh });
        localStorage.setItem("accessToken", data.access);
        localStorage.setItem("refreshToken", data.refresh);
        original.headers.Authorization = `Bearer ${data.access}`;
        return api(original);
      } catch {
        // Refresh failed — clear storage and redirect to login
        localStorage.clear();
        window.location.href = "/";
      }
    }

    // Handle rate limiting — wait and retry once
    if (status === 429 && !original._rateLimitRetry) {
      original._rateLimitRetry = true;
      const retryAfter = error.response?.headers["retry-after"] || "60";
      await new Promise((res) => setTimeout(res, parseInt(retryAfter) * 1000));
      return api(original);
    }

    // Handle invalid refresh token — force logout
    if (errorCode === "INVALID_REFRESH_TOKEN" || errorCode === "ACCOUNT_DISABLED") {
      localStorage.clear();
      window.location.href = "/";
    }

    return Promise.reject(error);
  }
);

// Helper to extract readable error message from any API error
export const getErrorMessage = (err: any): string => {
  const data = err?.response?.data;
  if (!data) return "Network error. Check your connection.";

  // Validation errors
  if (data.errors) {
    const firstField = Object.keys(data.errors)[0];
    return data.errors[firstField]?.[0] || "Validation failed.";
  }

  return (
    data.detail ||
    data.message ||
    data.non_field_errors?.[0] ||
    "An unexpected error occurred."
  );
};

// ─── Auth ────────────────────────────────────────────────
export const authAPI = {
  login: (email: string, password: string) =>
    api.post("/api/auth/login/", { email, password }),

  logout: () =>
    api.post("/api/auth/logout/", {
      refresh: localStorage.getItem("refreshToken"),
    }),

  getProfile: () => api.get("/api/auth/profile/"),

  updateProfile: (data: { first_name?: string; last_name?: string; email?: string }) =>
    api.put("/api/auth/profile/", data),

  changePassword: (old_password: string, new_password: string) =>
    api.post("/api/auth/change-password/", { old_password, new_password }),
};

// ─── Sessions ────────────────────────────────────────────
export const sessionsAPI = {
  getAll: (status?: string) =>
    api.get("/api/sessions/", { params: status ? { status } : {} }),

  getOne: (id: number) => api.get(`/api/sessions/${id}/`),

  create: (title: string, description?: string) =>
    api.post("/api/sessions/", { title, description }),

  update: (id: number, data: { title?: string; status?: string }) =>
    api.patch(`/api/sessions/${id}/`, data),

  delete: (id: number) => api.delete(`/api/sessions/${id}/`),
};

// ─── Transcripts ─────────────────────────────────────────
export const transcriptsAPI = {
  getAll: (sessionId: number) =>
    api.get("/api/transcripts/", { params: { session_id: sessionId } }),

  create: (sessionId: number, content: string) =>
    api.post("/api/transcripts/", {
      session_id: sessionId,
      content,
      speaker: "lecturer",
      timestamp: new Date().toISOString(),
    }),
};

// ─── Questions ───────────────────────────────────────────
export const questionsAPI = {
  getAll: (sessionId: number) =>
    api.get("/api/questions/", { params: { session_id: sessionId } }),

  create: (sessionId: number, text: string) =>
    api.post("/api/questions/", { session_id: sessionId, text }),

  answer: (id: number, answer: string) =>
    api.put(`/api/questions/${id}/`, { answer, status: "answered" }),
};

// ─── Responses ───────────────────────────────────────────
export const responsesAPI = {
  getAll: (sessionId: number, questionId?: number) =>
    api.get("/api/responses/", {
      params: {
        session_id: sessionId,
        ...(questionId ? { question_id: questionId } : {}),
      },
    }),

  create: (questionId: number, text: string) =>
    api.post("/api/responses/", { question_id: questionId, text }),

  feedback: (id: number, feedback: string, score: number) =>
    api.patch(`/api/responses/${id}/`, { feedback, score }),
};

// ─── Devices ─────────────────────────────────────────────
export const devicesAPI = {
  getAll: () => api.get("/api/devices/"),

  register: (name: string, type: string, protocol: string, device_key: string) =>
    api.post("/api/devices/", { name, type, protocol, device_key }),

  update: (id: number, status: string) =>
    api.patch(`/api/devices/${id}/`, { status }),
};

// ─── Analytics ───────────────────────────────────────────
export const analyticsAPI = {
  getSession: (sessionId: number, metric_type?: string) =>
    api.get("/api/analytics/", {
      params: {
        session_id: sessionId,
        ...(metric_type ? { metric_type } : {}),
      },
    }),
};

// ─── Dashboard ───────────────────────────────────────────
export const dashboardAPI = {
  getAll: () => api.get("/api/dashboards/"),
  getMetrics: (id: number) => api.get(`/api/dashboards/${id}/metrics/`),
};

// ─── Health ──────────────────────────────────────────────
export const healthAPI = {
  check: () => api.get("/api/health/"),
};

export default api;