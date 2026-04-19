import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  Clock3,
  Loader2,
  Sparkles,
} from "lucide-react";

import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";
import {
  type ExecutionGraphEdgeRead,
  type ExecutionGraphNodeRead,
  type ExecutionGraphRead,
} from "../../lib/api/graph";

interface ExecutionGraphViewerProps {
  graph: ExecutionGraphRead | null;
  title: string;
  subtitle: string;
  emptyTitle: string;
  emptyDescription: string;
}

function formatTime(value: string | null): string {
  if (!value) {
    return "--:--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--:--";
  }
  return date.toLocaleTimeString("vi-VN", { hour12: false });
}

function formatDatetime(value: string | null): string {
  if (!value) {
    return "--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }
  return date.toLocaleString("vi-VN", { hour12: false });
}

function formatNodeLabel(nodeId: string): string {
  return nodeId.replace(/_/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function getGraphBadgeVariant(status: ExecutionGraphRead["status"]): "optimal" | "warning" | "critical" | "neutral" {
  if (status === "completed") {
    return "optimal";
  }
  if (status === "running") {
    return "warning";
  }
  if (status === "blocked") {
    return "critical";
  }
  if (status === "failed") {
    return "critical";
  }
  return "neutral";
}

function getNodeBadgeVariant(status: ExecutionGraphNodeRead["status"]): "optimal" | "warning" | "critical" | "neutral" {
  if (status === "completed" || status === "skipped") {
    return "optimal";
  }
  if (status === "active") {
    return "warning";
  }
  if (status === "blocked") {
    return "warning";
  }
  if (status === "failed") {
    return "critical";
  }
  return "neutral";
}

function getNodeStatusText(status: ExecutionGraphNodeRead["status"]): string {
  if (status === "completed") {
    return "completed";
  }
  if (status === "active") {
    return "active";
  }
  if (status === "blocked") {
    return "blocked";
  }
  if (status === "failed") {
    return "failed";
  }
  if (status === "skipped") {
    return "skipped";
  }
  return "pending";
}

function getNodeToneClass(status: ExecutionGraphNodeRead["status"]): string {
  if (status === "completed" || status === "skipped") {
    return "border-mekong-mint/20 bg-mekong-mint/10 text-mekong-mint";
  }
  if (status === "active") {
    return "border-mekong-cyan/20 bg-mekong-cyan/10 text-mekong-cyan";
  }
  if (status === "blocked") {
    return "border-amber-200/20 bg-amber-100/10 text-amber-300";
  }
  if (status === "failed") {
    return "border-red-200/20 bg-red-100/10 text-red-300";
  }
  return "border-white/10 bg-white/5 text-slate-400";
}

function getGraphToneClass(status: ExecutionGraphRead["status"]): string {
  if (status === "completed") {
    return "border-mekong-mint/20 bg-mekong-mint/10 text-mekong-mint";
  }
  if (status === "running") {
    return "border-mekong-cyan/20 bg-mekong-cyan/10 text-mekong-cyan";
  }
  if (status === "blocked") {
    return "border-amber-200/20 bg-amber-100/10 text-amber-300";
  }
  if (status === "failed") {
    return "border-red-200/20 bg-red-100/10 text-red-300";
  }
  return "border-white/10 bg-white/5 text-slate-300";
}

type NodeBounds = {
  x: number;
  y: number;
  width: number;
  height: number;
};

function getEdgeStrokeColor(status: ExecutionGraphEdgeRead["status"]): string {
  if (status === "completed") {
    return "#1BAEA6";
  }
  if (status === "active") {
    return "#75E7FE";
  }
  if (status === "blocked") {
    return "#F59E0B";
  }
  if (status === "failed") {
    return "#EF4444";
  }
  return "#94A3B8";
}

function getEdgeLabelTone(status: ExecutionGraphEdgeRead["status"]): string {
  if (status === "completed") {
    return "text-mekong-mint bg-mekong-mint/10 border-mekong-mint/20";
  }
  if (status === "active") {
    return "text-mekong-cyan bg-mekong-cyan/10 border-mekong-cyan/20";
  }
  if (status === "blocked") {
    return "text-amber-300 bg-amber-100/10 border-amber-200/20";
  }
  if (status === "failed") {
    return "text-red-300 bg-red-100/10 border-red-200/20";
  }
  return "text-slate-400 bg-white/5 border-white/10";
}

function buildEdgePath(source: NodeBounds, target: NodeBounds): string {
  const startX = source.x + source.width;
  const startY = source.y + source.height / 2;
  const endX = target.x;
  const endY = target.y + target.height / 2;
  const distanceX = endX - startX;
  const controlOffset = Math.max(56, Math.min(180, Math.abs(distanceX) * 0.5));

  if (distanceX >= 0) {
    return `M ${startX} ${startY} C ${startX + controlOffset} ${startY}, ${endX - controlOffset} ${endY}, ${endX} ${endY}`;
  }

  return `M ${startX} ${startY} C ${startX + controlOffset} ${startY - 18}, ${endX - controlOffset} ${endY + 18}, ${endX} ${endY}`;
}

function getEdgeMidpoint(source: NodeBounds, target: NodeBounds): { x: number; y: number } {
  return {
    x: source.x + source.width + (target.x - (source.x + source.width)) / 2,
    y: source.y + source.height / 2 + (target.y + target.height / 2 - (source.y + source.height / 2)) / 2,
  };
}

function getProgressPercent(graph: ExecutionGraphRead | null): number {
  if (!graph || graph.nodes.length === 0) {
    return 0;
  }
  const completedCount = graph.nodes.filter((node) => node.status === "completed" || node.status === "skipped").length;
  return Math.round((completedCount / graph.nodes.length) * 100);
}

function getProgressWidthClass(progressPercent: number): string {
  if (progressPercent <= 0) {
    return "w-0";
  }
  if (progressPercent <= 12) {
    return "w-1/12";
  }
  if (progressPercent <= 25) {
    return "w-1/4";
  }
  if (progressPercent <= 37) {
    return "w-1/3";
  }
  if (progressPercent <= 50) {
    return "w-1/2";
  }
  if (progressPercent <= 62) {
    return "w-2/3";
  }
  if (progressPercent <= 75) {
    return "w-3/4";
  }
  if (progressPercent <= 87) {
    return "w-5/6";
  }
  return "w-full";
}

function getSelectedNode(graph: ExecutionGraphRead | null, selectedNodeId: string | null): ExecutionGraphNodeRead | null {
  if (!graph) {
    return null;
  }
  return graph.nodes.find((node) => node.id === selectedNodeId) ?? graph.nodes[0] ?? null;
}

export function ExecutionGraphViewer({
  graph,
  title,
  subtitle,
  emptyTitle,
  emptyDescription,
}: ExecutionGraphViewerProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(
    () => graph?.current_node ?? graph?.nodes[0]?.id ?? null,
  );
  const surfaceRef = useRef<HTMLDivElement | null>(null);
  const nodeRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const [nodeBounds, setNodeBounds] = useState<Record<string, NodeBounds>>({});

  const selectedNode = useMemo(() => getSelectedNode(graph, selectedNodeId), [graph, selectedNodeId]);
  const progressPercent = useMemo(() => getProgressPercent(graph), [graph]);
  const completedCount = graph ? graph.nodes.filter((node) => node.status === "completed" || node.status === "skipped").length : 0;
  const currentNodeLabel = graph?.current_node ? formatNodeLabel(graph.current_node) : "--";

  const measureGraph = useCallback(() => {
    const surface = surfaceRef.current;
    if (!surface || !graph) {
      return;
    }

    const surfaceRect = surface.getBoundingClientRect();
    const nextBounds: Record<string, NodeBounds> = {};

    graph.nodes.forEach((node) => {
      const element = nodeRefs.current[node.id];
      if (!element) {
        return;
      }
      const rect = element.getBoundingClientRect();
      nextBounds[node.id] = {
        x: rect.left - surfaceRect.left,
        y: rect.top - surfaceRect.top,
        width: rect.width,
        height: rect.height,
      };
    });

    setNodeBounds(nextBounds);
  }, [graph]);

  useEffect(() => {
    if (!graph || graph.nodes.length === 0) {
      return;
    }

    const surface = surfaceRef.current;
    if (!surface) {
      return;
    }

    let animationFrameId = window.requestAnimationFrame(measureGraph);
    const resizeObserver = new ResizeObserver(() => {
      window.cancelAnimationFrame(animationFrameId);
      animationFrameId = window.requestAnimationFrame(measureGraph);
    });

    resizeObserver.observe(surface);
    window.addEventListener("resize", measureGraph);

    return () => {
      window.cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", measureGraph);
      resizeObserver.disconnect();
    };
  }, [graph, measureGraph]);

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="rounded-3xl border border-dashed border-white/15 bg-white/5 p-6 text-center space-y-3">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-mekong-cyan/20 bg-mekong-cyan/10 text-mekong-cyan">
          <Sparkles size={20} />
        </div>
        <p className="text-sm font-bold text-slate-200">{emptyTitle}</p>
        <p className="text-[12px] leading-relaxed text-slate-400">{emptyDescription}</p>
      </div>
    );
  }

  return (
    <Card variant="navy" className="rounded-4xl border border-white/10 bg-[#00203F] p-6 shadow-2xl">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="space-y-2 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-2.5 text-mekong-cyan shadow-xl">
              <BrainCircuit size={20} />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-black uppercase tracking-[0.18em] text-white">{title}</h3>
              <p className="mt-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">{subtitle}</p>
            </div>
          </div>
          <p className="text-[12px] leading-relaxed text-slate-300">
            Graph contract chuẩn hóa từ backend để FE hiển thị node, edge, trạng thái và chi tiết thực thi.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <Badge variant={getGraphBadgeVariant(graph.status)} className={`px-2 py-0.5 text-[9px] font-bold ${getGraphToneClass(graph.status)}`}>
            {graph.graph_type}
          </Badge>
          <Badge variant={getGraphBadgeVariant(graph.status)} className={`px-2 py-0.5 text-[9px] font-bold ${getGraphToneClass(graph.status)}`}>
            {graph.status}
          </Badge>
          <Badge variant="neutral" className="border-white/10 bg-white/10 px-2 py-0.5 text-[9px] font-bold text-slate-200">
            Current: {currentNodeLabel}
          </Badge>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">Nodes</p>
          <p className="mt-2 text-sm font-black text-white">{graph.nodes.length}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">Completed</p>
          <p className="mt-2 text-sm font-black text-white">{completedCount}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">Progress</p>
          <p className="mt-2 text-sm font-black text-white">{progressPercent}%</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">Time</p>
          <p className="mt-2 text-sm font-black text-white">{formatTime(graph.started_at)}</p>
        </div>
      </div>

      <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/10">
        <div
          className={`h-full rounded-full bg-linear-to-r from-mekong-teal via-mekong-cyan to-mekong-mint transition-all duration-700 ${getProgressWidthClass(progressPercent)}`}
        />
      </div>

      {graph.summary ? (
        <div className={`mt-5 rounded-3xl border p-4 ${getGraphToneClass(graph.status)}`}>
          <div className="flex items-center gap-2 text-white">
            <Clock3 size={14} />
            <p className="text-[10px] font-black uppercase tracking-[0.2em]">Graph summary</p>
          </div>
          <p className="mt-2 text-[13px] font-semibold leading-relaxed text-slate-100">{graph.summary}</p>
          <p className="mt-2 text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">
            Start {formatDatetime(graph.started_at)} · Finish {formatDatetime(graph.completed_at)}
          </p>
        </div>
      ) : null}

      <div className="mt-5 rounded-3xl border border-white/10 bg-black/10 p-4">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-mekong-cyan">
              <ArrowRight size={14} />
              <p className="text-[10px] font-black uppercase tracking-[0.2em]">Node canvas</p>
            </div>
            <p className="text-[12px] leading-relaxed text-slate-300">
              Edges được vẽ từ source/target thật của backend, bám theo vị trí thực của node cards.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="neutral" className="border-white/10 bg-white/10 px-2 py-0.5 text-[9px] font-bold text-slate-200">
              {graph.edges.length} edges
            </Badge>
          </div>
        </div>

        <div ref={surfaceRef} className="relative w-full overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-4">
          <div className="relative w-full">
            <svg className="pointer-events-none absolute inset-0 h-full w-full" aria-hidden="true">
              <defs>
                <marker
                  id="graph-arrow-head"
                  markerWidth="10"
                  markerHeight="10"
                  refX="8"
                  refY="3"
                  orient="auto"
                  markerUnits="strokeWidth"
                >
                  <path d="M0,0 L0,6 L8,3 z" fill="#94A3B8" />
                </marker>
              </defs>

              {graph.edges.map((edge, index) => {
                const sourceBounds = nodeBounds[edge.source];
                const targetBounds = nodeBounds[edge.target];
                if (!sourceBounds || !targetBounds) {
                  return null;
                }

                const path = buildEdgePath(sourceBounds, targetBounds);
                const midpoint = getEdgeMidpoint(sourceBounds, targetBounds);
                const strokeColor = getEdgeStrokeColor(edge.status);
                const highlighted = selectedNode?.id === edge.source || selectedNode?.id === edge.target;

                return (
                  <g key={`${edge.source}-${edge.target}-${index}`}>
                    <title>{`${edge.source} → ${edge.target}${edge.label ? ` · ${edge.label}` : ""}`}</title>
                    <path
                      d={path}
                      fill="none"
                      stroke={strokeColor}
                      strokeWidth={highlighted ? 3 : 2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeDasharray={edge.status === "blocked" ? "8 8" : edge.status === "pending" ? "4 8" : undefined}
                      markerEnd="url(#graph-arrow-head)"
                      opacity={highlighted ? 1 : 0.72}
                    />
                    {edge.label ? (
                      <g transform={`translate(${midpoint.x}, ${midpoint.y})`}>
                        <rect
                          x="-40"
                          y="-11"
                          rx="11"
                          ry="11"
                          width="80"
                          height="22"
                          className={`${getEdgeLabelTone(edge.status)} rounded-full border`}
                        />
                        <text
                          x="0"
                          y="4"
                          textAnchor="middle"
                          className="fill-current text-[10px] font-black uppercase tracking-[0.14em]"
                        >
                          {edge.label}
                        </text>
                      </g>
                    ) : null}
                  </g>
                );
              })}
            </svg>

            <div className="relative flex flex-wrap gap-4">
              {graph.nodes.map((node) => {
                const isSelected = selectedNode?.id === node.id;
                return (
                  <button
                    key={node.id}
                    ref={(element) => {
                      nodeRefs.current[node.id] = element;
                    }}
                    type="button"
                    onClick={() => setSelectedNodeId(node.id)}
                    className={`group w-56 rounded-3xl border p-4 text-left transition-all duration-300 ${
                      isSelected
                        ? "border-mekong-cyan/30 bg-white/12 shadow-[0_16px_50px_-24px_rgba(0,0,0,0.8)] scale-[1.01]"
                        : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">
                          {node.step_index ? `Step ${node.step_index}` : "Node"}
                        </p>
                        <h4 className="mt-2 text-sm font-black text-white line-clamp-2">{node.label}</h4>
                      </div>
                      <Badge
                        variant={getNodeBadgeVariant(node.status)}
                        className={`text-[8px] px-2 py-0.5 font-bold ${getNodeToneClass(node.status)}`}
                      >
                        {getNodeStatusText(node.status)}
                      </Badge>
                    </div>

                    <div className="mt-4 flex items-center gap-3">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-2xl border ${getNodeToneClass(node.status)}`}>
                        {node.status === "completed" || node.status === "skipped" ? (
                          <CheckCircle2 size={18} />
                        ) : node.status === "active" ? (
                          <Loader2 size={18} className="animate-spin" />
                        ) : node.status === "failed" ? (
                          <AlertTriangle size={16} />
                        ) : (
                          <span className="text-[11px] font-black">{node.step_index ?? 0}</span>
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-500">{node.kind}</p>
                        <p className="mt-1 text-[11px] font-semibold leading-relaxed text-slate-300 line-clamp-2">
                          {node.summary ?? "Chưa có summary."}
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 flex items-center justify-between gap-2 text-[10px] font-black uppercase tracking-[0.15em] text-slate-500">
                      <span>{formatTime(node.started_at)}</span>
                      <span>{formatNodeLabel(node.id)}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

      </div>

      <div className="mt-5 rounded-3xl border border-white/10 bg-black/10 p-5 space-y-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-1 min-w-0">
            <div className="flex items-center gap-2 text-mekong-cyan">
              <ArrowRight size={14} />
              <p className="text-[10px] font-black uppercase tracking-[0.2em]">Node detail</p>
            </div>
            <h4 className="text-sm font-black text-white uppercase tracking-[0.08em]">
              {selectedNode?.label ?? "--"}
            </h4>
            <p className="text-[12px] leading-relaxed text-slate-300">
              {selectedNode?.summary ?? "Chưa có summary cho node đang chọn."}
            </p>
          </div>
          <div className="flex flex-wrap gap-2 shrink-0">
            <Badge variant={selectedNode ? getNodeBadgeVariant(selectedNode.status) : "neutral"} className="text-[8px] px-2 py-0.5 font-bold">
              {selectedNode?.status ?? "pending"}
            </Badge>
            <Badge variant="neutral" className="bg-white/10 text-slate-200 border-white/10 text-[8px] px-2 py-0.5 font-bold">
              {selectedNode?.kind ?? "node"}
            </Badge>
            <Badge variant="neutral" className="bg-white/10 text-slate-200 border-white/10 text-[8px] px-2 py-0.5 font-bold">
              {selectedNode?.id ?? "--"}
            </Badge>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Started</p>
            <p className="mt-2 text-[11px] font-bold text-white">{formatDatetime(selectedNode?.started_at ?? null)}</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Completed</p>
            <p className="mt-2 text-[11px] font-bold text-white">{formatDatetime(selectedNode?.completed_at ?? null)}</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Step index</p>
            <p className="mt-2 text-[11px] font-bold text-white">{selectedNode?.step_index ?? "--"}</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Graph type</p>
            <p className="mt-2 text-[11px] font-bold text-white">{graph.graph_type}</p>
          </div>
        </div>

        {selectedNode?.details && Object.keys(selectedNode.details).length > 0 ? (
          <div className="space-y-2">
            <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Details</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(selectedNode.details).slice(0, 6).map(([key, value]) => (
                <span
                  key={key}
                  className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-slate-300"
                >
                  {key}: {typeof value === "string" ? value : JSON.stringify(value)}
                </span>
              ))}
            </div>
          </div>
        ) : null}
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-white/10 pt-5">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="neutral" className="bg-white/10 text-slate-200 border-white/10 text-[9px] px-2 py-0.5 font-bold uppercase">
            {graph.edges.length} edges
          </Badge>
          {graph.metadata?.action_plan_id ? (
            <Badge variant="neutral" className="bg-white/10 text-slate-200 border-white/10 text-[9px] px-2 py-0.5 font-bold uppercase">
              plan {String(graph.metadata.action_plan_id).slice(0, 8)}
            </Badge>
          ) : null}
        </div>
        <p className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.2em]">
          Updated {formatTime(graph.completed_at ?? graph.started_at)}
        </p>
      </div>
    </Card>
  );
}
