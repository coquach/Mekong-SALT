import { useEffect, useMemo, useState } from "react";
import {
  ArrowUpRight,
  BrainCircuit,
  CheckCircle2,
  ClipboardList,
  Download,
  Filter,
  RefreshCcw,
  Search,
  Share2,
} from "lucide-react";

import { EmptyState, InlineError, SkeletonCards } from "../components/ui/AsyncState";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { PageHeading } from "../components/ui/PageHeading";
import { ApiError, type ErrorResponse } from "../lib/api/types";
import {
  evaluateFeedback,
  getActionLogs,
  getActionOutcomes,
  getExecutionBatches,
  getLatestFeedback,
  simulateExecutionBatch,
  type ActionOutcomeRead,
  type ExecutionBatchRead,
  type FeedbackLifecycleRead,
} from "../lib/api/operations";
import { getPlans, type ActionPlanRead } from "../lib/api/strategy";

type ActionLogsState = {
  loading: boolean;
  error: string | null;
  searchText: string;
  plans: ActionPlanRead[];
  actionLogs: Awaited<ReturnType<typeof getActionLogs>>["items"];
  batches: ExecutionBatchRead[];
  outcomes: ActionOutcomeRead[];
  feedback: FeedbackLifecycleRead | null;
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
  return "Không tải được dữ liệu action logs.";
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }
  return date.toLocaleString("vi-VN", { hour12: false });
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

function normalizeActionType(value: string): string {
  return value.replace(/[-_]/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export function ActionLogs() {
  const [state, setState] = useState<ActionLogsState>({
    loading: true,
    error: null,
    searchText: "",
    plans: [],
    actionLogs: [],
    batches: [],
    outcomes: [],
    feedback: null,
    lastRefreshAt: null,
  });
  const [simulateBusy, setSimulateBusy] = useState(false);
  const [feedbackBusy, setFeedbackBusy] = useState(false);

  const refreshData = async (options?: { signal?: AbortSignal; showLoading?: boolean }) => {
    const signal = options?.signal;
    const showLoading = options?.showLoading ?? false;
    if (showLoading) {
      setState((previous) => ({ ...previous, loading: true, error: null }));
    }

    try {
      const [plans, actionLogs, batches, outcomes] = await Promise.all([
        getPlans({ limit: 50 }, signal),
        getActionLogs({ limit: 100 }, signal),
        getExecutionBatches({ limit: 50 }, signal),
        getActionOutcomes({ limit: 50 }, signal),
      ]);

      let feedback: FeedbackLifecycleRead | null = null;
      const latestBatch = batches.items[0];
      if (latestBatch) {
        try {
          feedback = await getLatestFeedback(latestBatch.id, signal);
        } catch (error) {
          if (!(error instanceof ApiError && error.statusCode === 404)) {
            throw error;
          }
        }
      }

      setState((previous) => ({
        ...previous,
        loading: false,
        error: null,
        plans,
        actionLogs: actionLogs.items,
        batches: batches.items,
        outcomes: outcomes.items,
        feedback,
        lastRefreshAt: new Date().toISOString(),
      }));
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
  };

  useEffect(() => {
    const abortController = new AbortController();
    void refreshData({ signal: abortController.signal, showLoading: true });
    return () => abortController.abort();
  }, []);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      void refreshData({ showLoading: false });
    }, 20_000);
    return () => window.clearInterval(intervalId);
  }, []);

  const latestBatch = state.batches[0] ?? null;
  const approvedPlan = useMemo(
    () => state.plans.find((plan) => plan.status === "approved") ?? null,
    [state.plans],
  );

  const successfulActions = useMemo(
    () => state.actionLogs.filter((item) => item.execution.status === "succeeded").length,
    [state.actionLogs],
  );

  const filteredLogs = useMemo(() => {
    const keyword = state.searchText.trim().toLowerCase();
    if (!keyword) {
      return state.actionLogs;
    }
    return state.actionLogs.filter((item) => {
      const text = `${item.execution.action_type} ${item.execution.status} ${item.execution.result_summary ?? ""} ${item.decision_log?.summary ?? ""}`.toLowerCase();
      return text.includes(keyword);
    });
  }, [state.actionLogs, state.searchText]);

  const handleSimulate = async () => {
    if (!approvedPlan) {
      setState((previous) => ({
        ...previous,
        error: "Không có plan APPROVED để chạy simulate.",
      }));
      return;
    }
    setSimulateBusy(true);
    try {
      await simulateExecutionBatch(approvedPlan.id);
      await refreshData();
    } catch (error) {
      setState((previous) => ({ ...previous, error: parseApiError(error) }));
    } finally {
      setSimulateBusy(false);
    }
  };

  const handleEvaluateFeedback = async () => {
    if (!latestBatch) {
      return;
    }
    setFeedbackBusy(true);
    try {
      const feedback = await evaluateFeedback(latestBatch.id);
      setState((previous) => ({
        ...previous,
        feedback,
        error: null,
        lastRefreshAt: new Date().toISOString(),
      }));
    } catch (error) {
      setState((previous) => ({ ...previous, error: parseApiError(error) }));
    } finally {
      setFeedbackBusy(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      <PageHeading
        trailing={
          <Badge variant="neutral" className="text-[9px]">
            Đồng bộ lúc {formatTime(state.lastRefreshAt)}
          </Badge>
        }
      />

      {state.error ? (
        <InlineError
          title="Lỗi nhật ký hành động"
          message={state.error}
          onRetry={() => {
            void refreshData({ showLoading: true });
          }}
        />
      ) : null}

      {state.loading && state.actionLogs.length === 0 ? <SkeletonCards count={3} /> : null}

      <div className={`flex flex-col lg:flex-row justify-between items-start lg:items-end gap-6 ${state.loading && state.actionLogs.length === 0 ? "hidden" : ""}`}>
        <div className="space-y-3">
          <h1 className="text-4xl lg:text-5xl font-black text-mekong-navy tracking-tighter leading-none uppercase">
            Trung tâm can thiệp & học tập
          </h1>
          <p className="text-base text-mekong-slate font-medium max-w-3xl leading-relaxed">
            Theo dõi execution-batches, action logs, outcomes và feedback lifecycle từ backend.
          </p>
        </div>
        <div className="flex gap-4 w-full lg:w-auto">
          <Button variant="outline" className="flex-1 lg:flex-none h-14 px-8 border-slate-200 bg-white">
            <Share2 size={18} className="mr-2" /> Chia sẻ báo cáo
          </Button>
          <Button
            variant="navy"
            className="flex-1 lg:flex-none h-14 px-8 shadow-xl shadow-mekong-navy/20"
            onClick={() => void handleSimulate()}
            disabled={simulateBusy}
          >
            <Download size={18} className="mr-2" />
            {simulateBusy ? "Đang mô phỏng..." : "Mô phỏng plan đã duyệt"}
          </Button>
        </div>
      </div>

      <div className={`grid grid-cols-12 gap-8 ${state.loading && state.actionLogs.length === 0 ? "hidden" : ""}`}>
        <div className="col-span-12 lg:col-span-4 space-y-8">
          <Card variant="white" className="border-l-4 border-l-mekong-navy shadow-soft rounded-[32px] p-8">
            <div className="flex gap-5 items-start">
              <div className="p-3 bg-slate-50 rounded-2xl text-mekong-navy">
                <BrainCircuit size={24} />
              </div>
              <div className="space-y-4">
                <div>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] mb-2">
                    Feedback mới nhất
                  </p>
                  <p className="text-[15px] font-bold text-mekong-navy leading-relaxed italic">
                    {state.feedback?.evaluation.summary ?? "Chưa có feedback lifecycle cho batch gần nhất."}
                  </p>
                </div>
                <div className="flex justify-between items-center pt-2">
                  <Badge variant="cyan" className="px-3">
                    {state.feedback?.evaluation.outcome_class ?? "inconclusive"}
                  </Badge>
                  <span className="text-[10px] font-black text-slate-400">
                    {latestBatch ? formatDateTime(latestBatch.started_at) : "--"}
                  </span>
                </div>
                <button
                  className="text-[10px] font-black text-mekong-teal uppercase tracking-widest disabled:opacity-50"
                  disabled={!latestBatch || feedbackBusy}
                  onClick={() => void handleEvaluateFeedback()}
                >
                  {feedbackBusy ? "Đang đánh giá..." : "Đánh giá feedback"}
                </button>
              </div>
            </div>
          </Card>

          <Card variant="navy" padding="none" className="bg-mekong-navy text-white rounded-[40px] overflow-hidden min-h-[220px] flex flex-col p-10 shadow-2xl relative border border-white/5">
            <div className="relative z-10 space-y-2 flex-1">
              <p className="text-[11px] font-black text-slate-400 uppercase tracking-[0.3em] mb-6">
                Snapshot vận hành
              </p>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-[12px] font-bold text-slate-300 uppercase">Batches</span>
                  <span className="text-2xl font-black text-mekong-cyan">{state.batches.length}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[12px] font-bold text-slate-300 uppercase">Nhật ký</span>
                  <span className="text-2xl font-black text-mekong-cyan">{state.actionLogs.length}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[12px] font-bold text-slate-300 uppercase">Thành công</span>
                  <span className="text-2xl font-black text-mekong-cyan">{successfulActions}</span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        <div className="col-span-12 lg:col-span-8">
          <Card variant="white" padding="lg" className="h-full rounded-[40px] shadow-soft border border-slate-100 flex flex-col">
            <div className="flex justify-between items-center mb-8">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-mekong-teal/10 rounded-2xl text-mekong-teal border border-mekong-teal/20">
                  <RefreshCcw size={24} />
                </div>
                <div>
                  <h3 className="text-lg font-black text-mekong-navy uppercase tracking-tighter leading-none">
                    Execution batches gần đây
                  </h3>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-2">
                    Batch mới nhất: {latestBatch ? latestBatch.id.slice(0, 8) : "--"}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 bg-slate-50 rounded-full border border-slate-100 shadow-sm">
                <div className="w-2 h-2 bg-mekong-mint rounded-full animate-pulse" />
                <span className="text-[10px] font-black text-mekong-navy uppercase tracking-widest">
                  {state.loading ? "Đang tải" : "Đồng bộ"}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1">
              {state.batches.slice(0, 4).map((batch) => (
                <div key={batch.id} className="p-6 rounded-[30px] bg-slate-50/50 border border-slate-100 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-5">
                      <h5 className="text-[12px] font-black text-mekong-navy uppercase tracking-[0.2em]">
                        Batch #{batch.id.slice(0, 8)}
                      </h5>
                      <Badge variant="navy" className="text-[9px] uppercase">
                        {batch.status}
                      </Badge>
                    </div>
                    <p className="text-[13px] font-semibold text-slate-600">
                      Plan: {batch.plan_id.slice(0, 8)} • Steps: {batch.step_count}
                    </p>
                    <p className="text-[11px] font-black text-slate-400 uppercase tracking-widest mt-2">
                      Start: {formatDateTime(batch.started_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      <section className={`bg-white rounded-[48px] border border-slate-200 shadow-soft overflow-hidden ${state.loading && state.actionLogs.length === 0 ? "hidden" : ""}`}>
        <div className="bg-mekong-navy px-10 py-8 text-white flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/5 rounded-2xl border border-white/10 text-mekong-cyan shadow-xl">
              <ClipboardList size={26} />
            </div>
            <div>
              <h3 className="text-xl font-black uppercase tracking-tighter leading-none">Lịch sử action log chi tiết</h3>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.2em] mt-2 opacity-80">
                Nguồn: GET /api/v1/actions/logs
              </p>
            </div>
          </div>
          <div className="flex gap-3 w-full md:w-auto">
            <div className="relative flex-1 md:w-64">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
              <input
                type="text"
                placeholder="Tìm kiếm action/status..."
                value={state.searchText}
                onChange={(event) =>
                  setState((previous) => ({ ...previous, searchText: event.target.value }))
                }
                className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-12 pr-4 text-xs font-bold text-white focus:bg-white/10 outline-none transition-all"
              />
            </div>
            <Button variant="outline" className="border-white/20 text-white hover:bg-white/10 px-6 h-11 text-[11px]">
              <Filter size={14} className="mr-2" /> Bộ lọc
            </Button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-100">
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest">Thời gian</th>
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest">Action type</th>
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest">Result</th>
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest">Status</th>
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest text-center">Trace</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {filteredLogs.slice(0, 20).map((row) => (
                <tr key={row.execution.id} className="hover:bg-slate-50/30 transition-all group cursor-pointer">
                  <td className="px-10 py-8">
                    <p className="text-sm font-black text-mekong-navy mb-1 group-hover:text-mekong-teal transition-colors">
                      {formatDateTime(row.execution.started_at ?? row.execution.created_at)}
                    </p>
                    <p className="text-[10px] font-mono text-slate-400 font-bold">{row.execution.id.slice(0, 8)}</p>
                  </td>
                  <td className="px-10 py-8">
                    <span className="text-[14px] font-bold text-mekong-navy">{normalizeActionType(row.execution.action_type)}</span>
                  </td>
                  <td className="px-10 py-8">
                    <span className="text-[13px] font-semibold text-slate-600 line-clamp-2">
                      {row.execution.result_summary ?? row.decision_log?.summary ?? "--"}
                    </span>
                  </td>
                  <td className="px-10 py-8">
                    <Badge variant="navy" className="text-[9px] uppercase">
                      {row.execution.status}
                    </Badge>
                  </td>
                  <td className="px-10 py-8 text-center">
                    {row.decision_log ? (
                      <div className="w-10 h-10 rounded-full bg-mekong-mint/10 flex items-center justify-center text-mekong-mint mx-auto shadow-sm">
                        <CheckCircle2 size={20} strokeWidth={2.5} />
                      </div>
                    ) : (
                      <div className="text-[10px] font-black text-slate-400 uppercase">N/A</div>
                    )}
                  </td>
                </tr>
              ))}
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-6">
                    <EmptyState
                      title="Không có action log phù hợp"
                      description="Hãy đổi từ khóa tìm kiếm hoặc chạy simulate để sinh dữ liệu mới."
                      actionLabel="Làm mới"
                      onAction={() => {
                        void refreshData({ showLoading: true });
                      }}
                    />
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div className="bg-slate-50 px-10 py-6 flex justify-between items-center border-t border-slate-100">
          <span className="text-[11px] font-black text-slate-400 uppercase tracking-widest">
            Hiển thị {Math.min(filteredLogs.length, 20)} / {filteredLogs.length} action logs
          </span>
          <div className="flex items-center gap-2 text-[10px] font-black text-mekong-teal uppercase tracking-widest">
            Outcomes: {state.outcomes.length} <ArrowUpRight size={12} />
          </div>
        </div>
      </section>
    </div>
  );
}

export default ActionLogs;
