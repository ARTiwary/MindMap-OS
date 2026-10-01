import { useEffect, useState, Suspense, lazy } from "react";
import { Routes, Route } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";
import { ProtectedRoute } from "@/router/ProtectedRoute";
import { LandingPage } from "@/pages/LandingPage";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { NodesPage } from "@/pages/NodesPage";
import { NodeDetailPage } from "@/pages/NodeDetailPage";
import { TagsPage } from "@/pages/TagsPage";
import { SearchPage } from "@/pages/SearchPage";
import { ActivityPage } from "@/pages/ActivityPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { useAuthStore } from "@/stores/authStore";
import { useThemeStore } from "@/stores/themeStore";
import { authApi } from "@/services/resources";

// The graph (react-flow) and analytics (recharts) pages pull in the two
// heaviest dependencies in the app - lazy-loading them keeps those bundles
// out of the initial page load for everyone who isn't visiting those routes.
const GraphPage = lazy(() => import("@/pages/GraphPage").then((m) => ({ default: m.GraphPage })));
const AnalyticsPage = lazy(() =>
  import("@/pages/AnalyticsPage").then((m) => ({ default: m.AnalyticsPage }))
);

function RouteFallback() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="skeleton w-8 h-8 rounded-full" />
    </div>
  );
}

export default function App() {
  const { hydrate, accessToken, setUser } = useAuthStore();
  const applyTheme = useThemeStore((s) => s.applyTheme);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    applyTheme();
    hydrate();
    setReady(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!ready) return;
    if (accessToken) {
      authApi.me().then((res) => setUser(res.data)).catch(() => {});
    }
  }, [ready, accessToken, setUser]);

  if (!ready) return null;

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/nodes" element={<NodesPage />} />
          <Route path="/nodes/:id" element={<NodeDetailPage />} />
          <Route path="/tags" element={<TagsPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route
            path="/analytics"
            element={
              <Suspense fallback={<RouteFallback />}>
                <AnalyticsPage />
              </Suspense>
            }
          />
          <Route path="/activity" element={<ActivityPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route
            path="/graph"
            element={
              <Suspense fallback={<RouteFallback />}>
                <GraphPage />
              </Suspense>
            }
          />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
