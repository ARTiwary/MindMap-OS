import { useAuthStore } from "@/stores/authStore";
import { useThemeStore } from "@/stores/themeStore";
import { Sun, Moon, Monitor } from "lucide-react";

const THEME_OPTIONS = [
  { key: "light", label: "Light", icon: Sun },
  { key: "dark", label: "Dark", icon: Moon },
  { key: "system", label: "System", icon: Monitor },
] as const;

export function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const { theme, setTheme } = useThemeStore();

  return (
    <div className="max-w-xl mx-auto px-6 py-10">
      <h1 className="font-display text-2xl mb-1">Settings</h1>
      <p className="text-white/50 text-sm mb-8">Your account and appearance preferences.</p>

      <section className="card p-5 mb-6">
        <h2 className="font-display text-sm text-white/70 mb-4">Profile</h2>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-white/40">Username</span>
            <span>{user?.username}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-white/40">Email</span>
            <span>{user?.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-white/40">Full name</span>
            <span>{user?.full_name || "—"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-white/40">Member since</span>
            <span>{user ? new Date(user.created_at).toLocaleDateString() : "—"}</span>
          </div>
        </div>
      </section>

      <section className="card p-5">
        <h2 className="font-display text-sm text-white/70 mb-4">Appearance</h2>
        <div className="flex gap-2">
          {THEME_OPTIONS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTheme(key)}
              className={`flex-1 flex flex-col items-center gap-2 py-4 rounded-lg border transition-colors ${
                theme === key ? "border-accent text-accent" : "border-border text-white/50 hover:text-white/80"
              }`}
            >
              <Icon size={18} />
              <span className="text-xs">{label}</span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
