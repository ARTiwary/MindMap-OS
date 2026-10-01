import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search as SearchIcon } from "lucide-react";
import { searchApi } from "@/services/resources";
import { NodeCard } from "@/components/NodeCard";
import { SkeletonGrid } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";

export function SearchPage() {
  const [input, setInput] = useState("");
  const [query, setQuery] = useState("");

  useEffect(() => {
    const t = setTimeout(() => setQuery(input.trim()), 350);
    return () => clearTimeout(t);
  }, [input]);

  const { data, isFetching } = useQuery({
    queryKey: ["search", query],
    queryFn: () => searchApi.search(query),
    enabled: query.length > 0,
  });

  const results = data?.data;

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <h1 className="font-display text-2xl mb-1">Search</h1>
      <p className="text-white/50 text-sm mb-6">Find anything across your titles, notes, tags, and resources.</p>

      <div className="relative mb-8">
        <SearchIcon size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
        <input
          autoFocus
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Search your knowledge base…"
          className="w-full bg-transparent border border-border rounded-lg pl-11 pr-4 py-3 text-sm focus:outline-none focus:border-accent"
        />
      </div>

      {!query ? (
        <p className="text-sm text-white/40 text-center py-10">Start typing to search.</p>
      ) : isFetching ? (
        <SkeletonGrid count={4} />
      ) : !results || results.items.length === 0 ? (
        <EmptyState
          icon={<SearchIcon size={40} />}
          title="Nothing found"
          description="Try another keyword, or create a new node for this concept."
        />
      ) : (
        <>
          <p className="text-xs text-white/40 mb-4">{results.total} result{results.total === 1 ? "" : "s"}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {results.items.map((node) => (
              <NodeCard key={node.id} node={node} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
