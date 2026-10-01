import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Star, Pencil, Trash2, ArrowLeft, Link2, GitBranch } from "lucide-react";
import { nodesApi } from "@/services/resources";
import { NodeTypeBadge } from "@/components/ui/NodeTypeBadge";
import { NodeFormModal, type NodeFormValues } from "@/components/NodeFormModal";
import { SkeletonCard } from "@/components/ui/Skeleton";

export function NodeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["node", id],
    queryFn: () => nodesApi.get(id!),
    enabled: !!id,
  });

  const updateMutation = useMutation({
    mutationFn: (values: NodeFormValues) => nodesApi.update(id!, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["node", id] });
      queryClient.invalidateQueries({ queryKey: ["nodes"] });
      setEditing(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => nodesApi.remove(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nodes"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      navigate("/nodes");
    },
  });

  const toggleFavoriteMutation = useMutation({
    mutationFn: (is_favorite: boolean) => nodesApi.update(id!, { is_favorite }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["node", id] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-10 space-y-4">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  const node = data?.data;
  if (!node) return null;

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      <Link to="/nodes" className="inline-flex items-center gap-1.5 text-sm text-white/50 hover:text-white mb-6">
        <ArrowLeft size={15} /> Back to nodes
      </Link>

      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <NodeTypeBadge type={node.node_type} />
          <h1 className="font-display text-3xl mt-3">{node.title}</h1>
          {node.description && <p className="text-white/50 mt-2">{node.description}</p>}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={() => toggleFavoriteMutation.mutate(!node.is_favorite)}
            className="p-2 rounded-lg hover:bg-white/5 transition-colors"
            title={node.is_favorite ? "Remove from favorites" : "Add to favorites"}
          >
            <Star
              size={18}
              className={node.is_favorite ? "text-node-idea fill-node-idea" : "text-white/40"}
            />
          </button>
          <button onClick={() => setEditing(true)} className="p-2 rounded-lg hover:bg-white/5 transition-colors">
            <Pencil size={17} className="text-white/50" />
          </button>
          <button
            onClick={() => {
              if (confirm(`Delete "${node.title}"? This can't be undone.`)) deleteMutation.mutate();
            }}
            className="p-2 rounded-lg hover:bg-white/5 transition-colors"
          >
            <Trash2 size={17} className="text-node-question" />
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-8">
        {node.tags.map((tag) => (
          <span key={tag.id} className="text-xs px-2.5 py-1 rounded-full border border-border text-white/60">
            {tag.name}
          </span>
        ))}
      </div>

      {node.content && (
        <div className="card p-6 mb-6">
          <pre className="whitespace-pre-wrap font-sans text-sm text-white/80 leading-relaxed">
            {node.content}
          </pre>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 mb-8">
        <div className="card p-5 flex items-center gap-3">
          <GitBranch size={18} className="text-accent" />
          <div>
            <div className="text-lg font-display">{node.references_count}</div>
            <div className="text-xs text-white/50">References</div>
          </div>
        </div>
        <div className="card p-5 flex items-center gap-3">
          <Link2 size={18} className="text-accent" />
          <div>
            <div className="text-lg font-display">{node.referenced_by_count}</div>
            <div className="text-xs text-white/50">Referenced by</div>
          </div>
        </div>
      </div>

      <div className="text-center">
        <Link to="/graph" className="text-sm text-accent hover:underline">
          Explore in graph view →
        </Link>
      </div>

      {editing && (
        <NodeFormModal
          initial={node}
          onClose={() => setEditing(false)}
          submitting={updateMutation.isPending}
          onSubmit={(values) => updateMutation.mutate(values)}
        />
      )}
    </div>
  );
}
