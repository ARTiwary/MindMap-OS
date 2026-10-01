import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Brain } from "lucide-react";
import { authApi } from "@/services/resources";
import { useAuthStore } from "@/stores/authStore";
import { apiErrorMessage } from "@/services/api";

export function LoginPage() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data } = await authApi.login({ email, password });
      setTokens(data.access_token, data.refresh_token);
      const me = await authApi.me();
      setUser(me.data);
      navigate("/dashboard");
    } catch (err) {
      setError(apiErrorMessage(err, "Could not log in. Check your credentials."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <Link to="/" className="flex items-center justify-center gap-2 mb-8">
          <Brain size={22} className="text-accent" />
          <span className="font-display text-lg">MindMap OS</span>
        </Link>

        <div className="card p-6">
          <h1 className="font-display text-xl mb-1">Welcome back</h1>
          <p className="text-sm text-white/50 mb-6">Log in to continue exploring your graph.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs text-white/50 mb-1 block">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-transparent border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1 block">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-transparent border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
                placeholder="••••••••"
              />
            </div>
            {error && <p className="text-sm text-node-question">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-accent text-black font-medium py-2.5 rounded-lg hover:bg-accent-soft transition-colors disabled:opacity-50"
            >
              {loading ? "Logging in…" : "Log in"}
            </button>
          </form>

          <p className="text-xs text-white/40 mt-4 text-center">
            Demo account: <span className="font-mono">demo@mindmapos.app</span> /{" "}
            <span className="font-mono">DemoPassword123!</span>
          </p>
        </div>

        <p className="text-sm text-white/50 text-center mt-6">
          Don't have an account?{" "}
          <Link to="/register" className="text-accent hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
