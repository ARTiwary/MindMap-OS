import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node as FlowNode,
} from "reactflow";
import "reactflow/dist/style.css";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Maximize2, X, Check } from "lucide-react";
import { graphApi, relationshipsApi } from "@/services/resources";
import { GraphNode } from "@/components/graph/GraphNode";
import { NODE_TYPE_META } from "@/utils/nodeMeta";
import type { NodeType } from "@/types";
import { EmptyState } from "@/components/ui/EmptyState";
import { Network } from "lucide-react";

const nodeTypes = { knowledgeNode: GraphNode };

/**
 * Positions nodes for first render. Any node that already has a saved
 * position (from a previous drag, persisted via POST /graph/positions) keeps
 * it exactly - this is what makes the layout survive a refresh or navigating
 * away and back. Only nodes that have never been placed (new nodes, or the
 * very first time this user opens the graph) get a computed fallback
 * position, arranged in concentric rings so the first-ever view is legible.
 *
 * Returns both the positioned nodes and the ids that needed a fallback, so
 * the caller can persist those newly-computed positions once - after that,
 * they count as "saved" too and this function will just pass them through.
 */
function layoutNodes(nodes: FlowNode[]): { positioned: FlowNode[]; newlyPlacedIds: string[] } {
  const unplaced = nodes.filter((n) => !(n.data as any).__saved);
  const perRing = 12;
  const ringGap = 220;
  const newlyPlacedIds: string[] = [];

  const positioned = nodes.map((n) => {
    if ((n.data as any).__saved) return n; // already has a real saved position
    const i = unplaced.findIndex((u) => u.id === n.id);
    const ring = Math.floor(i / perRing) + 1;
    const indexInRing = i % perRing;
    const countInRing = Math.min(perRing, unplaced.length - (ring - 1) * perRing);
    const angle = (indexInRing / countInRing) * 2 * Math.PI;
    const radius = ring * ringGap;
    newlyPlacedIds.push(n.id);
    return {
      ...n,
      position: {
        x: 600 + radius * Math.cos(angle),
        y: 400 + radius * Math.sin(angle),
      },
    };
  });

  return { positioned, newlyPlacedIds };
}

export function GraphPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["graph"], queryFn: graphApi.get });

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [typeFilter, setTypeFilter] = useState<NodeType | "">("");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [showSaved, setShowSaved] = useState(false);

  const createRelMutation = useMutation({
    mutationFn: (payload: { source_node_id: string; target_node_id: string }) =>
      relationshipsApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["graph"] }),
  });

  const deleteRelMutation = useMutation({
    mutationFn: (id: string) => relationshipsApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["graph"] }),
  });

  const savePositionsMutation = useMutation({
    mutationFn: (positions: { node_id: string; x: number; y: number }[]) =>
      graphApi.savePositions(positions),
    onSuccess: () => {
      setShowSaved(true);
      setTimeout(() => setShowSaved(false), 1500);
    },
  });

  // Batches rapid position changes (e.g. dragging several nodes back to
  // back) into a single request instead of firing one per drag.
  const pendingPositions = useRef<Map<string, { x: number; y: number }>>(new Map());
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flushPositions = useCallback(() => {
    if (pendingPositions.current.size === 0) return;
    const positions = Array.from(pendingPositions.current.entries()).map(([node_id, p]) => ({
      node_id,
      ...p,
    }));
    pendingPositions.current.clear();
    savePositionsMutation.mutate(positions);
  }, [savePositionsMutation]);
  const queuePositionSave = useCallback(
    (nodeId: string, x: number, y: number, immediate = false) => {
      pendingPositions.current.set(nodeId, { x, y });
      if (saveTimer.current) clearTimeout(saveTimer.current);
      if (immediate) {
        flushPositions();
      } else {
        saveTimer.current = setTimeout(flushPositions, 500);
      }
    },
    [flushPositions]
  );

  useEffect(() => {
    if (!data?.data) return;
    const rawNodes: FlowNode[] = (data.data.nodes as any[]).map((n) => ({
      ...n,
      position: n.position ?? { x: 0, y: 0 },
      data: { ...n.data, __saved: n.position !== null },
    }));
    const { positioned, newlyPlacedIds } = layoutNodes(rawNodes);
    setNodes(positioned);
    setEdges(
      (data.data.edges as Edge[]).map((e) => ({
        ...e,
        style: { stroke: "#4A50A8", strokeWidth: 1.2 },
        labelStyle: { fill: "#8890A8", fontSize: 10 },
      }))
    );

    // First time this graph (or these specific new nodes) has been seen -
    // persist the computed fallback layout so it's stable from now on.
    if (newlyPlacedIds.length > 0) {
      const toSave = positioned
        .filter((n) => newlyPlacedIds.includes(n.id))
        .map((n) => ({ node_id: n.id, x: n.position.x, y: n.position.y }));
      savePositionsMutation.mutate(toSave);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const connectedNodeIds = useMemo(() => {
    if (!selectedNodeId) return null;
    const set = new Set<string>([selectedNodeId]);
    edges.forEach((e) => {
      if (e.source === selectedNodeId) set.add(e.target);
      if (e.target === selectedNodeId) set.add(e.source);
    });
    return set;
  }, [selectedNodeId, edges]);

  const visibleNodes = useMemo(() => {
    return nodes
      .filter((n) => !typeFilter || n.data.nodeType === typeFilter)
      .map((n) => ({
        ...n,
        data: {
          ...n.data,
          dimmed: connectedNodeIds ? !connectedNodeIds.has(n.id) : false,
          highlighted: n.id === selectedNodeId,
        },
      }));
  }, [nodes, typeFilter, connectedNodeIds, selectedNodeId]);

  const visibleIds = useMemo(() => new Set(visibleNodes.map((n) => n.id)), [visibleNodes]);
  const visibleEdges = useMemo(
    () => edges.filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target)),
    [edges, visibleIds]
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) return;
      createRelMutation.mutate({ source_node_id: connection.source, target_node_id: connection.target });
    },
    [createRelMutation]
  );

  const onEdgeClick = useCallback(
    (_: React.MouseEvent, edge: Edge) => {
      if (confirm("Remove this connection?")) deleteRelMutation.mutate(edge.id);
    },
    [deleteRelMutation]
  );

  const onNodeClick = useCallback((_: React.MouseEvent, node: FlowNode) => {
    setSelectedNodeId((prev) => (prev === node.id ? null : node.id));
  }, []);

  const onNodeDoubleClick = useCallback(
    (_: React.MouseEvent, node: FlowNode) => navigate(`/nodes/${node.id}`),
    [navigate]
  );

  // Fires once when the user releases a dragged node - this is what makes
  // your arrangement stick. Individual drags save almost immediately;
  // dragging several nodes in quick succession gets batched.
  const onNodeDragStop = useCallback(
    (_: React.MouseEvent, node: FlowNode) => {
      queuePositionSave(node.id, node.position.x, node.position.y);
    },
    [queuePositionSave]
  );

  useEffect(() => {
    // Flush any pending save if the user navigates away mid-debounce.
    return () => flushPositions();
  }, [flushPositions]);

  if (!isLoading && nodes.length === 0) {
    return (
      <div className="max-w-lg mx-auto px-6 py-24">
        <EmptyState
          icon={<Network size={40} />}
          title="Nothing to visualize yet"
          description="Create a few nodes and connect them to see your knowledge graph come alive."
        />
      </div>
    );
  }

  return (
    <div className="h-screen relative">
      <div className="absolute top-4 left-4 z-10 flex flex-wrap gap-2 max-w-[70%]">
        <button
          onClick={() => setTypeFilter("")}
          className={`text-xs px-3 py-1.5 rounded-full border backdrop-blur-md transition-colors ${
            !typeFilter ? "border-accent text-accent bg-surface/80" : "border-border text-white/50 bg-surface/80"
          }`}
        >
          All
        </button>
        {Object.entries(NODE_TYPE_META).map(([key, meta]) => (
          <button
            key={key}
            onClick={() => setTypeFilter(key as NodeType)}
            className={`text-xs px-3 py-1.5 rounded-full border backdrop-blur-md transition-colors ${
              typeFilter === key ? "text-black" : "border-border text-white/60 bg-surface/80"
            }`}
            style={typeFilter === key ? { backgroundColor: meta.color, borderColor: meta.color } : {}}
          >
            {meta.label}
          </button>
        ))}
      </div>

      <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
        {showSaved && (
          <span className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border border-teal/40 bg-surface/80 backdrop-blur-md text-node-concept">
            <Check size={12} /> Layout saved
          </span>
        )}
        {selectedNodeId && (
          <button
            onClick={() => setSelectedNodeId(null)}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border border-border bg-surface/80 backdrop-blur-md text-white/60 hover:text-white"
          >
            <X size={12} /> Clear focus
          </button>
        )}
      </div>

      <ReactFlow
        nodes={visibleNodes}
        edges={visibleEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onEdgeClick={onEdgeClick}
        onNodeClick={onNodeClick}
        onNodeDoubleClick={onNodeDoubleClick}
        onNodeDragStop={onNodeDragStop}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.1}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#22252E" gap={24} />
        <Controls showInteractive={false} />
        <MiniMap
          pannable
          zoomable
          nodeColor={(n) => NODE_TYPE_META[(n.data as any).nodeType as NodeType]?.color ?? "#7C8CFF"}
          maskColor="rgba(11,12,16,0.7)"
          style={{ backgroundColor: "#14161C" }}
        />
      </ReactFlow>

      <div className="absolute bottom-4 left-4 z-10 text-xs text-white/30 bg-surface/80 backdrop-blur-md px-3 py-2 rounded-lg border border-border flex items-center gap-1.5">
        <Maximize2 size={11} /> Drag a node to arrange it — your layout is saved automatically · drag between nodes to connect · click an edge to remove · double-click a node to open it
      </div>
    </div>
  );
}
