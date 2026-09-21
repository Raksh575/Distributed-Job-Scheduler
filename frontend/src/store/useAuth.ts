import { create } from "zustand";
import authService from "../services/auth.service";

import { UserResponse } from "../services/auth.service";

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  userEmail: string | null;
  userId: string | null;
  userInfo: UserResponse | null;
  login: (token: string, refreshToken: string, email: string, userId: string, userInfo?: UserResponse) => void;
  logout: () => Promise<void>;
  setUserInfo: (email: string, userInfo: UserResponse) => void;
}

export const useAuth = create<AuthState>((set, get) => {
  const savedToken = localStorage.getItem("djs_access_token");
  const savedRefresh = localStorage.getItem("djs_refresh_token");
  const savedEmail = localStorage.getItem("djs_user_email");
  const savedUserId = localStorage.getItem("djs_user_id");
  const savedUserInfo = localStorage.getItem("djs_user_info");
  const parsedUserInfo = savedUserInfo ? JSON.parse(savedUserInfo) : null;

  return {
    token: savedToken,
    refreshToken: savedRefresh,
    isAuthenticated: !!savedToken,
    isLoading: false,
    userEmail: savedEmail,
    userId: savedUserId,
    userInfo: parsedUserInfo,

    login: (token, refreshToken, email, userId, userInfo) => {
      localStorage.setItem("djs_access_token", token);
      localStorage.setItem("djs_refresh_token", refreshToken);
      localStorage.setItem("djs_user_email", email);
      localStorage.setItem("djs_user_id", userId);
      if (userInfo) localStorage.setItem("djs_user_info", JSON.stringify(userInfo));
      set({ token, refreshToken, isAuthenticated: true, userEmail: email, userId, userInfo: userInfo || null });
    },

    logout: async () => {
      const currentRefreshToken = get().refreshToken;
      if (currentRefreshToken) {
        try {
          await authService.logout(currentRefreshToken);
        } catch {
          // Ignore logout errors — clear state regardless
        }
      }
      localStorage.removeItem("djs_access_token");
      localStorage.removeItem("djs_refresh_token");
      localStorage.removeItem("djs_user_email");
      localStorage.removeItem("djs_user_id");
      localStorage.removeItem("djs_user_info");
      localStorage.removeItem("djs_active_org_id");
      set({ token: null, refreshToken: null, isAuthenticated: false, userEmail: null, userId: null, userInfo: null });
      window.location.href = "/login";
    },

    setUserInfo: (email, userInfo) => {
      localStorage.setItem("djs_user_email", email);
      localStorage.setItem("djs_user_info", JSON.stringify(userInfo));
      set({ userEmail: email, userInfo });
    },
  };
});
