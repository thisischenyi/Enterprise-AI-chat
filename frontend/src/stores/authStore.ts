import { create } from "zustand";
import { apiClient, AuthError, queryClient } from "../lib/api";

export interface User {
  id: string;
  email: string;
  name: string;
  role: "employee" | "admin";
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (role: "employee" | "admin") => Promise<LoginResult>;
  handleCallback: (stateToken: string, role: "employee" | "admin") => Promise<void>;
  fetchUser: () => Promise<void>;
  logout: () => void;
}

export interface LoginResult {
  redirectUrl: string;
  stateToken: string;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (role: "employee" | "admin") => {
    set({ isLoading: true, error: null });
    try {
      const result = await apiClient<{
        redirect_url: string;
        state_token: string;
        role: string;
      }>("/auth/login?role=" + encodeURIComponent(role), {
        method: "POST",
      });

      return {
        redirectUrl: result.redirect_url,
        stateToken: result.state_token,
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : "Login failed";
      set({ isLoading: false, error: message });
      throw err;
    }
  },

  handleCallback: async (stateToken: string, role: "employee" | "admin") => {
    set({ isLoading: true, error: null });
    try {
      const user = await apiClient<User>("/auth/callback?role=" + encodeURIComponent(role) + "&state_token=" + encodeURIComponent(stateToken), {
        method: "POST",
      });

      set({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      // Invalidate user query so TanStack Query picks up fresh state
      queryClient.invalidateQueries({ queryKey: ["currentUser"] });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Callback failed";
      set({ isLoading: false, error: message });
      throw err;
    }
  },

  fetchUser: async () => {
    set({ isLoading: true });
    try {
      const user = await apiClient<User>("/auth/me");

      set({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (err) {
      if (err instanceof AuthError) {
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        });
      } else {
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: err instanceof Error ? err.message : "Failed to fetch user",
        });
      }
    }
  },

  logout: () => {
    set({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    queryClient.invalidateQueries({ queryKey: ["currentUser"] });
  },
}));