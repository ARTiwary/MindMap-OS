import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Brain } from "lucide-react";
import { authApi } from "@/services/resources";
import { useAuthStore } from "@/stores/authStore";
import { apiErrorMessage } from "@/services/api";

export function RegisterPage() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);
  const [form, setForm] = useState({ email: "", username: "", password: "", full_name: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update(field: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await authApi.register(form);
      const { data } = await authApi.login({ email: form.email, password: form.password });
      setTokens(data.access_token, data.refresh_token);
      const me = await authApi.me();
      setUser(me.data);
      navigate("/dashboard");
    } catch (err) {
      setError(apiErrorMessage(err, "Could not create your account."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-sm">
        <Link to="/" className="flex items-center justify-center gap-2 mb-8">
          <Brain size={22} className="text-accent" />
          <span className="font-display text-lg">MindMap OS</span>
        </Link>

        <div className="card p-6">
          <h1 className="font-display text-xl mb-1">Start your graph</h1>
          <p className="text-sm text-white/50 mb-6">One idea is all it takes to begin.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs text-white/50 mb-1 block">Full name</label>
              <input
                value={form.full_name}
                onChange={update("full_name")}
                className="w-full bg-transparent border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
                placeholder="Ada Lovelace"
              />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1 block">Username</label>
              <input
                required
                value={form.username}
                onChange={update("username")}
                pattern="^[a-zA-Z0-9_]+$"
                minLength={3}
                className="w-full bg-transparent border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
                placeholder="ada"
              />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1 block">Email</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={update("email")}
                className="w-full bg-transparent border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1 block">Password</label>
              <input
                type="password"
                required
                minLength={8}
                value={form.password}
                onChange={update("password")}
                className="w-full bg-transparent border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
                placeholder="At least 8 characters, 1 uppercase, 1 digit"
              />
            </div>
            {error && <p className="text-sm text-node-question">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-accent text-black font-medium py-2.5 rounded-lg hover:bg-accent-soft transition-colors disabled:opacity-50"
            >
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>
        </div>

        <p className="text-sm text-white/50 text-center mt-6">
          Already have an account?{" "}
          <Link to="/login" className="text-accent hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
