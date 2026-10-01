import { create } from "zustand";
import type { User } from "@/types";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
  hydrate: () => void;
}

// Tokens are kept in localStorage so a page refresh doesn't sign the user
// out mid-session. This is a pragmatic default for a demo app; a
// production system would weigh this against XSS exposure and likely move
// to httpOnly cookies for the refresh token.
export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  setTokens: (access, refresh) => {
    localStorage.setItem("mindmap_access_token", access);
    localStorage.setItem("mindmap_refresh_token", refresh);
    set({ accessToken: access, refreshToken: refresh });
  },
  setUser: (user) => set({ user }),
  logout: () => {
    localStorage.removeItem("mindmap_access_token");
    localStorage.removeItem("mindmap_refresh_token");
    set({ accessToken: null, refreshToken: null, user: null });
  },
  hydrate: () => {
    const access = localStorage.getItem("mindmap_access_token");
    const refresh = localStorage.getItem("mindmap_refresh_token");
    if (access && refresh) set({ accessToken: access, refreshToken: refresh });
  },
}));
