import { useState, type FormEvent } from "react";
import { X } from "lucide-react";
import type { NodeDetail, NodeType, NodeStatus, Importance } from "@/types";
import { NODE_TYPE_META } from "@/utils/nodeMeta";

export interface NodeFormValues {
  title: string;
  description: string;
  content: string;
  node_type: NodeType;
  status: NodeStatus;
  importance: Importance;
  is_favorite: boolean;
}

export function NodeFormModal({
  initial,
  onClose,
  onSubmit,
  submitting,
}: {
  initial?: Partial<NodeDetail>;
  onClose: () => void;
  onSubmit: (values: NodeFormValues) => void;
  submitting: boolean;
}) {
  const [values, setValues] = useState<NodeFormValues>({
    title: initial?.title ?? "",
    description: initial?.description ?? "",
    content: initial?.content ?? "",
    node_type: initial?.node_type ?? "NOTE",
    status: initial?.status ?? "ACTIVE",
    importance: initial?.importance ?? "MEDIUM",
    is_favorite: initial?.is_favorite ?? false,
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit(values);
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50">
      <div className="card w-full max-w-lg max-h-[85vh] overflow-y-auto p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-display text-lg">{initial ? "Edit node" : "New node"}</h2>
          <button onClick={onClose} className="text-white/50 hover:text-white">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-white/50 mb-1 block">Title</label>
            <input
              required
              autoFocus
              value={values.title}
              onChange={(e) => setValues((v) => ({ ...v, title: e.target.value }))}
              className="w-full bg-transparent border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
              placeholder="What's the idea?"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-white/50 mb-1 block">Type</label>
              <select
                value={values.node_type}
                onChange={(e) => setValues((v) => ({ ...v, node_type: e.target.value as NodeType }))}
                className="w-full bg-transparent border border-border rounded-lg px-2 py-2 text-sm focus:outline-none focus:border-accent"
              >
                {Object.entries(NODE_TYPE_META).map(([key, meta]) => (
                  <option key={key} value={key} className="bg-surface">
                    {meta.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1 block">Status</label>
              <select
                value={values.status}
                onChange={(e) => setValues((v) => ({ ...v, status: e.target.value as NodeStatus }))}
                className="w-full bg-transparent border border-border rounded-lg px-2 py-2 text-sm focus:outline-none focus:border-accent"
              >
                {(["DRAFT", "ACTIVE", "ARCHIVED", "COMPLETED"] as const).map((s) => (
                  <option key={s} value={s} className="bg-surface">
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1 block">Importance</label>
              <select
                value={values.importance}
                onChange={(e) => setValues((v) => ({ ...v, importance: e.target.value as Importance }))}
                className="w-full bg-transparent border border-border rounded-lg px-2 py-2 text-sm focus:outline-none focus:border-accent"
              >
                {(["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const).map((s) => (
                  <option key={s} value={s} className="bg-surface">
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs text-white/50 mb-1 block">Description</label>
            <input
              value={values.description}
              onChange={(e) => setValues((v) => ({ ...v, description: e.target.value }))}
              className="w-full bg-transparent border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
              placeholder="One line summary"
            />
          </div>

          <div>
            <label className="text-xs text-white/50 mb-1 block">Content (Markdown)</label>
            <textarea
              rows={6}
              value={values.content}
              onChange={(e) => setValues((v) => ({ ...v, content: e.target.value }))}
              className="w-full bg-transparent border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent font-mono resize-none"
              placeholder="Write freely — headings, lists, code blocks, links…"
            />
          </div>

          <label className="flex items-center gap-2 text-sm text-white/70">
            <input
              type="checkbox"
              checked={values.is_favorite}
              onChange={(e) => setValues((v) => ({ ...v, is_favorite: e.target.checked }))}
              className="accent-accent"
            />
            Mark as favorite
          </label>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm text-white/60 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="bg-accent text-black font-medium px-5 py-2 rounded-lg hover:bg-accent-soft transition-colors text-sm disabled:opacity-50"
            >
              {submitting ? "Saving…" : initial ? "Save changes" : "Create node"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
