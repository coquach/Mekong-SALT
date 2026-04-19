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
import { Link } from "react-router-dom";

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

function getGraphTypeLabel(graphType: ExecutionGraphRead["graph_type"]): string {
  if (graphType === "planning") {
    return "Lập kế hoạch";
  }
  if (graphType === "execution_batch") {
    return "Thực thi";
  }
  return graphType.replace(/_/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function getGraphStatusLabel(status: ExecutionGraphRead["status"]): string {
  if (status === "completed") {
    return "Hoàn tất";
  }
  if (status === "running") {
    return "Đang chạy";
  }
  if (status === "blocked") {
    return "Bị chặn";
  }
  if (status === "failed") {
    return "Lỗi";
  }
  return "Đang chờ";
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
    return "Hoàn tất";
  }
  if (status === "active") {
    return "Đang chạy";
  }
  if (status === "blocked") {
    return "Bị chặn";
  }
  if (status === "failed") {
    return "Lỗi";
  }
  if (status === "skipped") {
    return "Bỏ qua";
  }
  return "Chờ xử lý";
}

function isTechnicalDetailKey(key: string): boolean {
  return /(^|_)id$/.test(key) || key.endsWith("_id") || key === "id";
}

function formatDetailLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatDetailValue(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return `${value.length} mục`;
  }
  if (value && typeof value === "object") {
    const keys = Object.keys(value as Record<string, unknown>);
    return keys.length > 0 ? `${keys.length} trường chi tiết` : "Có chi tiết bổ sung";
  }
  return "Có chi tiết bổ sung";
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

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function getRetrievalTrace(graph: ExecutionGraphRead | null): Record<string, unknown> | null {
  const metadata = graph?.metadata;
  if (!isRecord(metadata)) {
    return null;
  }
  const retrievalTrace = metadata.retrieval_trace;
  return isRecord(retrievalTrace) ? retrievalTrace : null;
}

function formatCitationTitle(value: unknown): string {
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) {
      return "Không có tiêu đề";
    }
    if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
      return trimmed;
    }
    return trimmed;
  }
  return "Không có tiêu đề";
}

function formatCitationSource(value: unknown): string {
  if (typeof value === "string" && value.trim().length > 0) {
    return value.trim();
  }
  return "unknown";
}

function formatCitationScore(value: unknown): string {
  if (typeof value === "number") {
    return value.toFixed(2);
  }
  if (typeof value === "string" && value.trim().length > 0) {
    return value.trim();
  }
  return "--";
}

function getNodeSummaryText(node: ExecutionGraphNodeRead | null): string {
  if (!node) {
    return "Chưa có mô tả cho bước này.";
  }
  if (node.summary) {
    return node.summary;
  }
  if (node.details && typeof node.details === "object") {
    const details = node.details as Record<string, unknown>;
    if (typeof details.objective === "string" && details.objective.trim().length > 0) {
      return `Bám mục tiêu: ${details.objective}.`;
    }
    if (typeof details.risk_level === "string" && details.risk_level.trim().length > 0) {
      return `Rủi ro được đánh giá ở mức ${details.risk_level}.`;
    }
    if (typeof details.summary === "string" && details.summary.trim().length > 0) {
      return details.summary;
    }
    if (typeof details.evidence_count === "number") {
      return `Truy xuất ${details.evidence_count} bằng chứng hỗ trợ.`;
    }
    if (typeof details.step_count === "number") {
      return `Soạn kế hoạch gồm ${details.step_count} bước.`;
    }
    if (typeof details.is_valid === "boolean") {
      return details.is_valid
        ? "Kế hoạch đã được xác thực và không có lỗi nổi bật."
        : "Kế hoạch đã được xác thực nhưng cần chỉnh sửa trước khi tiếp tục.";
    }
  }
  return "Chưa có mô tả cho bước này.";
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
  const graphStatus = graph?.status ?? "pending";
  const graphType = graph?.graph_type ?? "planning";
  const graphNodes = graph?.nodes ?? [];
  const graphEdges = graph?.edges ?? [];
  const graphStartedAt = graph?.started_at ?? null;
  const graphCompletedAt = graph?.completed_at ?? null;
  const completedCount = graphNodes.filter((node) => node.status === "completed" || node.status === "skipped").length;
  const currentNodeLabel = selectedNode?.label ?? selectedNode?.summary ?? "Chưa rõ";
  const retrievalTrace = useMemo(() => getRetrievalTrace(graph), [graph]);
  const retrievalTopCitations = useMemo(() => {
    const topCitations = retrievalTrace?.top_citations;
    if (!Array.isArray(topCitations)) {
      return [];
    }
    return topCitations.filter(isRecord).slice(0, 5);
  }, [retrievalTrace]);
  const retrievalMemoryCases = useMemo(
    () => retrievalTopCitations.filter((citation) => citation.evidence_source === "memory_case" || citation.source === "memory_case"),
    [retrievalTopCitations],
  );
  const hasGraph = Boolean(graph && graph.nodes.length > 0);

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
          <Badge variant={getGraphBadgeVariant(graphStatus)} className={`px-2 py-0.5 text-[9px] font-bold ${getGraphToneClass(graphStatus)}`}>
            {graph ? getGraphTypeLabel(graphType) : "Chờ dữ liệu"}
          </Badge>
          <Badge variant={getGraphBadgeVariant(graphStatus)} className={`px-2 py-0.5 text-[9px] font-bold ${getGraphToneClass(graphStatus)}`}>
            {graph ? getGraphStatusLabel(graphStatus) : "Đang chờ"}
          </Badge>
          <Badge variant="neutral" className="border-white/10 bg-white/10 px-2 py-0.5 text-[9px] font-bold text-slate-200">
            Đang xem: {currentNodeLabel}
          </Badge>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">Các bước</p>
          <p className="mt-2 text-sm font-black text-white">{graphNodes.length}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">Đã xong</p>
          <p className="mt-2 text-sm font-black text-white">{completedCount}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">Tiến độ</p>
          <p className="mt-2 text-sm font-black text-white">{progressPercent}%</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">Cập nhật</p>
          <p className="mt-2 text-sm font-black text-white">{formatTime(graphStartedAt)}</p>
        </div>
      </div>

      <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/10">
        <div
          className={`h-full rounded-full bg-linear-to-r from-mekong-teal via-mekong-cyan to-mekong-mint transition-all duration-700 ${getProgressWidthClass(progressPercent)}`}
        />
      </div>

      {graph?.summary ? (
        <div className={`mt-5 rounded-3xl border p-4 ${getGraphToneClass(graphStatus)}`}>
          <div className="flex items-center gap-2 text-white">
            <Clock3 size={14} />
            <p className="text-[10px] font-black uppercase tracking-[0.2em]">Tóm tắt luồng</p>
          </div>
          <p className="mt-2 text-[13px] font-semibold leading-relaxed text-slate-100">{graph.summary}</p>
          <p className="mt-2 text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">
            Start {formatDatetime(graphStartedAt)} · Finish {formatDatetime(graphCompletedAt)}
          </p>
        </div>
      ) : null}

      <div className="mt-5 rounded-3xl border border-white/10 bg-black/10 p-4">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-mekong-cyan">
              <ArrowRight size={14} />
              <p className="text-[10px] font-black uppercase tracking-[0.2em]">Canvas node</p>
            </div>
            <p className="text-[12px] leading-relaxed text-slate-300">
              {hasGraph ? "Edges được vẽ từ source/target thật của backend, bám theo vị trí thực của node cards." : emptyDescription}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="neutral" className="border-white/10 bg-white/10 px-2 py-0.5 text-[9px] font-bold text-slate-200">
              {graphEdges.length} edges
            </Badge>
          </div>
        </div>

        {hasGraph ? (
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

                {graphEdges.map((edge, index) => {
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
                {graphNodes.map((node) => {
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
                        <p className="mt-1 text-[11px] font-semibold leading-relaxed text-slate-300 line-clamp-2">
                          {getNodeSummaryText(node)}
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 flex items-center justify-between gap-2 text-[10px] font-black uppercase tracking-[0.15em] text-slate-500">
                      <span>{formatTime(node.started_at)}</span>
                      <span>{node.step_index ? `Bước ${node.step_index}` : "Trong luồng"}</span>
                    </div>
                  </button>
                );
                })}
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-3xl border border-dashed border-white/15 bg-white/5 p-5">
            <div className="mb-4 flex items-center gap-2 text-mekong-cyan">
              <Sparkles size={14} />
              <p className="text-[10px] font-black uppercase tracking-[0.2em]">{emptyTitle}</p>
            </div>
            <p className="mb-4 text-[12px] leading-relaxed text-slate-300">{emptyDescription}</p>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 4 }, (_, index) => index + 1).map((stepIndex) => (
                <div key={stepIndex} className="rounded-3xl border border-white/10 bg-white/5 p-4">
                  <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">Step {stepIndex}</p>
                  <div className="mt-3 h-3 w-2/3 rounded-full bg-white/10" />
                  <div className="mt-3 h-3 w-full rounded-full bg-white/10" />
                  <div className="mt-2 h-3 w-5/6 rounded-full bg-white/10" />
                  <div className="mt-4 flex items-center justify-between">
                    <div className="h-6 w-16 rounded-full bg-white/10" />
                    <div className="h-6 w-12 rounded-full bg-white/10" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>

      <div className="mt-5 rounded-3xl border border-white/10 bg-black/10 p-5 space-y-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-1 min-w-0">
            <div className="flex items-center gap-2 text-mekong-cyan">
              <ArrowRight size={14} />
              <p className="text-[10px] font-black uppercase tracking-[0.2em]">Chi tiết node</p>
            </div>
            <h4 className="text-sm font-black text-white uppercase tracking-[0.08em]">
              {selectedNode?.label ?? "--"}
            </h4>
            <p className="text-[12px] leading-relaxed text-slate-300">
              {getNodeSummaryText(selectedNode)}
            </p>
          </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <Badge variant={selectedNode ? getNodeBadgeVariant(selectedNode.status) : "neutral"} className="text-[8px] px-2 py-0.5 font-bold">
            {selectedNode?.status ?? "pending"}
          </Badge>
        </div>
      </div>

        <div className="space-y-3">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Bắt đầu</p>
            <p className="mt-2 text-[11px] font-bold text-white">{formatDatetime(selectedNode?.started_at ?? null)}</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Hoàn tất</p>
            <p className="mt-2 text-[11px] font-bold text-white">{formatDatetime(selectedNode?.completed_at ?? null)}</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Thứ tự</p>
            <p className="mt-2 text-[11px] font-bold text-white">
              {selectedNode?.step_index ? `Bước ${selectedNode.step_index}` : "Trong luồng"}
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Loại luồng</p>
              <p className="mt-2 text-[11px] font-bold text-white">{getGraphTypeLabel(graphType)}</p>
          </div>
        </div>

        {selectedNode?.details && Object.keys(selectedNode.details).length > 0 ? (
          <div className="space-y-2">
            <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Chi tiết thêm</p>
            <div className="space-y-2">
              {Object.entries(selectedNode.details)
                .filter(([key]) => !isTechnicalDetailKey(key))
                .slice(0, 6)
                .map(([key, value]) => (
                  <div key={key} className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2">
                    <p className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-500">{formatDetailLabel(key)}</p>
                    <p className="mt-1 text-[11px] font-semibold leading-relaxed text-slate-300">{formatDetailValue(value)}</p>
                  </div>
                ))}
            </div>
          </div>
        ) : null}

          {selectedNode?.id === "retrieve_context" && retrievalTrace ? (
            <div className="space-y-3 rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Truy xuất ngữ cảnh</p>
                <Badge variant="neutral" className="bg-white/10 text-slate-200 border-white/10 text-[8px] px-2 py-0.5 font-bold">
                  {typeof retrievalTrace.total_evidence === "number" ? `${retrievalTrace.total_evidence} evidence` : "0 evidence"}
                </Badge>
              </div>

              <div className="flex flex-wrap gap-2">
                {isRecord(retrievalTrace.source_counts)
                  ? Object.entries(retrievalTrace.source_counts).map(([source, count]) => (
                      <Badge
                        key={source}
                        variant="neutral"
                        className="bg-white/10 text-slate-200 border-white/10 text-[8px] px-2 py-0.5 font-bold uppercase"
                      >
                        {source}: {String(count)}
                      </Badge>
                    ))
                  : null}
              </div>

              {retrievalTopCitations.length > 0 ? (
                <div className="space-y-2">
                  {retrievalTopCitations.map((citation, index) => (
                    <div key={`${citation.rank ?? index}-${index}`} className="rounded-2xl border border-white/10 bg-black/10 p-3">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-500">
                            #{String(citation.rank ?? index + 1)} · {formatCitationSource(citation.source ?? citation.evidence_source)}
                          </p>
                          <p className="mt-1 text-[12px] font-black leading-relaxed text-white">
                            {formatCitationTitle(citation.title ?? citation.citation)}
                          </p>
                        </div>
                        <Badge variant="neutral" className="bg-white/10 text-slate-200 border-white/10 text-[8px] px-2 py-0.5 font-bold">
                          {formatCitationScore(citation.score)}
                        </Badge>
                      </div>
                      {typeof citation.source_uri === "string" && citation.source_uri.trim().length > 0 ? (
                        <p className="mt-2 break-all text-[10px] leading-relaxed text-slate-400">
                          {citation.source_uri}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : null}

              {retrievalMemoryCases.length > 0 ? (
                <div className="space-y-3 rounded-2xl border border-mekong-cyan/20 bg-mekong-cyan/10 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-[9px] font-black uppercase tracking-[0.2em] text-mekong-cyan">Memory case</p>
                    <Badge variant="neutral" className="bg-white/10 text-slate-200 border-white/10 text-[8px] px-2 py-0.5 font-bold">
                      {retrievalMemoryCases.length} mục
                    </Badge>
                  </div>
                  <p className="text-[12px] leading-relaxed text-slate-300">
                    Các memory case đã được tách sang trang riêng để xem đầy đủ ID, thời điểm và ngữ cảnh.
                  </p>
                  <Link
                    to="/memory-cases"
                    state={{
                      sourceTitle: title,
                      sourceSubtitle: subtitle,
                      sourceGraphType: graph ? getGraphTypeLabel(graphType) : null,
                      sourceGraphStatus: graph ? getGraphStatusLabel(graphStatus) : null,
                      sourceGraphSummary: graph?.summary ?? null,
                      memoryCases: retrievalMemoryCases,
                    }}
                    className="inline-flex w-full items-center justify-center rounded-xl border border-mekong-cyan/20 bg-white/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.14em] text-white transition-colors hover:border-mekong-cyan/40 hover:bg-white/15"
                  >
                    Mở trang memory case
                  </Link>
                </div>
              ) : null}
            </div>
          ) : null}
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-white/10 pt-5">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="neutral" className="bg-white/10 text-slate-200 border-white/10 text-[9px] px-2 py-0.5 font-bold uppercase">
            {graphEdges.length} edges
          </Badge>
        </div>
        <p className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.2em]">
          Cập nhật {formatTime(graphCompletedAt ?? graphStartedAt)}
        </p>
      </div>
    </Card>
  );
}
