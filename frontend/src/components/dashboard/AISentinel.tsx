import { BrainCircuit, CheckCircle2, Clock3, Loader2, Sparkles, Terminal } from "lucide-react";

import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";
import { type AgentRunRead } from "../../lib/api/strategy";

type StreamStatus = "connecting" | "connected" | "disconnected";

type PlanningTrace = {
  incident_decision?: {
    decision?: string;
    reason?: string;
  };
  plan_decision?: {
    decision?: string;
    reason?: string;
    action_plan_id?: string;
  };
  retrieval_trace?: {
    total_evidence?: number;
    source_counts?: Record<string, unknown>;
    top_citations?: Array<{
      citation?: string;
      source?: string;
      score?: number;
      rank?: number;
    }>;
  };
  planning_transition_log?: Array<{
    node?: string;
    status?: string;
  }>;
};

type PlanningStageState = "completed" | "active" | "pending";

type PlanningStage = {
  node: string;
  title: string;
  subtitle: string;
};

const PLANNING_STAGES: PlanningStage[] = [
  {
    node: "observe",
    title: "1. Quan sát",
    subtitle: "Chuẩn hóa request và filters đầu vào.",
  },
  {
    node: "assess_risk",
    title: "2. Đánh giá rủi ro",
    subtitle: "Tính rủi ro từ reading hiện tại và weather context.",
  },
  {
    node: "retrieve_context",
    title: "3. Truy xuất ngữ cảnh",
    subtitle: "Truy xuất evidence, citation và Earth Engine context.",
  },
  {
    node: "draft_plan",
    title: "4. Soạn kế hoạch",
    subtitle: "Sinh action plan theo objective và ngữ cảnh.",
  },
  {
    node: "validate_plan",
    title: "5. Xác thực kế hoạch",
    subtitle: "Kiểm tra policy guard trước khi chốt trace.",
  },
];

interface AgentReasoningPanelProps {
  agentRun: AgentRunRead | null;
  streamStatus: StreamStatus;
  lastStreamAt: string | null;
}

function formatTime(value: string | null): string {
  if (!value) {
    return "--:--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--:--";
  }
  return date.toLocaleTimeString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function getStreamStatusText(status: StreamStatus): string {
  if (status === "connected") {
    return "Realtime bật";
  }
  if (status === "connecting") {
    return "Đang kết nối";
  }
  return "Realtime tắt";
}

function getStreamStatusClass(status: StreamStatus): string {
  if (status === "connected") {
    return "bg-mekong-cyan/10 text-mekong-cyan border-mekong-cyan/20";
  }
  if (status === "connecting") {
    return "bg-amber-100/10 text-amber-300 border-amber-200/20";
  }
  return "bg-red-100/10 text-red-300 border-red-200/20";
}

function getPlanningTrace(run: AgentRunRead | null): PlanningTrace | null {
  if (!run || typeof run.trace !== "object" || run.trace === null || Array.isArray(run.trace)) {
    return null;
  }
  return run.trace as PlanningTrace;
}

function getRunObjective(run: AgentRunRead | null): string | null {
  if (!run || typeof run.payload !== "object" || run.payload === null || Array.isArray(run.payload)) {
    return null;
  }
  const request = (run.payload as Record<string, unknown>).request;
  if (!request || typeof request !== "object" || Array.isArray(request)) {
    return null;
  }
  const objective = (request as Record<string, unknown>).objective;
  return typeof objective === "string" ? objective : null;
}

function getNodeLabel(node: string | undefined): string {
  if (!node) {
    return "Không rõ";
  }
  return node
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatCompactId(value: string | null | undefined): string {
  if (!value) {
    return "--";
  }
  return value.length > 10 ? `${value.slice(0, 6)}…${value.slice(-4)}` : value;
}

function getStageState(
  stageNode: string,
  completedNodes: Set<string>,
  lastCompletedNode: string | null,
  isTerminalRun: boolean,
): PlanningStageState {
  if (!completedNodes.has(stageNode)) {
    return "pending";
  }
  if (!isTerminalRun && stageNode === lastCompletedNode) {
    return "active";
  }
  return "completed";
}

function getStageCardClass(stageState: PlanningStageState): string {
  if (stageState === "active") {
    return "border-mekong-cyan/30 bg-gradient-to-r from-mekong-cyan/12 to-white/5 shadow-[0_0_0_1px_rgba(117,231,254,0.12)]";
  }
  if (stageState === "completed") {
    return "border-white/10 bg-white/5";
  }
  return "border-white/5 bg-white/[0.03] opacity-75";
}

function getStageDotClass(stageState: PlanningStageState): string {
  if (stageState === "active") {
    return "bg-mekong-cyan text-mekong-navy ring-4 ring-mekong-cyan/20 animate-pulse";
  }
  if (stageState === "completed") {
    return "bg-mekong-mint text-mekong-navy";
  }
  return "bg-white/10 text-slate-400";
}

function getStageStatusText(stageState: PlanningStageState): string {
  if (stageState === "active") {
    return "đang chạy";
  }
  if (stageState === "completed") {
    return "hoàn tất";
  }
  return "chờ";
}

function getStageStatusClass(stageState: PlanningStageState): string {
  if (stageState === "active") {
    return "bg-mekong-cyan/10 text-mekong-cyan border-mekong-cyan/20";
  }
  if (stageState === "completed") {
    return "bg-mekong-mint/10 text-mekong-mint border-mekong-mint/20";
  }
  return "bg-white/5 text-slate-400 border-white/10";
}

function getProgressWidthClass(progressPercent: number): string {
  if (progressPercent <= 0) {
    return "w-0";
  }
  if (progressPercent <= 20) {
    return "w-1/5";
  }
  if (progressPercent <= 40) {
    return "w-2/5";
  }
  if (progressPercent <= 60) {
    return "w-3/5";
  }
  if (progressPercent <= 80) {
    return "w-4/5";
  }
  return "w-full";
}

export const AISentinel = ({ agentRun, streamStatus, lastStreamAt }: AgentReasoningPanelProps) => {
  const trace = getPlanningTrace(agentRun);
  const transitions = trace?.planning_transition_log ?? [];
  const retrievalTrace = trace?.retrieval_trace;
  const evidenceCount = retrievalTrace?.total_evidence ?? 0;
  const citationsCount = retrievalTrace?.top_citations?.length ?? 0;
  const topCitations = retrievalTrace?.top_citations?.slice(0, 3) ?? [];
  const objective = getRunObjective(agentRun);
  const planDecision = trace?.plan_decision;
  const incidentDecision = trace?.incident_decision;
  const statusLabel = agentRun ? `Run ${agentRun.status}` : "Awaiting agent run";
  const runAt = agentRun?.finished_at ?? agentRun?.started_at ?? null;
  const completedNodes = new Set(
    transitions
      .map((step) => step.node)
      .filter((node): node is string => typeof node === "string" && node.length > 0),
  );
  const lastCompletedNode = transitions[transitions.length - 1]?.node ?? null;
  const isTerminalRun = Boolean(
    agentRun && /succeeded|failed|cancelled|canceled|completed/i.test(agentRun.status),
  );
  const completionPercent = Math.round(
    (Math.min(completedNodes.size, PLANNING_STAGES.length) / PLANNING_STAGES.length) * 100,
  );
  const visualStages = PLANNING_STAGES.map((stage, index) => ({
    ...stage,
    index: index + 1,
    state: getStageState(stage.node, completedNodes, lastCompletedNode, isTerminalRun),
  }));

  return (
    <Card variant="navy" className="h-full p-8 flex flex-col rounded-4xl border border-white/5">
      <div className="relative z-10 flex items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-4 min-w-0">
          <div className="p-3 bg-mekong-cyan/10 rounded-2xl text-mekong-cyan border border-mekong-cyan/20 ring-4 ring-mekong-cyan/5 shrink-0">
            <BrainCircuit size={28} strokeWidth={2.5} />
          </div>
          <div className="min-w-0">
            <h3 className="text-lg font-black tracking-tight leading-none">
              AI Sentinel
            </h3>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mt-2">
              Trace theo từng node, cập nhật từ run mới nhất
            </p>
          </div>
        </div>
        <Badge className={`${getStreamStatusClass(streamStatus)} text-[9px] py-0.5 px-2 font-bold`}>
          {getStreamStatusText(streamStatus)}
        </Badge>
      </div>

      <div className="relative z-10 space-y-5 flex-1 min-h-0">
        <div className="rounded-card border border-white/10 bg-white/5 p-5 space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Terminal size={16} className="text-mekong-cyan" />
              <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
                {statusLabel}
              </span>
            </div>
            <div className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
              <Clock3 size={14} />
              {formatTime(lastStreamAt)}
            </div>
          </div>

          <p className="text-sm leading-relaxed text-slate-200">
            {objective ? `Mục tiêu: ${objective}` : "Đang chờ trace agent mới từ backend."}
          </p>

          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
                <Sparkles size={13} className="text-mekong-cyan" />
                {completedNodes.size}/{PLANNING_STAGES.length} bước
              </div>
              <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
                {completionPercent}%
              </div>
            </div>
            <div className="h-2 rounded-full bg-white/10 overflow-hidden">
              <div
                className={`h-full rounded-full bg-linear-to-r from-mekong-teal via-mekong-cyan to-mekong-mint transition-all duration-700 ${getProgressWidthClass(completionPercent)}`}
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge variant="info" className="border-white/10 bg-white/10 text-[9px] px-2 py-0.5">
              Plan {planDecision?.decision ?? "pending"}
            </Badge>
            <Badge variant="neutral" className="border-white/10 bg-white/10 text-[9px] px-2 py-0.5">
              Evidence {evidenceCount}
            </Badge>
            <Badge variant="optimal" className="border-white/10 bg-white/10 text-[9px] px-2 py-0.5">
              Citations {citationsCount}
            </Badge>
            <Badge className="border-white/10 bg-white/10 text-[9px] px-2 py-0.5 text-slate-300">
              Trace {transitions.length}
            </Badge>
          </div>

          {topCitations.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {topCitations.map((citation, index) => (
                <Badge
                  key={`${citation.source ?? citation.citation ?? "citation"}-${index}`}
                  className="border-white/10 bg-white/5 text-[9px] px-2 py-0.5 text-slate-300"
                >
                  {index + 1}. {citation.source ?? citation.citation ?? "Nguồn"}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>

        <div className="flex-1 min-h-0 overflow-y-auto pr-1 custom-scrollbar space-y-3">
          {visualStages.map((stage, index) => (
            <div
              key={stage.node}
              className={`group relative overflow-hidden rounded-3xl border p-4 transition-all ${getStageCardClass(stage.state)}`}
            >
              <div className="absolute left-0 top-0 h-full w-1 bg-linear-to-b from-mekong-cyan/20 via-mekong-teal/20 to-transparent" />
              <div className="flex items-start gap-4 pl-2">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${getStageDotClass(stage.state)}`}>
                  {stage.state === "completed" ? (
                    <CheckCircle2 size={18} />
                  ) : stage.state === "active" ? (
                    <Loader2 size={18} className="animate-spin" />
                  ) : (
                    <span className="text-[11px] font-black">{stage.index}</span>
                  )}
                </div>

                <div className="flex-1 min-w-0 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="text-sm font-black text-white tracking-tight">{stage.title}</h4>
                        <Badge className={`text-[9px] px-2 py-0.5 font-bold ${getStageStatusClass(stage.state)}`}>
                          {getStageStatusText(stage.state)}
                        </Badge>
                      </div>
                      <p className="mt-1 text-[12px] text-slate-300 leading-relaxed">
                        {stage.subtitle}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">
                        Node
                      </p>
                      <p className="mt-1 text-[10px] font-black uppercase tracking-[0.2em] text-mekong-cyan">
                        {getNodeLabel(stage.node)}
                      </p>
                    </div>
                  </div>

                  {index < visualStages.length - 1 ? (
                    <div className="h-px w-full bg-linear-to-r from-white/10 via-white/5 to-transparent" />
                  ) : null}
                </div>
              </div>
            </div>
          ))}

          {transitions.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-white/15 bg-white/5 p-6 text-center space-y-3">
              <div className="mx-auto w-12 h-12 rounded-2xl bg-mekong-cyan/10 text-mekong-cyan border border-mekong-cyan/20 flex items-center justify-center">
                <Sparkles size={20} />
              </div>
              <p className="text-sm font-bold text-slate-200">Chưa có trace mới</p>
              <p className="text-[12px] text-slate-400 leading-relaxed">
                Khi sensor stream tạo run mới, từng node của agent sẽ xuất hiện ở dạng timeline.
              </p>
            </div>
          ) : null}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          <div className="rounded-2xl bg-white/5 border border-white/10 p-4">
            <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">Incident decision</p>
            <p className="text-sm font-black text-white mt-2">{incidentDecision?.decision ?? "unknown"}</p>
            <p className="text-[12px] text-slate-300 mt-1 leading-relaxed">
              {incidentDecision?.reason ?? "Chưa có quyết định sự cố."}
            </p>
          </div>
          <div className="rounded-2xl bg-white/5 border border-white/10 p-4">
            <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">Plan decision</p>
            <p className="text-sm font-black text-white mt-2">
              {planDecision?.decision ?? "pending"}
            </p>
            <p className="text-[12px] text-slate-300 mt-1 leading-relaxed">
              {planDecision?.reason ?? "Đang chờ agent tạo hoặc xác thực kế hoạch."}
            </p>
          </div>
        </div>
      </div>

      <div className="relative z-10 mt-6 pt-6 border-t border-white/10 flex justify-between items-center gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex gap-1 shrink-0">
            <div className="w-1 h-3 bg-mekong-teal rounded-full animate-pulse" />
            <div className="w-1 h-3 bg-mekong-teal/60 rounded-full animate-pulse delay-75" />
            <div className="w-1 h-3 bg-mekong-teal/30 rounded-full animate-pulse delay-150" />
          </div>
          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest truncate">
            {agentRun ? `Run ${formatCompactId(agentRun.id)} · ${formatTime(runAt)}` : "Chưa có agent run mới"}
          </span>
        </div>
        <p className="text-[9px] font-bold text-slate-500 italic whitespace-nowrap">
          live coordination panel
        </p>
      </div>
    </Card>
  );
};
