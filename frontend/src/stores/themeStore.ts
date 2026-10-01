import { create } from "zustand";

type Theme = "light" | "dark" | "system";

interface ThemeState {
  theme: Theme;
  setTheme: (t: Theme) => void;
  applyTheme: () => void;
}

function resolveSystemPrefersDark() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: (localStorage.getItem("mindmap_theme") as Theme) || "dark",
  setTheme: (t) => {
    localStorage.setItem("mindmap_theme", t);
    set({ theme: t });
    get().applyTheme();
  },
  applyTheme: () => {
    const { theme } = get();
    const isDark = theme === "dark" || (theme === "system" && resolveSystemPrefersDark());
    document.documentElement.classList.toggle("light", !isDark);
  },
}));
