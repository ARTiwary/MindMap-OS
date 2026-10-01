import type { NodeType } from "@/types";
import { NODE_TYPE_META } from "@/utils/nodeMeta";

export function NodeTypeBadge({ type }: { type: NodeType }) {
  const meta = NODE_TYPE_META[type];
  const Icon = meta.icon;
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
      style={{ backgroundColor: `${meta.color}20`, color: meta.color }}
    >
      <Icon size={12} strokeWidth={2.5} />
      {meta.label}
    </span>
  );
}
