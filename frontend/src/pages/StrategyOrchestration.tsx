import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  History as HistoryIcon,
  ShieldCheck,
  ListChecks,
  MapPinned,
  Quote,
  Terminal,
  Zap,
} from "lucide-react";

import { EmptyState, InlineError, SkeletonCards } from "../components/ui/AsyncState";
import { AISentinelPanel } from "../components/dashboard/AISentinelPanel";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { PageHeading } from "../components/ui/PageHeading";
import { isPageCacheFresh, readPageCache, writePageCache } from "../lib/cache/pageCache";
import { ApiError, type ErrorResponse } from "../lib/api/types";
import {
  decidePlan,
  getAgentRuns,
  getGoals,
  getPlans,
  updateGoal,
  type ActionPlanRead,
  type AgentRunRead,
  type MonitoringGoalRead,
} from "../lib/api/strategy";

type StrategyState = {
  loading: boolean;
  error: string | null;
  goals: MonitoringGoalRead[];
  plans: ActionPlanRead[];
  runs: AgentRunRead[];
  selectedPlanId: string | null;
  lastRefreshAt: string | null;
};

type StrategyCache = {
  state: Pick<StrategyState, "goals" | "plans" | "runs" | "selectedPlanId" | "lastRefreshAt">;
};

const STRATEGY_CACHE_KEY = "mekong.cache.strategy";
const STRATEGY_CACHE_MAX_AGE_MS = 30_000;

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
  return JSON.stringify(run.payload).slice(0, 160);
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
  const cachedStrategy = useMemo(() => readPageCache<StrategyCache>(STRATEGY_CACHE_KEY), []);
  const [state, setState] = useState<StrategyState>(() => {
    const cachedState = cachedStrategy?.value.state;
    if (!cachedState) {
      return {
        loading: true,
        error: null,
        goals: [],
        plans: [],
        runs: [],
        selectedPlanId: null,
        lastRefreshAt: null,
      };
    }

    return {
      loading: false,
      error: null,
      goals: cachedState.goals,
      plans: cachedState.plans,
      runs: cachedState.runs,
      selectedPlanId: cachedState.selectedPlanId,
      lastRefreshAt: cachedState.lastRefreshAt,
    };
  });
  const [decisionBusy, setDecisionBusy] = useState<"approved" | "rejected" | null>(null);
  const [goalBusyId, setGoalBusyId] = useState<string | null>(null);
  const selectedPlanIdRef = useRef<string | null>(state.selectedPlanId);

  useEffect(() => {
    selectedPlanIdRef.current = state.selectedPlanId;
  }, [state.selectedPlanId]);

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

      setState((previous) => {
        const reviewablePlans = plans.filter((plan) => plan.status === "pending_approval");
        const selectedPlan =
          reviewablePlans.find((plan) => plan.id === previous.selectedPlanId) ??
          reviewablePlans[0] ??
          null;

        return {
          ...previous,
          loading: false,
          error: null,
          goals: goals.items,
          plans,
          runs: runs.items,
          selectedPlanId: selectedPlan?.id ?? null,
          lastRefreshAt: new Date().toISOString(),
        };
      });

      const nextLastRefreshAt = new Date().toISOString();
      const reviewablePlans = plans.filter((plan) => plan.status === "pending_approval");
      const nextSelectedPlan =
        reviewablePlans.find((plan) => plan.id === selectedPlanIdRef.current) ?? reviewablePlans[0] ?? null;
      writePageCache<StrategyCache>(STRATEGY_CACHE_KEY, {
        state: {
          goals: goals.items,
          plans,
          runs: runs.items,
          selectedPlanId: nextSelectedPlan?.id ?? null,
          lastRefreshAt: nextLastRefreshAt,
        },
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
  }, []);

  useEffect(() => {
    const abortController = new AbortController();
    const shouldSkipInitialRefresh =
      cachedStrategy !== null && isPageCacheFresh(cachedStrategy, STRATEGY_CACHE_MAX_AGE_MS);

    if (shouldSkipInitialRefresh) {
      return () => abortController.abort();
    }

    void refreshData({ signal: abortController.signal, showLoading: true });
    return () => abortController.abort();
  }, [cachedStrategy, refreshData]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      void refreshData({ showLoading: false });
    }, 20_000);
    return () => window.clearInterval(intervalId);
  }, [refreshData]);

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

  const latestRuns = useMemo(() => state.runs.slice(0, 8), [state.runs]);
  const latestPlanningRun = useMemo(
    () =>
      (selectedPlan
        ? state.runs.find(
            (run) => run.run_type === "plan_generation" && run.action_plan_id === selectedPlan.id,
          )
        : null) ?? state.runs.find((run) => run.run_type === "plan_generation") ?? latestRuns[0] ?? null,
    [latestRuns, selectedPlan, state.runs],
  );
  const reasoningStreamStatus = state.loading ? "connecting" : "connected";
  const planningTrace = useMemo(() => getPlanningTrace(latestPlanningRun), [latestPlanningRun]);
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
          <Badge variant="neutral" className="text-[9px]">
            Đồng bộ lúc {formatTime(state.lastRefreshAt)}
          </Badge>
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

      <div className={`${isBootstrapping ? "hidden" : ""}`}>
        <AISentinelPanel
          agentRun={latestPlanningRun}
          streamStatus={reasoningStreamStatus}
          lastStreamAt={state.lastRefreshAt}
        />
      </div>

      <Card variant="white" className={`rounded-4xl border border-slate-200 p-6 shadow-soft ${isBootstrapping ? "hidden" : ""}`}>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-2 max-w-3xl">
            <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Cách đọc nhanh</p>
            <h3 className="text-xl font-black text-mekong-navy">Màn này cho biết hệ thống đang đề xuất gì và vì sao bạn nên duyệt hoặc từ chối.</h3>
            <p className="text-sm font-semibold leading-relaxed text-slate-600">
              Chọn một kế hoạch đang chờ duyệt, đọc phần rủi ro và bằng chứng tham chiếu, rồi xem các bước mà hệ thống sẽ thực hiện nếu được chấp thuận.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3 lg:w-md">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-400">1. Chọn kế hoạch</p>
              <p className="mt-1 text-sm font-semibold text-slate-700">Xem kế hoạch nào đang chờ bạn quyết định.</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-400">2. Đọc lý do</p>
              <p className="mt-1 text-sm font-semibold text-slate-700">Xem rủi ro, bằng chứng và cảnh báo.</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-400">3. Quyết định</p>
              <p className="mt-1 text-sm font-semibold text-slate-700">Phê duyệt hoặc từ chối trước khi chạy mô phỏng.</p>
            </div>
          </div>
        </div>
      </Card>

      <div className={`grid grid-cols-12 gap-6 ${isBootstrapping ? "hidden" : ""}`}>
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
                      onClick={() => setState((previous) => ({ ...previous, selectedPlanId: plan.id }))}
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
                        <p className="text-sm font-semibold text-slate-600 leading-relaxed">
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

                    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
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

                    <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
                      <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm">
                        <div className="flex items-center gap-2 text-mekong-navy">
                          <Quote size={14} />
                          <p className="text-[10px] font-black uppercase tracking-[0.16em]">Vì sao hệ thống đề xuất</p>
                        </div>
                        <p className="text-[13px] font-semibold leading-relaxed text-slate-700">
                          {getString(selectedPlan.approval_explanation) ?? getString(observationAssessment?.rationale) ?? selectedPlan.summary}
                        </p>
                        <p className="text-[12px] font-semibold leading-relaxed text-slate-500">
                          {getString(observationWeather?.condition_summary)
                            ? `Điều kiện thời tiết: ${getString(observationWeather?.condition_summary)}`
                            : "Chưa có weather snapshot bổ sung."}
                        </p>
                        <p className="text-[12px] font-semibold leading-relaxed text-slate-500">
                          {observationReading
                            ? `Reading ${getString(observationReading.station_code) ?? "--"} • salinity ${getString(observationReading.salinity_dsm) ?? "--"} dS/m • water level ${getString(observationReading.water_level_m) ?? "--"} m`
                            : "Chưa có reading snapshot để đối chiếu."}
                        </p>
                      </div>

                      <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm">
                        <div className="flex items-center gap-2 text-mekong-navy">
                          <MapPinned size={14} />
                          <p className="text-[10px] font-black uppercase tracking-[0.16em]">Dữ liệu tham chiếu</p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {topCitations.length > 0 ? (
                            topCitations.map((citation, index) => (
                              <div
                                key={`${getString(citation.citation) ?? index}-${index}`}
                                className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] font-semibold text-slate-600"
                              >
                                <p className="font-black uppercase tracking-[0.12em] text-slate-400">
                                  {getString(citation.source) ?? `Nguồn ${index + 1}`}
                                </p>
                                <p className="mt-1 line-clamp-2">{getString(citation.citation) ?? "Không có trích dẫn"}</p>
                              </div>
                            ))
                          ) : (
                            <p className="text-[12px] font-semibold text-slate-500">
                              Chưa có citations nổi bật trong trace.
                            </p>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
                      <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm">
                        <div className="flex items-center gap-2 text-mekong-navy">
                          <AlertTriangle size={14} />
                          <p className="text-[10px] font-black uppercase tracking-[0.16em]">Điểm cần chú ý</p>
                        </div>
                        <div className="space-y-2">
                          {validationErrors.length > 0 ? (
                            validationErrors.map((error, index) => (
                              <div
                                key={`${error}-${index}`}
                                className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-[12px] font-semibold text-red-800"
                              >
                                {error}
                              </div>
                            ))
                          ) : validationWarnings.length > 0 ? (
                            validationWarnings.map((warning, index) => (
                              <div
                                key={`${warning}-${index}`}
                                className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-[12px] font-semibold text-amber-900"
                              >
                                {warning}
                              </div>
                            ))
                          ) : (
                            <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-[12px] font-semibold text-emerald-900">
                              Không có lỗi guard; chỉ còn quyết định vận hành của người điều hành.
                            </div>
                          )}
                        </div>
                        {assumptionItems.length > 0 ? (
                          <div className="pt-1">
                            <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-400">
                              Giả định chính
                            </p>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {assumptionItems.map((assumption, index) => (
                                <span
                                  key={`${assumption}-${index}`}
                                  className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-semibold text-slate-600"
                                >
                                  {assumption}
                                </span>
                              ))}
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
                          {planSteps.slice(0, 4).map((step, index) => {
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
                                {getString(step.rationale) ? (
                                  <p className="mt-1 text-[11px] font-semibold leading-relaxed text-slate-500 line-clamp-2">
                                    {getString(step.rationale)}
                                  </p>
                                ) : null}
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

                <div className="grid grid-cols-2 gap-3">
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

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
              {latestRuns.map((run) => (
                <div key={run.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-[10px] font-black uppercase tracking-[0.15em] text-mekong-cyan">
                      {run.run_type}
                    </p>
                    <Badge className="bg-white/10 text-slate-200 border-white/10 text-[8px]">
                      {run.status}
                    </Badge>
                  </div>
                  <p className="mt-2 text-[12px] font-semibold leading-relaxed text-slate-200 line-clamp-4">
                    {buildRunMessage(run)}
                  </p>
                  <div className="mt-3 flex items-center justify-between text-[10px] font-black uppercase tracking-[0.12em] text-slate-400">
                    <span>{formatDatetime(run.started_at)}</span>
                    <span>{run.id.slice(0, 8)}</span>
                  </div>
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
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
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
