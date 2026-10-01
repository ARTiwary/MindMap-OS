import { useQuery } from "@tanstack/react-query";
import { Clock } from "lucide-react";
import { activityApi } from "@/services/resources";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";

const ACTION_LABELS: Record<string, string> = {
  NODE_CREATED: "Created",
  NODE_UPDATED: "Updated",
  NODE_DELETED: "Deleted",
  NODE_VIEWED: "Viewed",
  RELATIONSHIP_CREATED: "Connected",
  RELATIONSHIP_DELETED: "Disconnected",
  TAG_ADDED: "Tagged",
  RESOURCE_ADDED: "Added resource",
};

function groupByDay(items: any[]) {
  const groups: Record<string, any[]> = {};
  for (const item of items) {
    const day = new Date(item.created_at).toDateString();
    groups[day] = groups[day] || [];
    groups[day].push(item);
  }
  return groups;
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function ActivityPage() {
  const { data, isLoading } = useQuery({ queryKey: ["activity"], queryFn: () => activityApi.list() });
  const items = (data?.data as any[]) ?? [];
  const groups = groupByDay(items);
  const today = new Date().toDateString();

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">
      <h1 className="font-display text-2xl mb-1">Activity</h1>
      <p className="text-white/50 text-sm mb-8">A running history of what you've built.</p>

      {isLoading ? (
        <div className="space-y-3">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : items.length === 0 ? (
        <EmptyState icon={<Clock size={40} />} title="No activity yet" description="Create or connect a node to see it appear here." />
      ) : (
        Object.entries(groups).map(([day, entries]) => (
          <div key={day} className="mb-8">
            <h2 className="text-xs uppercase tracking-wide text-white/40 mb-3">
              {day === today ? "Today" : day}
            </h2>
            <div className="space-y-1 border-l border-border pl-4">
              {entries.map((entry) => (
                <div key={entry.id} className="relative py-2">
                  <span className="absolute -left-[21px] top-3.5 w-2 h-2 rounded-full bg-accent" />
                  <div className="flex items-baseline gap-3">
                    <span className="text-xs text-white/30 font-mono w-12 shrink-0">
                      {formatTime(entry.created_at)}
                    </span>
                    <span className="text-sm text-white/80">
                      <span className="text-accent">{ACTION_LABELS[entry.action] ?? entry.action}</span>{" "}
                      {entry.summary}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
