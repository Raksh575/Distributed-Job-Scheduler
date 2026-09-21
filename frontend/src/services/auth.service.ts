import api from "./api";

export interface LoginPayload {
  username: string; // backend expects OAuth2 form: username field = email
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  username: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  username: string;
  phone?: string;
  country?: string;
  timezone?: string;
  profile_picture?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

const authService = {
  login: async (email: string, password: string): Promise<TokenResponse> => {
    // FastAPI OAuth2 expects form-encoded, not JSON
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);
    const response = await api.post<TokenResponse>("/auth/token", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return response.data;
  },

  register: async (payload: RegisterPayload): Promise<UserResponse> => {
    const response = await api.post<UserResponse>("/auth/register", payload);
    return response.data;
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  logout: async (refreshToken: string): Promise<void> => {
    await api.post("/auth/logout", { refresh_token: refreshToken });
  },

  changePassword: async (oldPassword: string, newPassword: string): Promise<void> => {
    await api.post("/auth/change-password", {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  forgotPassword: async (email: string): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>("/auth/forgot-password", { email });
    return response.data;
  },

  getMe: async (): Promise<UserResponse> => {
    const response = await api.get<UserResponse>("/users/me");
    return response.data;
  },

  updateProfile: async (payload: Partial<UserResponse>): Promise<UserResponse> => {
    const response = await api.patch<UserResponse>("/users/me", payload);
    return response.data;
  },
};

export default authService;
