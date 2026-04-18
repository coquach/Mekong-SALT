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
import { isPageCacheFresh, readPageCache, writePageCache } from "../lib/cache/pageCache";
import { ApiError } from "../lib/api/types";
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
import { getApiErrorMessage } from "../lib/api/error";
import { formatDateTime as formatDateTimeUtil, formatTime as formatTimeUtil, formatLabel as formatLabelUtil } from "../lib/format";

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

type ActionLogsCache = {
  state: Pick<ActionLogsState, "plans" | "actionLogs" | "batches" | "outcomes" | "feedback" | "lastRefreshAt">;
};

const ACTION_LOGS_CACHE_KEY = "mekong.cache.action-logs";
const ACTION_LOGS_CACHE_MAX_AGE_MS = 30_000;

export function ActionLogs() {
  const cachedActionLogs = useMemo(() => readPageCache<ActionLogsCache>(ACTION_LOGS_CACHE_KEY), []);
  const [state, setState] = useState<ActionLogsState>(() => {
    const cachedState = cachedActionLogs?.value.state;
    if (!cachedState) {
      return {
        loading: true,
        error: null,
        searchText: "",
        plans: [],
        actionLogs: [],
        batches: [],
        outcomes: [],
        feedback: null,
        lastRefreshAt: null,
      };
    }

    return {
      loading: false,
      error: null,
      searchText: "",
      plans: cachedState.plans,
      actionLogs: cachedState.actionLogs,
      batches: cachedState.batches,
      outcomes: cachedState.outcomes,
      feedback: cachedState.feedback,
      lastRefreshAt: cachedState.lastRefreshAt,
    };
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

      writePageCache<ActionLogsCache>(ACTION_LOGS_CACHE_KEY, {
        state: {
          plans,
          actionLogs: actionLogs.items,
          batches: batches.items,
          outcomes: outcomes.items,
          feedback,
          lastRefreshAt: new Date().toISOString(),
        },
      });
    } catch (error) {
      if (signal?.aborted) {
        return;
      }
      setState((previous) => ({
        ...previous,
        loading: false,
        error: getApiErrorMessage(error, "Không tải được dữ liệu nhật ký hành động."),
      }));
    }
  };

  useEffect(() => {
    const abortController = new AbortController();
    const shouldSkipInitialRefresh =
      cachedActionLogs !== null && isPageCacheFresh(cachedActionLogs, ACTION_LOGS_CACHE_MAX_AGE_MS);

    if (shouldSkipInitialRefresh) {
      return () => abortController.abort();
    }

    void refreshData({ signal: abortController.signal, showLoading: true });
    return () => abortController.abort();
  }, [cachedActionLogs]);

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
      setState((previous) => ({ ...previous, error: getApiErrorMessage(error, "Không tải được dữ liệu nhật ký hành động.") }));
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
      const nextLastRefreshAt = new Date().toISOString();
      setState((previous) => ({
        ...previous,
        feedback,
        error: null,
        lastRefreshAt: nextLastRefreshAt,
      }));
      writePageCache<ActionLogsCache>(ACTION_LOGS_CACHE_KEY, {
        state: {
          plans: state.plans,
          actionLogs: state.actionLogs,
          batches: state.batches,
          outcomes: state.outcomes,
          feedback,
          lastRefreshAt: nextLastRefreshAt,
        },
      });
    } catch (error) {
      setState((previous) => ({ ...previous, error: getApiErrorMessage(error, "Không tải được dữ liệu nhật ký hành động.") }));
    } finally {
      setFeedbackBusy(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      <PageHeading
        trailing={
          <Badge variant="neutral" className="text-[9px]">
            Đồng bộ lúc {formatTimeUtil(state.lastRefreshAt)}
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
            Nhật ký thực thi
          </h1>
          <p className="text-base text-mekong-slate font-medium max-w-3xl leading-relaxed">
            Xem hệ thống đã làm gì sau khi một kế hoạch được duyệt, kết quả ra sao và phản hồi nào được ghi nhận.
          </p>
        </div>
          <div className="flex gap-4 w-full lg:w-auto">
          <Button variant="outline" className="flex-1 lg:flex-none h-14 px-8 border-slate-200 bg-white">
            <Share2 size={18} className="mr-2" /> Chia sẻ
          </Button>
          <Button
            variant="navy"
            className="flex-1 lg:flex-none h-14 px-8 shadow-xl shadow-mekong-navy/20"
            onClick={() => void handleSimulate()}
            disabled={simulateBusy}
          >
            <Download size={18} className="mr-2" />
            {simulateBusy ? "Đang chạy..." : "Chạy kế hoạch đã duyệt"}
          </Button>
        </div>
      </div>

      <Card variant="white" className={`rounded-[32px] border border-slate-200 p-5 shadow-soft ${state.loading && state.actionLogs.length === 0 ? "hidden" : ""}`}>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.4fr_1fr_1fr]">
          <div className="space-y-2">
            <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Cách đọc nhanh</p>
            <h3 className="text-lg font-black text-mekong-navy">Màn này cho biết mỗi lần hệ thống đã làm gì và kết quả cuối cùng ra sao.</h3>
            <p className="text-sm font-semibold leading-relaxed text-slate-600">
              Mỗi thẻ bên phải là một lần chạy. Bảng bên dưới là từng bước nhỏ trong lần chạy đó. Nếu muốn xem phản hồi sau chạy, nhìn card feedback ở bên trái.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">1. Phiên chạy</p>
            <p className="mt-1 text-sm font-semibold text-slate-700">Một lần hệ thống xử lý một kế hoạch.</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">2. Nhật ký bước</p>
            <p className="mt-1 text-sm font-semibold text-slate-700">Từng hành động trong lần chạy đó.</p>
          </div>
        </div>
      </Card>

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
                    Kết quả sau chạy
                  </p>
                  <p className="text-[15px] font-bold text-mekong-navy leading-relaxed italic">
                    {state.feedback?.evaluation.summary ?? "Chưa có kết quả phản hồi cho phiên chạy gần nhất."}
                  </p>
                </div>
                <div className="flex justify-between items-center pt-2">
                  <Badge variant="cyan" className="px-3">
                    {state.feedback?.evaluation.outcome_class ?? "inconclusive"}
                  </Badge>
                  <span className="text-[10px] font-black text-slate-400">
                    {latestBatch ? formatDateTimeUtil(latestBatch.started_at) : "--"}
                  </span>
                </div>
                <button
                  className="text-[10px] font-black text-mekong-teal uppercase tracking-widest disabled:opacity-50"
                  disabled={!latestBatch || feedbackBusy}
                  onClick={() => void handleEvaluateFeedback()}
                >
                  {feedbackBusy ? "Đang cập nhật..." : "Xem kết quả sau chạy"}
                </button>
              </div>
            </div>
          </Card>

          <Card variant="navy" padding="none" className="bg-mekong-navy text-white rounded-[40px] overflow-hidden min-h-[220px] flex flex-col p-10 shadow-2xl relative border border-white/5">
            <div className="relative z-10 space-y-2 flex-1">
              <p className="text-[11px] font-black text-slate-400 uppercase tracking-[0.3em] mb-6">
                Tóm tắt nhanh
              </p>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-[12px] font-bold text-slate-300 uppercase">Phiên chạy</span>
                  <span className="text-2xl font-black text-mekong-cyan">{state.batches.length}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[12px] font-bold text-slate-300 uppercase">Bước thực thi</span>
                  <span className="text-2xl font-black text-mekong-cyan">{state.actionLogs.length}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[12px] font-bold text-slate-300 uppercase">Bước thành công</span>
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
                    Các phiên chạy gần đây
                  </h3>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-2">
                    Phiên gần nhất: {latestBatch ? latestBatch.id.slice(0, 8) : "--"}
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
                        Phiên #{batch.id.slice(0, 8)}
                      </h5>
                      <Badge variant="navy" className="text-[9px] uppercase">
                        {batch.status}
                      </Badge>
                    </div>
                    <p className="text-[13px] font-semibold text-slate-600">
                      Kế hoạch: {batch.plan_id.slice(0, 8)} · Số bước: {batch.step_count}
                    </p>
                    <p className="text-[11px] font-black text-slate-400 uppercase tracking-widest mt-2">
                      Bắt đầu: {formatDateTimeUtil(batch.started_at)}
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
                  <h3 className="text-xl font-black uppercase tracking-tighter leading-none">Chi tiết từng bước</h3>
                  <p className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.2em] mt-2 opacity-80">
                    Nguồn: dữ liệu nhật ký từ backend
                  </p>
                </div>
              </div>
          <div className="flex gap-3 w-full md:w-auto">
            <div className="relative flex-1 md:w-64">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
              <input
                type="text"
                placeholder="Tìm theo hành động, trạng thái, kết quả..."
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
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest">Thời điểm</th>
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest">Hành động</th>
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest">Kết quả</th>
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest">Trạng thái</th>
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest text-center">Có phản hồi?</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {filteredLogs.slice(0, 20).map((row) => (
                <tr key={row.execution.id} className="hover:bg-slate-50/30 transition-all group cursor-pointer">
                  <td className="px-10 py-8">
                    <p className="text-sm font-black text-mekong-navy mb-1 group-hover:text-mekong-teal transition-colors">
                      {formatDateTimeUtil(row.execution.started_at ?? row.execution.created_at)}
                    </p>
                    <p className="text-[10px] font-mono text-slate-400 font-bold">{row.execution.id.slice(0, 8)}</p>
                  </td>
                  <td className="px-10 py-8">
                    <span className="text-[14px] font-bold text-mekong-navy">{formatLabelUtil(row.execution.action_type)}</span>
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
                      title="Không có nhật ký hành động phù hợp"
                      description="Hãy đổi từ khóa tìm kiếm hoặc chạy mô phỏng để sinh dữ liệu mới."
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
            Hiển thị {Math.min(filteredLogs.length, 20)} / {filteredLogs.length} bước
          </span>
          <div className="flex items-center gap-2 text-[10px] font-black text-mekong-teal uppercase tracking-widest">
            Kết quả đã ghi: {state.outcomes.length} <ArrowUpRight size={12} />
          </div>
        </div>
      </section>
    </div>
  );
}

export default ActionLogs;
