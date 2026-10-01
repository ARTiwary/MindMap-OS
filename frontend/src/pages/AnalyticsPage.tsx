import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from "recharts";
import { analyticsApi, suggestionsApi } from "@/services/resources";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { Lightbulb } from "lucide-react";

const BAR_COLORS = ["#7C8CFF", "#5CD6C0", "#F5B95C", "#F27878", "#B98CE8", "#5CC2F2", "#8CD65C", "#F28CC5"];

export function AnalyticsPage() {
  const mostConnected = useQuery({ queryKey: ["analytics", "most-connected"], queryFn: analyticsApi.mostConnected });
  const tagStats = useQuery({ queryKey: ["analytics", "tags"], queryFn: analyticsApi.tagStats });
  const suggestions = useQuery({ queryKey: ["suggestions"], queryFn: suggestionsApi.connections });

  return (
    <div className="max-w-5xl mx-auto px-6 py-10 space-y-8">
      <div>
        <h1 className="font-display text-2xl mb-1">Analytics</h1>
        <p className="text-white/50 text-sm">How your knowledge graph is shaping up.</p>
      </div>

      <section className="card p-5">
        <h2 className="font-display text-sm text-white/70 mb-4">Top concepts by connections</h2>
        {mostConnected.isLoading ? (
          <SkeletonCard />
        ) : !mostConnected.data?.data?.length ? (
          <p className="text-sm text-white/40">Connect a few nodes to see this chart fill in.</p>
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(160, mostConnected.data.data.length * 36)}>
            <BarChart data={mostConnected.data.data} layout="vertical" margin={{ left: 20 }}>
              <XAxis type="number" hide />
              <YAxis
                dataKey="title"
                type="category"
                width={140}
                tick={{ fill: "#8890A8", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{ background: "#14161C", border: "1px solid #22252E", borderRadius: 8 }}
                cursor={{ fill: "rgba(255,255,255,0.03)" }}
              />
              <Bar dataKey="connections" radius={[0, 6, 6, 0]}>
                {mostConnected.data.data.map((_: any, i: number) => (
                  <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </section>

      <section className="card p-5">
        <h2 className="font-display text-sm text-white/70 mb-4">Tag usage</h2>
        {tagStats.isLoading ? (
          <SkeletonCard />
        ) : !tagStats.data?.data?.length ? (
          <p className="text-sm text-white/40">No tags yet.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {tagStats.data.data
              .filter((t: any) => t.usage > 0)
              .map((t: any) => (
                <span
                  key={t.name}
                  className="text-xs px-3 py-1.5 rounded-full border border-border flex items-center gap-1.5"
                >
                  <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: t.color }} />
                  {t.name} <span className="text-white/30">· {t.usage}</span>
                </span>
              ))}
          </div>
        )}
      </section>

      <section className="card p-5">
        <h2 className="font-display text-sm text-white/70 mb-4 flex items-center gap-2">
          <Lightbulb size={15} className="text-node-idea" /> Suggested connections
        </h2>
        {suggestions.isLoading ? (
          <SkeletonCard />
        ) : !suggestions.data?.data?.length ? (
          <p className="text-sm text-white/40">
            No suggestions right now — as you tag more nodes, we'll flag ones that share a tag but
            aren't connected yet.
          </p>
        ) : (
          <div className="space-y-2">
            {suggestions.data.data.map((s: any, i: number) => (
              <div key={i} className="flex items-center justify-between px-4 py-3 rounded-lg border border-border">
                <span className="text-sm">
                  {s.node_a_title} <span className="text-white/30">↔</span> {s.node_b_title}
                </span>
                <span className="text-xs text-white/40">{s.reason}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
