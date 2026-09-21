import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token!);
    }
  });
  failedQueue = [];
};

// ─── Request Interceptor: attach JWT ───
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem("djs_access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor: auto-refresh on 401 ───
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem("djs_refresh_token");

      // No refresh token — redirect to login
      if (!refreshToken) {
        localStorage.removeItem("djs_access_token");
        localStorage.removeItem("djs_refresh_token");
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Queue the request until token is refreshed
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        });
        const { access_token, refresh_token: newRefreshToken } = response.data;

        localStorage.setItem("djs_access_token", access_token);
        localStorage.setItem("djs_refresh_token", newRefreshToken);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }

        processQueue(null, access_token);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem("djs_access_token");
        localStorage.removeItem("djs_refresh_token");
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;

/**
 * Extract a human-readable error message from any Axios error response.
 * Handles:
 * - App exceptions: { error: { message: "..." } }
 * - FastAPI 422 validation: { detail: [{ msg: "..." }] }
 * - Generic string detail: { detail: "string" }
 */
export function extractApiError(error: unknown): string {
  if (!error || typeof error !== "object") return "An unexpected error occurred.";
  // Plain Error (e.g. guard rejections) — return its message directly
  if (error instanceof Error && !("response" in error)) {
    return error.message || "An unexpected error occurred.";
  }
  const axiosError = error as { response?: { data?: unknown }; message?: string };
  const data = axiosError.response?.data as Record<string, unknown> | undefined;
  if (!data) {
    // True network failure (CORS, server down, etc.)
    return axiosError.message || "Network error. Please check your connection.";
  }
  // App exception format: { error: { message: "..." } }
  if (data.error && typeof (data.error as Record<string, unknown>).message === "string") {
    return (data.error as Record<string, unknown>).message as string;
  }
  // FastAPI default 422 detail array
  if (Array.isArray(data.detail) && data.detail.length > 0) {
    const first = data.detail[0] as Record<string, unknown>;
    const loc = Array.isArray(first.loc) ? first.loc.filter((p: unknown) => p !== "body").join(" → ") : "";
    return loc ? `${loc}: ${first.msg}` : String(first.msg);
  }
  // FastAPI default string detail
  if (typeof data.detail === "string") return data.detail;
  return "An unexpected error occurred.";
}
