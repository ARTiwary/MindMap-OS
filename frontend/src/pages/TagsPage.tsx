import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Tags as TagsIcon } from "lucide-react";
import { tagsApi } from "@/services/resources";
import { EmptyState } from "@/components/ui/EmptyState";
import { SkeletonGrid } from "@/components/ui/Skeleton";

const PALETTE = ["#7C8CFF", "#5CD6C0", "#F5B95C", "#F27878", "#B98CE8", "#5CC2F2", "#8CD65C", "#F28CC5"];

export function TagsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["tags"], queryFn: tagsApi.list });
  const [name, setName] = useState("");

  const createMutation = useMutation({
    mutationFn: (payload: { name: string; color: string }) => tagsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      setName("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => tagsApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tags"] }),
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    const color = PALETTE[Math.floor(Math.random() * PALETTE.length)];
    createMutation.mutate({ name: name.trim(), color });
  }

  const tags = data?.data ?? [];

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      <h1 className="font-display text-2xl mb-1">Tags</h1>
      <p className="text-white/50 text-sm mb-6">Organize your knowledge with lightweight labels.</p>

      <form onSubmit={handleSubmit} className="flex gap-2 mb-8">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New tag name…"
          className="flex-1 bg-transparent border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
        />
        <button
          type="submit"
          disabled={createMutation.isPending}
          className="bg-accent text-black font-medium px-4 py-2 rounded-lg hover:bg-accent-soft transition-colors inline-flex items-center gap-2 text-sm disabled:opacity-50"
        >
          <Plus size={16} /> Add
        </button>
      </form>

      {isLoading ? (
        <SkeletonGrid count={6} />
      ) : tags.length === 0 ? (
        <EmptyState icon={<TagsIcon size={40} />} title="No tags yet" description="Create your first tag above." />
      ) : (
        <div className="flex flex-wrap gap-3">
          {tags.map((tag) => (
            <div
              key={tag.id}
              className="flex items-center gap-2 pl-3 pr-2 py-1.5 rounded-full border border-border group"
            >
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: tag.color }} />
              <span className="text-sm">{tag.name}</span>
              <button
                onClick={() => deleteMutation.mutate(tag.id)}
                className="text-white/30 hover:text-node-question p-1 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
