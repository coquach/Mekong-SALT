import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  History as HistoryIcon,
  RefreshCcw,
  ShieldCheck,
  ListChecks,
  MapPinned,
  Quote,
  Terminal,
  Zap,
  ArrowUpRight,
} from "lucide-react";
import { Link } from "react-router-dom";

import { EmptyState, InlineError, SkeletonCards } from "../components/ui/AsyncState";
import { ExecutionGraphViewer } from "../components/graph/ExecutionGraphViewer";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { PageHeading } from "../components/ui/PageHeading";
import { ApiError, type ErrorResponse } from "../lib/api/types";
import { type ExecutionGraphRead } from "../lib/api/graph";
import { useLivePageRefresh } from "../lib/hooks/useLivePageRefresh";
import {
  decidePlan,
  getAgentRuns,
  getGoals,
  getPlanApprovalHistory,
  getPlans,
  updateGoal,
  type ActionPlanRead,
  type AgentRunRead,
  type ApprovalRead,
  type MonitoringGoalRead,
} from "../lib/api/strategy";

type StrategyState = {
  loading: boolean;
  error: string | null;
  goals: MonitoringGoalRead[];
  plans: ActionPlanRead[];
  runs: AgentRunRead[];
  selectedPlanId: string | null;
  approvals: ApprovalRead[];
  approvalsLoading: boolean;
  approvalsError: string | null;
  approvalsLastRefreshAt: string | null;
  lastRefreshAt: string | null;
};

function parseApiError(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error && typeof error === "object") {
    const maybeError = error as ErrorResponse;
    if (typeof maybeError.message === "string") {
      return maybeError.message;
    }
  }
  return "Không tải được dữ liệu điều phối.";
}

function formatDatetime(value: string | null): string {
  if (!value) {
    return "--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }
  return date.toLocaleString("vi-VN", {
    hour12: false,
  });
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

function statusBadgeVariant(status: ActionPlanRead["status"]): "navy" | "warning" | "critical" | "optimal" {
  if (status === "approved" || status === "simulated" || status === "closed") {
    return "optimal";
  }
  if (status === "pending_approval" || status === "validated") {
    return "warning";
  }
  if (status === "rejected") {
    return "critical";
  }
  return "navy";
}

function buildRunMessage(run: AgentRunRead): string {
  if (run.trace && typeof run.trace === "object") {
    const trace = run.trace as {
      incident_decision?: { decision?: string; reason?: string };
      plan_decision?: { decision?: string; reason?: string; action_plan_id?: string };
      retrieval_trace?: { total_evidence?: number };
      planning_transition_log?: Array<{ node?: string; status?: string }>;
    };
    const parts = [
      trace.incident_decision?.decision ? `Incident ${trace.incident_decision.decision}` : null,
      trace.plan_decision?.decision ? `Plan ${trace.plan_decision.decision}` : null,
      typeof trace.retrieval_trace?.total_evidence === "number"
        ? `${trace.retrieval_trace.total_evidence} evidence`
        : null,
      trace.planning_transition_log?.length ? `${trace.planning_transition_log.length} nodes` : null,
    ].filter((value): value is string => typeof value === "string" && value.length > 0);

    if (parts.length > 0) {
      return parts.join(" · ");
    }
  }
  if (run.error_message) {
    return run.error_message;
  }
  if (run.payload && typeof run.payload === "object" && !Array.isArray(run.payload)) {
    const payload = run.payload as Record<string, unknown>;
    const request = payload.request;
    if (request && typeof request === "object" && !Array.isArray(request)) {
      const objective = (request as Record<string, unknown>).objective;
      if (typeof objective === "string" && objective.trim().length > 0) {
        return objective;
      }
    }
  }
  return "Run này chưa có mô tả nổi bật để hiển thị.";
}

function buildRunSummary(run: AgentRunRead, trace: ReturnType<typeof getPlanningTrace>): string {
  const traceParts = [
    trace?.plan_decision?.reason,
    trace?.incident_decision?.reason,
    run.error_message,
  ].filter((value): value is string => typeof value === "string" && value.trim().length > 0);

  if (traceParts.length > 0) {
    return traceParts.join(" · ");
  }

  return buildRunMessage(run);
}

function getPlanningTrace(run: AgentRunRead | null): {
  incident_decision?: { decision?: string; reason?: string };
  plan_decision?: {
    decision?: string;
    reason?: string;
    action_plan_id?: string;
    validation?: {
      is_valid?: boolean;
      errors?: string[];
      warnings?: string[];
    };
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
  planning_transition_log?: Array<{ node?: string; status?: string }>;
} | null {
  if (!run || typeof run.trace !== "object" || run.trace === null || Array.isArray(run.trace)) {
    return null;
  }
  return run.trace as NonNullable<ReturnType<typeof getPlanningTrace>>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function getString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function getBoolean(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function toStringList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

function toRecordList(value: unknown): Record<string, unknown>[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter(isRecord);
}

export function StrategyOrchestration() {
  const [state, setState] = useState<StrategyState>(() => ({
    loading: true,
    error: null,
    goals: [],
    plans: [],
    runs: [],
    selectedPlanId: null,
    approvals: [],
    approvalsLoading: false,
    approvalsError: null,
    approvalsLastRefreshAt: null,
    lastRefreshAt: null,
  }));
  const [decisionBusy, setDecisionBusy] = useState<"approved" | "rejected" | null>(null);
  const [goalBusyId, setGoalBusyId] = useState<string | null>(null);
  const [livePlanningGraph, setLivePlanningGraph] = useState<ExecutionGraphRead | null>(null);
  const [livePlanningRunId, setLivePlanningRunId] = useState<string | null>(null);
  const selectedPlanIdRef = useRef<string | null>(state.selectedPlanId);
  const approvalRequestIdRef = useRef(0);

  useEffect(() => {
    selectedPlanIdRef.current = state.selectedPlanId;
  }, [state.selectedPlanId]);

  const refreshApprovalHistory = useCallback(
    async (planId: string | null, options?: { signal?: AbortSignal; showLoading?: boolean }) => {
      const signal = options?.signal;
      const showLoading = options?.showLoading ?? false;
      const requestId = ++approvalRequestIdRef.current;

      if (!planId) {
        setState((previous) => ({
          ...previous,
          approvals: [],
          approvalsLoading: false,
          approvalsError: null,
          approvalsLastRefreshAt: null,
        }));
        return;
      }

      if (showLoading) {
        setState((previous) => ({ ...previous, approvalsLoading: true, approvalsError: null }));
      }

      try {
        const response = await getPlanApprovalHistory(planId, signal);
        if (signal?.aborted || requestId !== approvalRequestIdRef.current) {
          return;
        }

        const refreshedAt = new Date().toISOString();
        setState((previous) => {
          return {
            ...previous,
            approvals: response.items,
            approvalsLoading: false,
            approvalsError: null,
            approvalsLastRefreshAt: refreshedAt,
          };
        });
      } catch (error) {
        if (signal?.aborted || requestId !== approvalRequestIdRef.current) {
          return;
        }
        setState((previous) => ({
          ...previous,
          approvalsLoading: false,
          approvalsError: parseApiError(error),
        }));
      }
    },
    [],
  );

  const refreshData = useCallback(async (options?: { signal?: AbortSignal; showLoading?: boolean }) => {
    const signal = options?.signal;
    const showLoading = options?.showLoading ?? false;
    if (showLoading) {
      setState((previous) => ({ ...previous, loading: true, error: null }));
    }
    try {
      const [goals, plans, runs] = await Promise.all([
        getGoals({ limit: 30 }, signal),
        getPlans({ limit: 50 }, signal),
        getAgentRuns({ limit: 30 }, signal),
      ]);

      setState((previous) => ({
        ...previous,
        loading: false,
        error: null,
        goals: goals.items,
        plans,
        runs: runs.items,
        lastRefreshAt: new Date().toISOString(),
      }));

      const reviewablePlans = plans.filter((plan) => plan.status === "pending_approval");
      const nextSelectedPlan =
        reviewablePlans.find((plan) => plan.id === selectedPlanIdRef.current) ?? reviewablePlans[0] ?? null;

      setState((previous) => ({
        ...previous,
        selectedPlanId: nextSelectedPlan?.id ?? null,
        approvals: [],
        approvalsLoading: false,
        approvalsError: null,
        approvalsLastRefreshAt: null,
      }));

      void refreshApprovalHistory(nextSelectedPlan?.id ?? null, {
        signal,
        showLoading: false,
      });
    } catch (error) {
      if (signal?.aborted) {
        return;
      }
      setState((previous) => ({
        ...previous,
        loading: false,
        error: parseApiError(error),
      }));
    }
  }, [refreshApprovalHistory]);

  useLivePageRefresh({
    refresh: refreshData,
    pollIntervalMs: 15_000,
  });

  const reviewablePlans = useMemo(
    () => state.plans.filter((plan) => plan.status === "pending_approval"),
    [state.plans],
  );

  const selectedPlan = useMemo(
    () => reviewablePlans.find((plan) => plan.id === state.selectedPlanId) ?? null,
    [reviewablePlans, state.selectedPlanId],
  );

  const activeGoalsCount = useMemo(
    () => state.goals.filter((goal) => goal.is_active).length,
    [state.goals],
  );

  const sortedRuns = useMemo(
    () =>
      [...state.runs].sort((left, right) => {
        const leftTime = new Date(left.started_at ?? left.created_at).getTime();
        const rightTime = new Date(right.started_at ?? right.created_at).getTime();
        return rightTime - leftTime;
      }),
    [state.runs],
  );
  const latestRuns = useMemo(() => sortedRuns.slice(0, 8), [sortedRuns]);
  const latestPlanningRun = useMemo(
    () =>
      (selectedPlan
        ? sortedRuns.find(
            (run) => run.run_type === "plan_generation" && run.action_plan_id === selectedPlan.id,
          )
        : null) ?? sortedRuns.find((run) => run.run_type === "plan_generation") ?? latestRuns[0] ?? null,
    [latestRuns, selectedPlan, sortedRuns],
  );
  useEffect(() => {
    const nextRunId = latestPlanningRun?.id ?? null;
    if (!nextRunId) {
      if (livePlanningRunId === null && livePlanningGraph !== null) {
        setLivePlanningGraph(null);
      }
      return;
    }

    if (nextRunId !== livePlanningRunId) {
      setLivePlanningRunId(nextRunId);
      setLivePlanningGraph(latestPlanningRun?.execution_graph ?? null);
      return;
    }

    if (livePlanningGraph === null && latestPlanningRun?.execution_graph !== null) {
      setLivePlanningGraph(latestPlanningRun.execution_graph ?? null);
    }
  }, [latestPlanningRun?.execution_graph, latestPlanningRun?.id, livePlanningGraph, livePlanningRunId]);

  const planningTrace = useMemo(() => getPlanningTrace(latestPlanningRun), [latestPlanningRun]);
  const latestExecutionGraph = livePlanningGraph ?? latestPlanningRun?.execution_graph ?? null;
  const observationSnapshot = useMemo(() => {
    const payload = latestPlanningRun?.observation_snapshot?.payload;
    return isRecord(payload) ? payload : null;
  }, [latestPlanningRun]);
  const observationAssessment = isRecord(observationSnapshot?.assessment)
    ? observationSnapshot.assessment
    : null;
  const observationReading = isRecord(observationSnapshot?.reading) ? observationSnapshot.reading : null;
  const observationWeather = isRecord(observationSnapshot?.weather_snapshot)
    ? observationSnapshot.weather_snapshot
    : null;
  const gateTargets = toRecordList(observationSnapshot?.gate_targets);
  const recommendedGateTargetCode = getString(observationSnapshot?.recommended_gate_target_code);
  const recommendedGateTarget =
    gateTargets.find((gate) => getString(gate.code) === recommendedGateTargetCode) ??
    gateTargets[0] ??
    null;
  const validationResult = isRecord(selectedPlan?.validation_result) ? selectedPlan.validation_result : null;
  const validationErrors = toStringList(validationResult?.errors);
  const validationWarnings = toStringList(validationResult?.warnings);
  const assumptionItems = toStringList(isRecord(selectedPlan?.assumptions) ? selectedPlan.assumptions.items : null);
  const planSteps = toRecordList(selectedPlan?.plan_steps);
  const topCitations = toRecordList(planningTrace?.retrieval_trace?.top_citations).slice(0, 3);
  const totalEvidence = planningTrace?.retrieval_trace?.total_evidence ?? 0;
  const sourceCount = isRecord(planningTrace?.retrieval_trace?.source_counts)
    ? Object.values(planningTrace.retrieval_trace.source_counts).reduce<number>(
        (count, value) => (typeof value === "number" ? count + value : count),
        0,
      )
    : 0;
  const isPlanValid = getBoolean(validationResult?.is_valid);
  const topCitationPreview = topCitations.slice(0, 2);
  const primaryAttentionMessage =
    validationErrors[0] ?? validationWarnings[0] ?? (isPlanValid === false ? "Kế hoạch chưa qua kiểm tra an toàn." : "Không có cảnh báo nổi bật.");
  const attentionTone = validationErrors.length > 0 ? "critical" : validationWarnings.length > 0 ? "warning" : "optimal";
  const attentionLabel =
    validationErrors.length > 0
      ? `${validationErrors.length} lỗi`
      : validationWarnings.length > 0
        ? `${validationWarnings.length} cảnh báo`
        : isPlanValid === false
          ? "Chưa hợp lệ"
          : "Ổn để xem";
  const planStepPreview = planSteps.slice(0, 3);
  const latestApproval = useMemo(
    () =>
      [...state.approvals].sort((left, right) => {
        const leftTime = new Date(left.decided_at).getTime();
        const rightTime = new Date(right.decided_at).getTime();
        return rightTime - leftTime;
      })[0] ?? null,
    [state.approvals],
  );
  const decisionStance = useMemo(() => {
    if (!selectedPlan) {
      return {
        label: "Chưa chọn plan",
        tone: "neutral" as const,
        detail: "Chọn một kế hoạch ở bên phải để xem vì sao hệ thống đề xuất như vậy và có nên duyệt không.",
      };
    }
    if (isPlanValid === false || validationErrors.length > 0) {
      return {
        label: "Chưa nên duyệt",
        tone: "critical" as const,
        detail: "Kế hoạch đang có lỗi an toàn. Nên sửa hoặc yêu cầu hệ thống lập lại trước khi duyệt.",
      };
    }
    if (validationWarnings.length > 0) {
      return {
        label: "Duyệt có điều kiện",
        tone: "warning" as const,
        detail: "Kế hoạch vẫn dùng được nhưng còn cảnh báo. Chỉ nên duyệt nếu chấp nhận rủi ro đã nêu.",
      };
    }
    if (totalEvidence < 3) {
      return {
        label: "Cân nhắc thêm bằng chứng",
        tone: "warning" as const,
        detail: "Kế hoạch đã qua kiểm tra, nhưng bằng chứng còn ít. Nên xem thêm trước khi quyết định.",
      };
    }
    return {
      label: "Có thể duyệt",
      tone: "optimal" as const,
      detail: "Kế hoạch đã có đủ ngữ cảnh, bằng chứng và kiểm tra an toàn để bạn cân nhắc duyệt.",
    };
  }, [isPlanValid, selectedPlan, totalEvidence, validationErrors.length, validationWarnings.length]);
  const isBootstrapping = state.loading && state.goals.length === 0 && state.plans.length === 0;

  const handleDecision = async (decision: "approved" | "rejected") => {
    if (!selectedPlan) {
      return;
    }
    setDecisionBusy(decision);
    try {
      await decidePlan(selectedPlan.id, {
        decision,
        comment: decision === "approved" ? "Approved from FE strategy page." : "Rejected from FE strategy page.",
      });
      await refreshData();
    } catch (error) {
      setState((previous) => ({ ...previous, error: parseApiError(error) }));
    } finally {
      setDecisionBusy(null);
    }
  };

  const handleToggleGoal = async (goal: MonitoringGoalRead) => {
      setGoalBusyId(goal.id);
      try {
        const updatedGoal = await updateGoal(goal.id, { is_active: !goal.is_active });
        setState((previous) => ({
          ...previous,
          goals: previous.goals.map((item) => (item.id === goal.id ? updatedGoal : item)),
          error: null,
      }));
    } catch (error) {
      setState((previous) => ({ ...previous, error: parseApiError(error) }));
    } finally {
      setGoalBusyId(null);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <PageHeading
        trailing={
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              className="h-9 rounded-xl border-slate-200 bg-white px-3 text-[10px]"
              onClick={() => void refreshData({ showLoading: true })}
            >
              <RefreshCcw size={14} className="mr-2" />
              Làm mới
            </Button>
            <Badge variant="neutral" className="text-[9px]">
              Đồng bộ lúc {formatTime(state.lastRefreshAt)}
            </Badge>
          </div>
        }
      />

      {state.error ? (
        <InlineError
          title="Lỗi điều phối strategy"
          message={state.error}
          onRetry={() => {
            void refreshData({ showLoading: true });
          }}
        />
      ) : null}

      {isBootstrapping ? <SkeletonCards count={3} /> : null}

     

      <div className="space-y-6">
        {/* <PlanningTracePanel
          agentRun={latestPlanningRun}
          streamStatus={reasoningStreamStatus}
          lastStreamAt={planningGraphStream.lastStreamAt ?? state.lastRefreshAt}
          executionGraph={latestExecutionGraph}
        /> */}

        <ExecutionGraphViewer
          graph={latestExecutionGraph}
          title="Planning Execution Graph"
          subtitle="Graph snapshot của run gần nhất"
          emptyTitle="Chưa có execution graph"
          emptyDescription="Đang chờ dữ liệu để hiển thị biểu đồ."
        />
      </div>

      <div className="space-y-6">
        <div className="col-span-12 xl:col-span-6">
          <Card variant="white" padding="lg" className="rounded-4xl shadow-soft border border-slate-200 h-full">
            <div className="flex items-center justify-between gap-3 mb-6">
              <div className="flex items-center gap-3 text-mekong-navy">
                <BrainCircuit size={20} />
                <h3 className="text-sm font-black uppercase tracking-[0.18em]">Mục tiêu đang theo dõi</h3>
              </div>
              <Badge variant="optimal" className="text-[9px]">
                {activeGoalsCount}/{state.goals.length} đang bật
              </Badge>
            </div>

            <div className="space-y-3 max-h-140 overflow-y-auto custom-scrollbar pr-1">
              {state.goals.slice(0, 8).map((goal) => (
                <div key={goal.id} className="rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-[12px] font-black uppercase tracking-[0.14em] text-mekong-navy line-clamp-1">
                        {goal.name}
                      </p>
                      <p className="mt-1 text-[12px] font-semibold text-slate-600 line-clamp-2">{goal.objective}</p>
                    </div>
                    <Badge variant={goal.is_active ? "optimal" : "warning"} className="text-[9px] uppercase">
                      {goal.is_active ? "đang chạy" : "tạm dừng"}
                    </Badge>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <p className="text-[10px] font-black uppercase tracking-[0.12em] text-slate-400">
                      Lần chạy gần nhất: {formatDatetime(goal.last_run_at)}
                    </p>
                    <button
                      className="text-[10px] font-black uppercase tracking-[0.12em] text-mekong-teal disabled:opacity-50"
                      disabled={goalBusyId === goal.id}
                      onClick={() => void handleToggleGoal(goal)}
                    >
                      {goalBusyId === goal.id ? "Đang lưu..." : goal.is_active ? "Tạm dừng" : "Kích hoạt"}
                    </button>
                  </div>
                </div>
              ))}
              {state.goals.length === 0 ? (
                <EmptyState
                  title="Chưa có goal hoạt động"
                  description="Tạo hoặc bật goal để agent có objective rõ ràng trước khi lập kế hoạch."
                />
              ) : null}
            </div>
          </Card>
        </div>

        <div className="col-span-12 xl:col-span-6">
          <Card variant="white" padding="lg" className="rounded-4xl shadow-soft border border-slate-200 h-full">
            <div className="flex items-center justify-between gap-3 mb-6">
              <div className="flex items-center gap-3 text-mekong-navy">
                <Zap size={20} />
                <h3 className="text-sm font-black uppercase tracking-[0.18em]">Kế hoạch cần quyết định</h3>
              </div>
              <Badge variant="warning" className="text-[9px]">
                {reviewablePlans.length} kế hoạch
              </Badge>
            </div>

            {reviewablePlans.length > 0 ? (
              <div className="space-y-4">
                <div className="space-y-2 max-h-40 overflow-y-auto custom-scrollbar pr-1">
                  {reviewablePlans.map((plan) => (
                    <button
                      key={plan.id}
                      onClick={() => {
                        setState((previous) => ({ ...previous, selectedPlanId: plan.id }));
                        void refreshApprovalHistory(plan.id, { showLoading: true });
                      }}
                      className={`w-full rounded-2xl border px-4 py-3 text-left transition-all ${
                        state.selectedPlanId === plan.id
                          ? "border-mekong-navy bg-mekong-navy text-white shadow-lg"
                          : "border-slate-200 bg-slate-50 text-mekong-navy hover:border-mekong-teal/40 hover:bg-white"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-[11px] font-black uppercase tracking-[0.14em] line-clamp-1">
                          {plan.objective}
                        </p>
                        <Badge variant={statusBadgeVariant(plan.status)} className="text-[8px]">
                          {plan.status}
                        </Badge>
                      </div>
                      <p className="mt-1 text-[11px] font-semibold opacity-80">
                        {formatDatetime(plan.created_at)}
                      </p>
                    </button>
                  ))}
                </div>

                {selectedPlan ? (
                  <div className="rounded-3xl border border-slate-200 bg-slate-50/70 p-5 space-y-5">
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div className="min-w-0 space-y-2">
                        <p className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">
                          Vì sao hệ thống đề xuất
                        </p>
                        <h4 className="text-sm font-black text-mekong-navy uppercase tracking-[0.08em]">
                          {selectedPlan.objective}
                        </h4>
                        <p className="text-sm font-semibold text-slate-600 leading-relaxed whitespace-pre-wrap wrap-break-word">
                          {selectedPlan.summary}
                        </p>
                      </div>
                      <Badge variant={decisionStance.tone} className="text-[9px] uppercase shrink-0">
                        {decisionStance.label}
                      </Badge>
                    </div>

                    <p className="text-[11px] font-black uppercase tracking-[0.14em] text-slate-400">
                      Bước: {planSteps.length} • Tạo lúc: {formatDatetime(selectedPlan.created_at)}
                    </p>

                    <div className="space-y-3">
                      <div className="rounded-2xl border border-white/70 bg-white p-4 shadow-sm">
                        <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-400">Rủi ro hiện tại</p>
                        <p className="mt-2 text-sm font-black text-mekong-navy uppercase tracking-[0.08em]">
                          {getString(observationAssessment?.risk_level) ?? "Chưa rõ"}
                        </p>
                        <p className="mt-2 text-[11px] font-semibold leading-relaxed text-slate-600 line-clamp-3">
                          {getString(observationAssessment?.summary) ?? "Chưa có tóm tắt đánh giá rủi ro từ run gần nhất."}
                        </p>
                      </div>

                      <div className="rounded-2xl border border-white/70 bg-white p-4 shadow-sm">
                        <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-400">Bằng chứng tham chiếu</p>
                        <p className="mt-2 text-sm font-black text-mekong-navy uppercase tracking-[0.08em]">
                          {totalEvidence} evidence
                        </p>
                        <p className="mt-2 text-[11px] font-semibold leading-relaxed text-slate-600 line-clamp-3">
                          {sourceCount > 0
                            ? `${sourceCount} nguồn được tổng hợp trong retrieval trace.`
                            : "Trace hiện chưa có breakdown nguồn chi tiết."}
                        </p>
                      </div>

                      <div className="rounded-2xl border border-white/70 bg-white p-4 shadow-sm">
                        <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-400">Điểm đến khuyến nghị</p>
                        <p className="mt-2 text-sm font-black text-mekong-navy uppercase tracking-[0.08em]">
                          {recommendedGateTarget ? getString(recommendedGateTarget.name) ?? getString(recommendedGateTarget.code) ?? "--" : "--"}
                        </p>
                        <p className="mt-2 text-[11px] font-semibold leading-relaxed text-slate-600 line-clamp-3">
                          {recommendedGateTarget
                            ? `${getString(recommendedGateTarget.code) ?? "--"} • ${getString(recommendedGateTarget.status) ?? "unknown"}`
                            : "Chưa xác định gate đích trong trace hiện tại."}
                        </p>
                      </div>

                      <div className="rounded-2xl border border-white/70 bg-white p-4 shadow-sm">
                        <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-400">Kiểm tra an toàn</p>
                        <p className="mt-2 text-sm font-black text-mekong-navy uppercase tracking-[0.08em]">
                          {validationErrors.length > 0
                            ? `${validationErrors.length} lỗi`
                            : validationWarnings.length > 0
                              ? `${validationWarnings.length} cảnh báo`
                              : isPlanValid === false
                                ? "Không hợp lệ"
                                : "Sẵn sàng duyệt"}
                        </p>
                        <p className="mt-2 text-[11px] font-semibold leading-relaxed text-slate-600 line-clamp-3">
                          {decisionStance.detail}
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 gap-3">
                      <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm">
                        <div className="flex items-center gap-2 text-mekong-navy">
                          <Quote size={14} />
                          <p className="text-[10px] font-black uppercase tracking-[0.16em]">Vì sao hệ thống đề xuất</p>
                        </div>
                        <p className="text-[13px] font-semibold leading-relaxed text-slate-700 line-clamp-3">
                          {getString(selectedPlan.approval_explanation) ?? getString(observationAssessment?.rationale) ?? selectedPlan.summary}
                        </p>
                        <div className="flex flex-wrap gap-2 pt-1">
                          {getString(observationWeather?.condition_summary) ? (
                            <Badge variant="neutral" className="text-[8px] uppercase">
                              {getString(observationWeather?.condition_summary)}
                            </Badge>
                          ) : null}
                          {observationReading ? (
                            <Badge variant="neutral" className="text-[8px] uppercase">
                              {`Reading ${getString(observationReading.station_code) ?? "--"} • mực nước ${getString(observationReading.water_level_m) ?? "--"} m`}
                            </Badge>
                          ) : null}
                        </div>
                      </div>

                      <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm">
                        <div className="flex items-center gap-2 text-mekong-navy">
                          <MapPinned size={14} />
                          <p className="text-[10px] font-black uppercase tracking-[0.16em]">Dữ liệu tham chiếu</p>
                        </div>
                        {topCitationPreview.length > 0 ? (
                          <div className="space-y-2">
                            {topCitationPreview.map((citation, index) => (
                              <div
                                key={`${getString(citation.citation) ?? index}-${index}`}
                                className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] font-semibold text-slate-600"
                              >
                                <p className="font-black uppercase tracking-[0.12em] text-slate-400">
                                  {getString(citation.source) ?? `Nguồn ${index + 1}`}
                                </p>
                                <p className="mt-1 line-clamp-2">{getString(citation.citation) ?? "Không có trích dẫn"}</p>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div>
                            <p className="text-[12px] font-semibold text-slate-500">
                              Chưa có citations nổi bật trong trace.
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2 text-mekong-navy">
                          <CheckCircle2 size={14} />
                          <p className="text-[10px] font-black uppercase tracking-[0.16em]">Lịch sử duyệt</p>
                        </div>
                        <Badge variant="neutral" className="text-[9px] uppercase">
                          {state.approvals.length} lần
                        </Badge>
                      </div>
                      {state.approvalsLoading ? (
                        <div className="mt-3 space-y-2">
                          <div className="h-16 animate-pulse rounded-2xl bg-slate-100" />
                          <div className="h-16 animate-pulse rounded-2xl bg-slate-100" />
                        </div>
                      ) : state.approvalsError ? (
                        <div className="mt-3 rounded-2xl border border-red-200 bg-red-50 px-3 py-3 text-[12px] font-semibold text-red-800">
                          {state.approvalsError}
                        </div>
                      ) : latestApproval ? (
                        <div className="mt-3 rounded-2xl border border-slate-200 bg-slate-50/80 px-3 py-3">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <Badge
                                variant={latestApproval.decision === "approved" ? "optimal" : "critical"}
                                className="text-[8px] uppercase"
                              >
                                {latestApproval.decision === "approved" ? "Đã duyệt" : "Đã từ chối"}
                              </Badge>
                              <p className="text-[11px] font-black uppercase tracking-[0.14em] text-mekong-navy">
                                {latestApproval.decided_by_name}
                              </p>
                            </div>
                            <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-400">
                              {formatDatetime(latestApproval.decided_at)}
                            </p>
                          </div>
                          {latestApproval.comment ? (
                            <p className="mt-2 text-[12px] font-semibold leading-relaxed text-slate-600 line-clamp-3">
                              {latestApproval.comment}
                            </p>
                          ) : (
                            <p className="mt-2 text-[12px] font-semibold leading-relaxed text-slate-500">
                              Không có ghi chú bổ sung.
                            </p>
                          )}
                          {state.approvals.length > 1 ? (
                            <p className="mt-2 text-[11px] font-semibold text-slate-500">
                              {state.approvals.length - 1} lần duyệt cũ hơn được giữ lại trong lịch sử backend.
                            </p>
                          ) : null}
                        </div>
                      ) : (
                        <EmptyState
                          title="Chưa có lịch sử duyệt"
                          description="Khi plan này được duyệt hoặc từ chối, lịch sử sẽ hiển thị tại đây."
                        />
                      )}
                    </div>

                    <div className="grid grid-cols-1 gap-3">
                      <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm">
                        <div className="flex items-center gap-2 text-mekong-navy">
                          <AlertTriangle size={14} />
                          <p className="text-[10px] font-black uppercase tracking-[0.16em]">Điểm cần chú ý</p>
                        </div>
                        <div
                          className={`rounded-xl border px-3 py-2 text-[12px] font-semibold ${
                            attentionTone === "critical"
                              ? "border-red-200 bg-red-50 text-red-800"
                              : attentionTone === "warning"
                                ? "border-amber-200 bg-amber-50 text-amber-900"
                                : "border-emerald-200 bg-emerald-50 text-emerald-900"
                          }`}
                        >
                          <p className="font-black uppercase tracking-[0.12em]">{attentionLabel}</p>
                          <p className="mt-1 leading-relaxed line-clamp-2">{primaryAttentionMessage}</p>
                        </div>
                        {assumptionItems.length > 0 ? (
                          <div className="pt-1">
                            <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-400">
                              Giả định chính
                            </p>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {assumptionItems.slice(0, 3).map((assumption, index) => (
                                <span
                                  key={`${assumption}-${index}`}
                                  className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-semibold text-slate-600"
                                >
                                  {assumption}
                                </span>
                              ))}
                              {assumptionItems.length > 3 ? (
                                <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-semibold text-slate-500">
                                  +{assumptionItems.length - 3}
                                </span>
                              ) : null}
                            </div>
                          </div>
                        ) : null}
                      </div>

                      <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm">
                        <div className="flex items-center gap-2 text-mekong-navy">
                          <ListChecks size={14} />
                          <p className="text-[10px] font-black uppercase tracking-[0.16em]">Việc hệ thống sẽ làm</p>
                        </div>
                        <div className="space-y-2 max-h-52 overflow-y-auto custom-scrollbar pr-1">
                          {planStepPreview.map((step, index) => {
                            const stepIndex = typeof step.step_index === "number" ? step.step_index : index + 1;
                            return (
                              <div
                                key={`${stepIndex}-${getString(step.title) ?? index}`}
                                className="rounded-2xl border border-slate-200 bg-slate-50/80 px-3 py-2"
                              >
                                <div className="flex items-center justify-between gap-2">
                                  <p className="text-[11px] font-black uppercase tracking-[0.12em] text-mekong-navy line-clamp-1">
                                    {stepIndex}. {getString(step.title) ?? "Bước đề xuất"}
                                  </p>
                                  <Badge variant="neutral" className="text-[8px] uppercase">
                                    {getString(step.action_type) ?? "step"}
                                  </Badge>
                                </div>
                                <p className="mt-1 text-[11px] font-semibold leading-relaxed text-slate-600 line-clamp-3">
                                  {getString(step.instructions) ?? "Chưa có instructions."}
                                </p>
                              </div>
                            );
                          })}
                          {planSteps.length === 0 ? (
                            <EmptyState
                              title="Chưa có plan steps"
                              description="Khi hệ thống sinh ra các bước cụ thể, chúng sẽ hiện ở đây để bạn đọc nhanh." 
                            />
                          ) : null}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : null}

                <div className="grid grid-cols-1 gap-3">
                  <Button
                    variant="navy"
                    className="h-11 rounded-xl px-4"
                    onClick={() => void handleDecision("approved")}
                    disabled={decisionBusy !== null || !selectedPlan}
                  >
                    <ShieldCheck size={16} />
                    {decisionBusy === "approved" ? "Đang duyệt..." : "Phê duyệt"}
                  </Button>
                  <Button
                    variant="outline"
                    className="h-11 rounded-xl border-slate-200 px-4"
                    onClick={() => void handleDecision("rejected")}
                    disabled={decisionBusy !== null || !selectedPlan}
                  >
                    {decisionBusy === "rejected" ? "Đang từ chối..." : "Từ chối"}
                  </Button>
                </div>
              </div>
            ) : (
              <EmptyState
                title="Không có plan chờ duyệt"
                description="Khi agent sinh plan ở trạng thái pending_approval, danh sách sẽ xuất hiện tại đây."
              />
            )}
          </Card>
        </div>

        <div className="col-span-12 xl:col-span-12">
          <Card variant="navy" className="h-full rounded-4xl border border-white/10 bg-[#00203F] p-6 shadow-2xl">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div className="flex items-center gap-3 text-white">
                <Terminal size={19} />
                <h3 className="text-sm font-black uppercase tracking-[0.18em]">Dấu vết suy luận</h3>
              </div>
              <Badge className="bg-white/10 text-slate-200 border-white/10 text-[9px]">{latestRuns.length} runs</Badge>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {latestRuns.map((run) => (
                <div key={run.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0 space-y-1">
                      <p className="text-[10px] font-black uppercase tracking-[0.15em] text-mekong-cyan">
                        {run.run_type}
                      </p>
                      <p className="text-[11px] font-black uppercase tracking-[0.12em] text-white">
                        {formatDatetime(run.started_at ?? run.created_at)}
                      </p>
                    </div>
                    <Badge className="bg-white/10 text-slate-200 border-white/10 text-[8px] uppercase">
                      {run.status}
                    </Badge>
                  </div>
                  <p className="mt-3 text-[13px] font-semibold leading-relaxed text-slate-200">
                    {buildRunSummary(run, getPlanningTrace(run))}
                  </p>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {(() => {
                      const runTrace = getPlanningTrace(run);
                      const evidenceCount = runTrace?.retrieval_trace?.total_evidence;
                      const transitionCount = runTrace?.planning_transition_log?.length;
                      return (
                        <>
                          {typeof evidenceCount === "number" ? (
                            <Badge className="bg-white/10 text-slate-200 border-white/10 text-[8px] uppercase">
                              {evidenceCount} evidence
                            </Badge>
                          ) : null}
                          {typeof transitionCount === "number" ? (
                            <Badge className="bg-white/10 text-slate-200 border-white/10 text-[8px] uppercase">
                              {transitionCount} node transitions
                            </Badge>
                          ) : null}
                          {run.error_message ? (
                            <Badge className="bg-red-500/15 text-red-200 border-red-400/20 text-[8px] uppercase">
                              Có lỗi run
                            </Badge>
                          ) : null}
                        </>
                      );
                    })()}
                  </div>
                  <Link
                    to={`/strategy/runs/${run.id}`}
                    className="mt-3 inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.14em] text-mekong-cyan transition-colors hover:text-white"
                  >
                    Mở chi tiết graph
                    <ArrowUpRight size={12} />
                  </Link>
                </div>
              ))}
              {latestRuns.length === 0 ? (
                <EmptyState
                  title="Chưa có run trace"
                  description="Khi backend kích hoạt vòng reasoning mới, trace sẽ xuất hiện theo thứ tự thời gian."
                />
              ) : null}
            </div>
          </Card>
        </div>
      </div>

      <Card variant="white" className="rounded-4xl border border-slate-200 p-6 shadow-soft">
        <div className="flex items-center gap-3 text-mekong-navy">
          <HistoryIcon size={20} />
        <h3 className="text-sm font-black uppercase tracking-[0.18em]">Kế hoạch gần đây</h3>
        </div>
        <div className="mt-4 grid grid-cols-1 gap-3">
          {state.plans.slice(0, 8).map((plan) => (
            <div key={plan.id} className="rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="text-[10px] font-black uppercase tracking-[0.12em] text-slate-400">
                  {formatDatetime(plan.created_at)}
                </p>
                <Badge variant={statusBadgeVariant(plan.status)} className="text-[8px] uppercase">
                  {plan.status}
                </Badge>
              </div>
              <p className="mt-2 text-[12px] font-black text-mekong-navy line-clamp-2">{plan.objective}</p>
              <p className="mt-2 text-[11px] font-semibold text-slate-500 line-clamp-2">{plan.summary}</p>
            </div>
          ))}
          {state.plans.length === 0 ? (
            <EmptyState
              title="Chưa có lịch sử plan"
              description="Agent cần tạo ít nhất một plan trước khi màn lịch sử có dữ liệu."
            />
          ) : null}
        </div>
        <div className="mt-4 pt-4 border-t border-slate-200">
          <Button variant="navy" className="h-11 rounded-xl px-4" disabled>
            <CheckCircle2 size={16} />
            Chỉnh mục tiêu (sắp mở)
          </Button>
        </div>
      </Card>
    </div>
  );
}

export default StrategyOrchestration;
