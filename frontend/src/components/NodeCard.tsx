import { Link } from "react-router-dom";
import { Star } from "lucide-react";
import type { KnowledgeNode } from "@/types";
import { NodeTypeBadge } from "./ui/NodeTypeBadge";

export function NodeCard({ node }: { node: KnowledgeNode }) {
  return (
    <Link
      to={`/nodes/${node.id}`}
      className="card p-5 flex flex-col gap-3 hover:border-accent/50 transition-colors group"
    >
      <div className="flex items-start justify-between gap-2">
        <NodeTypeBadge type={node.node_type} />
        {node.is_favorite && <Star size={15} className="text-node-idea fill-node-idea shrink-0" />}
      </div>
      <h3 className="font-display text-lg leading-snug group-hover:text-accent transition-colors">
        {node.title}
      </h3>
      {node.description && (
        <p className="text-sm text-white/50 line-clamp-2">{node.description}</p>
      )}
      {node.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-auto pt-1">
          {node.tags.slice(0, 3).map((tag) => (
            <span
              key={tag.id}
              className="text-[11px] px-2 py-0.5 rounded-full border border-border text-white/60"
            >
              {tag.name}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}
