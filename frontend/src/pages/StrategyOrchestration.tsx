import { useEffect, useMemo, useState } from "react";
import {
  BrainCircuit,
  CheckCircle2,
  History as HistoryIcon,
  ShieldCheck,
  Terminal,
  Zap,
} from "lucide-react";

import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
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

export function StrategyOrchestration() {
  const [state, setState] = useState<StrategyState>({
    loading: true,
    error: null,
    goals: [],
    plans: [],
    runs: [],
  });
  const [decisionBusy, setDecisionBusy] = useState<"approved" | "rejected" | null>(null);
  const [goalBusyId, setGoalBusyId] = useState<string | null>(null);

  useEffect(() => {
    const abortController = new AbortController();

    const loadData = async () => {
      setState((previous) => ({ ...previous, loading: true, error: null }));
      try {
        const [goals, plans, runs] = await Promise.all([
          getGoals({ limit: 30 }, abortController.signal),
          getPlans({ limit: 30 }, abortController.signal),
          getAgentRuns({ limit: 20 }, abortController.signal),
        ]);

        setState({
          loading: false,
          error: null,
          goals: goals.items,
          plans,
          runs: runs.items,
        });
      } catch (error) {
        if (abortController.signal.aborted) {
          return;
        }
        setState((previous) => ({
          ...previous,
          loading: false,
          error: parseApiError(error),
        }));
      }
    };

    void loadData();
    return () => abortController.abort();
  }, []);

  const pendingPlan = useMemo(
    () => state.plans.find((plan) => plan.status === "pending_approval") ?? null,
    [state.plans],
  );

  const activeGoalsCount = useMemo(
    () => state.goals.filter((goal) => goal.is_active).length,
    [state.goals],
  );

  const recentTraceLogs = useMemo(
    () =>
      state.runs.slice(0, 4).map((run) => ({
        id: run.id,
        time: formatDatetime(run.started_at),
        category: run.run_type,
        message:
          (run.trace && JSON.stringify(run.trace).slice(0, 180)) ||
          run.error_message ||
          JSON.stringify(run.payload).slice(0, 180),
      })),
    [state.runs],
  );

  const handleDecision = async (decision: "approved" | "rejected") => {
    if (!pendingPlan) {
      return;
    }
    setDecisionBusy(decision);
    try {
      await decidePlan(pendingPlan.id, {
        decision,
        comment: decision === "approved" ? "Approved from FE strategy page." : "Rejected from FE strategy page.",
      });

      const [plans, runs] = await Promise.all([getPlans({ limit: 30 }), getAgentRuns({ limit: 20 })]);
      setState((previous) => ({
        ...previous,
        plans,
        runs: runs.items,
        error: null,
      }));
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
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {state.error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-3 text-sm font-bold text-red-700">
          {state.error}
        </div>
      ) : null}

      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-end gap-6">
        <div className="space-y-3">
          <h1 className="text-4xl lg:text-5xl font-black text-mekong-navy tracking-tighter leading-none uppercase">
            Điều phối chiến lược
          </h1>
          <p className="text-base text-mekong-slate font-medium max-w-3xl leading-relaxed">
            Trang này kết nối trực tiếp với backend để vận hành vòng đời goals, plans và quyết định phê duyệt.
          </p>
        </div>
        <div className="flex items-center gap-3 px-5 py-3 bg-white rounded-2xl border border-slate-100 shadow-sm">
          <div className="w-2.5 h-2.5 bg-mekong-mint rounded-full animate-pulse" />
          <span className="text-[11px] font-black text-mekong-navy uppercase tracking-widest">
            Active Goals: {activeGoalsCount}/{state.goals.length}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-8">
          <Card variant="white" padding="lg" className="rounded-[40px] shadow-soft border-l-[6px] border-l-mekong-teal">
            <div className="flex justify-between items-center mb-8">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-mekong-navy rounded-xl text-white shadow-lg">
                  <Zap size={18} fill="currentColor" />
                </div>
                <h3 className="text-[13px] font-black text-mekong-navy uppercase tracking-[0.2em]">
                  Plan chờ quyết định
                </h3>
              </div>
              <Badge variant="cyan" className="px-4 py-1.5 font-black uppercase tracking-widest text-[10px]">
                {pendingPlan ? "pending_approval" : "không có"}
              </Badge>
            </div>

            {pendingPlan ? (
              <div className="space-y-6">
                <div className="p-8 bg-slate-50 rounded-[32px] border border-slate-100 space-y-3">
                  <h4 className="text-[13px] font-black text-mekong-navy uppercase tracking-widest">
                    Mục tiêu: {pendingPlan.objective}
                  </h4>
                  <p className="text-[15px] text-slate-600 leading-relaxed font-semibold">{pendingPlan.summary}</p>
                  <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">
                    Số bước kế hoạch: {pendingPlan.plan_steps.length} • Tạo lúc: {formatDatetime(pendingPlan.created_at)}
                  </p>
                </div>

                <div className="flex gap-4">
                  <Button
                    variant="navy"
                    className="h-14 px-8 rounded-2xl shadow-xl flex gap-3"
                    onClick={() => void handleDecision("approved")}
                    disabled={decisionBusy !== null}
                  >
                    <ShieldCheck size={20} />
                    {decisionBusy === "approved" ? "Đang phê duyệt..." : "Phê duyệt"}
                  </Button>
                  <Button
                    variant="outline"
                    className="h-14 px-8 rounded-2xl border-slate-200"
                    onClick={() => void handleDecision("rejected")}
                    disabled={decisionBusy !== null}
                  >
                    {decisionBusy === "rejected" ? "Đang từ chối..." : "Từ chối"}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="p-8 bg-slate-50 rounded-[32px] border border-slate-100 text-[14px] font-bold text-slate-500">
                Không có kế hoạch nào đang ở trạng thái `pending_approval`.
              </div>
            )}
          </Card>
        </div>

        <div className="col-span-12 lg:col-span-4">
          <Card variant="navy" className="bg-[#00203F] border-none shadow-2xl rounded-[40px] relative overflow-hidden flex flex-col h-full">
            <div className="absolute top-0 right-0 w-80 h-80 bg-mekong-cyan/5 rounded-full blur-[100px]" />
            <div className="relative z-10 p-10 flex-1 flex flex-col">
              <div className="flex items-center gap-4 mb-10 border-b border-white/10 pb-6">
                <div className="p-3 bg-mekong-cyan/10 rounded-2xl text-mekong-cyan border border-mekong-cyan/20">
                  <HistoryIcon size={24} />
                </div>
                <h3 className="text-lg font-black text-white uppercase tracking-tighter">Plan gần nhất</h3>
              </div>
              <div className="space-y-4">
                {state.plans.slice(0, 4).map((plan) => (
                  <div key={plan.id} className="p-4 rounded-2xl bg-white/5 border border-white/10">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                        {formatDatetime(plan.created_at)}
                      </span>
                      <Badge variant={statusBadgeVariant(plan.status)} className="text-[9px] uppercase">
                        {plan.status}
                      </Badge>
                    </div>
                    <p className="text-[12px] font-semibold text-slate-200 line-clamp-2">{plan.objective}</p>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-8">
          <Card variant="white" padding="none" className="rounded-[40px] shadow-soft border border-slate-200 overflow-hidden h-[450px] flex flex-col">
            <div className="p-8 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
              <div className="flex items-center gap-3 text-mekong-navy">
                <Terminal size={22} />
                <h3 className="text-base font-black uppercase tracking-widest">Agent run traces</h3>
              </div>
              <Badge variant="navy" className="font-mono text-[10px]">
                {state.runs.length} runs
              </Badge>
            </div>

            <div className="flex-1 p-8 space-y-4 overflow-y-auto font-mono bg-[#FAFAFB]">
              {recentTraceLogs.map((log) => (
                <div key={log.id} className="flex gap-4 p-4 rounded-xl bg-white border border-slate-100 hover:shadow-md transition-all">
                  <span className="text-[11px] font-black text-slate-400 opacity-60">[{log.time}]</span>
                  <div className="space-y-1">
                    <span className="text-[10px] font-black text-mekong-teal uppercase tracking-widest">[{log.category}]</span>
                    <p className="text-[13px] font-medium text-mekong-navy leading-relaxed">{log.message}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="col-span-12 lg:col-span-4">
          <Card variant="white" padding="lg" className="rounded-[40px] bg-slate-100/50 border-none shadow-soft h-full flex flex-col">
            <div className="flex items-center gap-3 text-mekong-navy mb-8">
              <BrainCircuit size={22} />
              <h3 className="text-base font-black uppercase tracking-widest leading-none">Monitoring goals</h3>
            </div>

            <div className="space-y-4 overflow-y-auto pr-1">
              {state.goals.slice(0, 6).map((goal) => (
                <div key={goal.id} className="rounded-2xl bg-white border border-slate-200 p-4">
                  <div className="flex justify-between items-start gap-3">
                    <div>
                      <p className="text-[12px] font-black text-mekong-navy uppercase tracking-widest line-clamp-1">
                        {goal.name}
                      </p>
                      <p className="text-[11px] text-slate-500 font-semibold line-clamp-2">{goal.objective}</p>
                    </div>
                    <Badge variant={goal.is_active ? "optimal" : "warning"} className="text-[9px] uppercase">
                      {goal.is_active ? "active" : "paused"}
                    </Badge>
                  </div>
                  <div className="mt-3 flex justify-between items-center">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                      Last run: {formatDatetime(goal.last_run_at)}
                    </p>
                    <button
                      className="text-[10px] font-black text-mekong-teal uppercase tracking-widest disabled:opacity-50"
                      disabled={goalBusyId === goal.id}
                      onClick={() => void handleToggleGoal(goal)}
                    >
                      {goalBusyId === goal.id ? "Đang lưu..." : goal.is_active ? "Tạm dừng" : "Kích hoạt"}
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-8 pt-6 border-t border-slate-200">
              <Button variant="navy" className="w-full h-14 rounded-[24px] shadow-2xl flex gap-2" disabled>
                <CheckCircle2 size={20} /> Goal editor (sẽ mở ở bước tiếp theo)
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default StrategyOrchestration;
