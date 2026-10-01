import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { AreaChart, Area, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import { Star, Plus, Network } from "lucide-react";
import { dashboardApi } from "@/services/resources";
import { useAuthStore } from "@/stores/authStore";
import { SkeletonGrid } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { NODE_TYPE_META } from "@/utils/nodeMeta";

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

const STAT_CARDS = [
  { key: "total_nodes", label: "Nodes" },
  { key: "total_connections", label: "Connections" },
  { key: "total_tags", label: "Topics" },
  { key: "total_projects", label: "Projects" },
] as const;

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: dashboardApi.get });
  const stats = data?.data;

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-2xl">
            {greeting()}, {user?.full_name || user?.username} 👋
          </h1>
          <p className="text-white/50 text-sm mt-1">Here's your knowledge universe.</p>
        </div>
        <Link
          to="/nodes?create=1"
          className="bg-accent text-black font-medium px-4 py-2 rounded-lg hover:bg-accent-soft transition-colors inline-flex items-center gap-2 text-sm"
        >
          <Plus size={16} /> New node
        </Link>
      </div>

      {isLoading ? (
        <SkeletonGrid count={4} />
      ) : !stats || stats.total_nodes === 0 ? (
        <EmptyState
          icon={<Network size={40} />}
          title="Your knowledge graph is empty"
          description="Start with one idea. Every connection you draw from here builds your personal knowledge universe."
          action={
            <Link
              to="/nodes?create=1"
              className="bg-accent text-black font-medium px-5 py-2.5 rounded-lg hover:bg-accent-soft transition-colors inline-flex items-center gap-2 text-sm"
            >
              <Plus size={16} /> Create your first node
            </Link>
          }
        />
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {STAT_CARDS.map(({ key, label }) => (
              <div key={key} className="card p-5">
                <div className="text-3xl font-display">{stats[key as keyof typeof stats] as number}</div>
                <div className="text-xs text-white/50 mt-1">{label}</div>
              </div>
            ))}
          </div>

          <div className="card p-5 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-sm text-white/70">Knowledge growth (30 days)</h2>
              <span className="text-xs text-white/40">
                Density: {stats.knowledge_density} connections/node
              </span>
            </div>
            <ResponsiveContainer width="100%" height={140}>
              <AreaChart data={stats.growth}>
                <defs>
                  <linearGradient id="growthFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#7C8CFF" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#7C8CFF" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" hide />
                <Tooltip
                  contentStyle={{ background: "#14161C", border: "1px solid #22252E", borderRadius: 8 }}
                  labelStyle={{ color: "#fff" }}
                />
                <Area type="monotone" dataKey="count" stroke="#7C8CFF" fill="url(#growthFill)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <section>
              <h2 className="font-display text-sm text-white/70 mb-3">Recently updated</h2>
              <div className="space-y-2">
                {stats.recently_updated.map((n) => (
                  <NodeRow key={n.id} id={n.id} title={n.title} typeLabel={n.node_type} />
                ))}
              </div>
            </section>
            <section>
              <h2 className="font-display text-sm text-white/70 mb-3 flex items-center gap-1.5">
                <Star size={14} className="text-node-idea fill-node-idea" /> Favorites
              </h2>
              <div className="space-y-2">
                {stats.favorites.length === 0 ? (
                  <p className="text-sm text-white/40">No favorites yet — star a node to pin it here.</p>
                ) : (
                  stats.favorites.map((n) => (
                    <NodeRow key={n.id} id={n.id} title={n.title} typeLabel={n.node_type} />
                  ))
                )}
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  );
}

function NodeRow({ id, title, typeLabel }: { id: string; title: string; typeLabel: string }) {
  const meta = NODE_TYPE_META[typeLabel as keyof typeof NODE_TYPE_META];
  return (
    <Link
      to={`/nodes/${id}`}
      className="flex items-center gap-3 px-3 py-2.5 rounded-lg border border-border hover:border-accent/50 transition-colors"
    >
      <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: meta?.color }} />
      <span className="text-sm truncate">{title}</span>
    </Link>
  );
}
