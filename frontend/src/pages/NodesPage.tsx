import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, FolderKanban } from "lucide-react";
import { nodesApi } from "@/services/resources";
import { NodeCard } from "@/components/NodeCard";
import { SkeletonGrid } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { NodeFormModal, type NodeFormValues } from "@/components/NodeFormModal";
import { NODE_TYPE_META } from "@/utils/nodeMeta";

export function NodesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState("");
  const [favoriteOnly, setFavoriteOnly] = useState(false);
  const showCreate = searchParams.get("create") === "1";
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["nodes", page, typeFilter, favoriteOnly],
    queryFn: () =>
      nodesApi.list({
        page,
        limit: 12,
        type: typeFilter || undefined,
        favorite: favoriteOnly || undefined,
      }),
  });

  const createMutation = useMutation({
    mutationFn: (values: NodeFormValues) => nodesApi.create(values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nodes"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setSearchParams({});
    },
  });

  const result = data?.data;

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-2xl">Nodes</h1>
          <p className="text-white/50 text-sm mt-1">Every piece of knowledge you've captured.</p>
        </div>
        <button
          onClick={() => setSearchParams({ create: "1" })}
          className="bg-accent text-black font-medium px-4 py-2 rounded-lg hover:bg-accent-soft transition-colors inline-flex items-center gap-2 text-sm"
        >
          <Plus size={16} /> New node
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-6">
        <button
          onClick={() => {
            setTypeFilter("");
            setPage(1);
          }}
          className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
            !typeFilter ? "border-accent text-accent" : "border-border text-white/50 hover:text-white/80"
          }`}
        >
          All types
        </button>
        {Object.entries(NODE_TYPE_META).map(([key, meta]) => (
          <button
            key={key}
            onClick={() => {
              setTypeFilter(key);
              setPage(1);
            }}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              typeFilter === key ? "border-accent text-accent" : "border-border text-white/50 hover:text-white/80"
            }`}
          >
            {meta.label}
          </button>
        ))}
        <div className="w-px h-4 bg-border mx-1" />
        <button
          onClick={() => {
            setFavoriteOnly((v) => !v);
            setPage(1);
          }}
          className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
            favoriteOnly ? "border-node-idea text-node-idea" : "border-border text-white/50 hover:text-white/80"
          }`}
        >
          ★ Favorites
        </button>
      </div>

      {isLoading ? (
        <SkeletonGrid count={9} />
      ) : !result || result.items.length === 0 ? (
        <EmptyState
          icon={<FolderKanban size={40} />}
          title="Nothing here yet"
          description="Try a different filter, or create a new node to get started."
        />
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {result.items.map((node) => (
              <NodeCard key={node.id} node={node} />
            ))}
          </div>

          {result.pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              {Array.from({ length: result.pages }).map((_, i) => (
                <button
                  key={i}
                  onClick={() => setPage(i + 1)}
                  className={`w-8 h-8 rounded-lg text-sm transition-colors ${
                    page === i + 1 ? "bg-accent text-black" : "text-white/50 hover:bg-white/5"
                  }`}
                >
                  {i + 1}
                </button>
              ))}
            </div>
          )}
        </>
      )}

      {showCreate && (
        <NodeFormModal
          onClose={() => setSearchParams({})}
          submitting={createMutation.isPending}
          onSubmit={(values) => createMutation.mutate(values)}
        />
      )}
    </div>
  );
}
