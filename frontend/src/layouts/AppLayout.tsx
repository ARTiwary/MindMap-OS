import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Network, Tags, Search, FolderKanban,
  BarChart3, Clock, Settings, LogOut, Sun, Moon, Monitor, Brain,
} from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { useThemeStore } from "@/stores/themeStore";
import { authApi } from "@/services/resources";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/nodes", label: "Nodes", icon: FolderKanban },
  { to: "/graph", label: "Graph", icon: Network },
  { to: "/tags", label: "Tags", icon: Tags },
  { to: "/search", label: "Search", icon: Search },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/activity", label: "Activity", icon: Clock },
];

export function AppLayout() {
  const navigate = useNavigate();
  const { user, logout, refreshToken } = useAuthStore();
  const { theme, setTheme } = useThemeStore();

  async function handleLogout() {
    try {
      await authApi.logout(refreshToken ?? undefined);
    } catch {
      /* token may already be invalid; proceed with local logout regardless */
    }
    logout();
    navigate("/login");
  }

  const themeIcons = { dark: Moon, light: Sun, system: Monitor } as const;
  const ThemeIcon = themeIcons[theme];

  function cycleTheme() {
    const order: (typeof theme)[] = ["dark", "light", "system"];
    setTheme(order[(order.indexOf(theme) + 1) % order.length]);
  }

  return (
    <div className="flex min-h-screen">
      <aside className="w-64 shrink-0 border-r border-border flex flex-col p-4 hidden md:flex">
        <div className="flex items-center gap-2 px-2 py-3 mb-4">
          <Brain size={22} className="text-accent" />
          <span className="font-display text-lg">MindMap OS</span>
        </div>

        <nav className="flex-1 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? "bg-accent/15 text-accent"
                    : "text-white/60 hover:text-white/90 hover:bg-white/5"
                }`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="space-y-1 pt-3 border-t border-border">
          <button
            onClick={cycleTheme}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-white/60 hover:text-white/90 hover:bg-white/5 transition-colors"
          >
            <ThemeIcon size={17} />
            <span className="capitalize">{theme} mode</span>
          </button>
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? "bg-accent/15 text-accent" : "text-white/60 hover:text-white/90 hover:bg-white/5"
              }`
            }
          >
            <Settings size={17} />
            Settings
          </NavLink>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-white/60 hover:text-node-question hover:bg-white/5 transition-colors"
          >
            <LogOut size={17} />
            Log out
          </button>
          {user && (
            <div className="px-3 pt-2 text-xs text-white/40 truncate">{user.email}</div>
          )}
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        <Outlet />
      </main>
    </div>
  );
}
