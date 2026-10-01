import { Handle, Position, type NodeProps } from "reactflow";
import { Star } from "lucide-react";
import { NODE_TYPE_META } from "@/utils/nodeMeta";
import type { NodeType } from "@/types";

interface GraphNodeData {
  label: string;
  nodeType: NodeType;
  isFavorite: boolean;
  dimmed?: boolean;
  highlighted?: boolean;
}

export function GraphNode({ data }: NodeProps<GraphNodeData>) {
  const meta = NODE_TYPE_META[data.nodeType] ?? NODE_TYPE_META.NOTE;
  const Icon = meta.icon;

  return (
    <div
      className="px-3 py-2 rounded-xl border flex items-center gap-2 min-w-[120px] max-w-[200px] transition-all duration-150"
      style={{
        backgroundColor: `${meta.color}18`,
        borderColor: data.highlighted ? meta.color : `${meta.color}55`,
        opacity: data.dimmed ? 0.25 : 1,
        boxShadow: data.highlighted ? `0 0 0 2px ${meta.color}55` : "none",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <Icon size={13} style={{ color: meta.color }} className="shrink-0" />
      <span className="text-xs font-medium truncate">{data.label}</span>
      {data.isFavorite && <Star size={11} className="text-node-idea fill-node-idea shrink-0" />}
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}
