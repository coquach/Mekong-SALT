import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowUpRight,
  BrainCircuit,
  CheckCircle2,
  ClipboardList,
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
import { ApiError } from "../lib/api/types";
import { useLivePageRefresh } from "../lib/hooks/useLivePageRefresh";
import { useGraphStream } from "../lib/hooks/useGraphStream";
import { ExecutionGraphViewer } from "../components/graph/ExecutionGraphViewer";
import {
  evaluateFeedback,
  getActionLogs,
  getActionOutcomes,
  getExecutionBatches,
  getExecutionBatchDetail,
  getLatestFeedback,
  type ActionOutcomeRead,
  type ExecutionBatchDetail,
  type ExecutionBatchRead,
  type FeedbackLifecycleRead,
} from "../lib/api/operations";
import { getPlans, type ActionPlanRead } from "../lib/api/strategy";
import { getApiErrorMessage } from "../lib/api/error";
import { formatDateTime as formatDateTimeUtil, formatTime as formatTimeUtil, formatLabel as formatLabelUtil } from "../lib/format";
import type { ExecutionGraphRead } from "../lib/api/graph";

type ActionLogsState = {
  loading: boolean;
  error: string | null;
  searchText: string;
  plans: ActionPlanRead[];
  actionLogs: Awaited<ReturnType<typeof getActionLogs>>["items"];
  batches: ExecutionBatchRead[];
  selectedBatchId: string | null;
  selectedBatchDetail: ExecutionBatchDetail | null;
  selectedBatchLoading: boolean;
  selectedBatchError: string | null;
  outcomes: ActionOutcomeRead[];
  feedback: FeedbackLifecycleRead | null;
  lastRefreshAt: string | null;
};

export function ActionLogs() {
  const [state, setState] = useState<ActionLogsState>(() => {
    return {
      loading: true,
      error: null,
      searchText: "",
      plans: [],
      actionLogs: [],
      batches: [],
      selectedBatchId: null,
      selectedBatchDetail: null,
      selectedBatchLoading: false,
      selectedBatchError: null,
      outcomes: [],
      feedback: null,
      lastRefreshAt: null,
    };
  });
  const [feedbackBusy, setFeedbackBusy] = useState(false);
  const [liveBatchGraph, setLiveBatchGraph] = useState<ExecutionGraphRead | null>(null);
  const [liveBatchId, setLiveBatchId] = useState<string | null>(null);
  const selectedBatchRequestIdRef = useRef(0);

  const refreshSelectedBatch = useCallback(
    async (batchId: string | null, options?: { signal?: AbortSignal; showLoading?: boolean }) => {
      const signal = options?.signal;
      const showLoading = options?.showLoading ?? false;
      const requestId = ++selectedBatchRequestIdRef.current;

      if (!batchId) {
        setState((previous) => ({
          ...previous,
          selectedBatchId: null,
          selectedBatchDetail: null,
          selectedBatchLoading: false,
          selectedBatchError: null,
          feedback: null,
        }));
        setLiveBatchId(null);
        setLiveBatchGraph(null);
        return;
      }

      if (showLoading) {
        setState((previous) => ({
          ...previous,
          selectedBatchId: batchId,
          selectedBatchLoading: true,
          selectedBatchError: null,
        }));
      }

      try {
        const [detailResponse, feedbackResponse] = await Promise.all([
          getExecutionBatchDetail(batchId, signal),
          getLatestFeedback(batchId, signal).catch((error) => {
            if (error instanceof ApiError && error.statusCode === 404) {
              return null;
            }
            throw error;
          }),
        ]);

        if (signal?.aborted || requestId !== selectedBatchRequestIdRef.current) {
          return;
        }

        setState((previous) => ({
          ...previous,
          selectedBatchId: batchId,
          selectedBatchDetail: detailResponse,
          selectedBatchLoading: false,
          selectedBatchError: null,
          feedback: feedbackResponse,
        }));
        setLiveBatchId(batchId);
        setLiveBatchGraph(detailResponse.execution_graph ?? null);
      } catch (error) {
        if (signal?.aborted || requestId !== selectedBatchRequestIdRef.current) {
          return;
        }
        setState((previous) => ({
          ...previous,
          selectedBatchId: batchId,
          selectedBatchLoading: false,
          selectedBatchError: getApiErrorMessage(error, "Không tải được graph thực thi."),
        }));
      }
    },
    [],
  );

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

      const selectedBatchId =
        batches.items.find((batch) => batch.id === state.selectedBatchId)?.id ?? liveBatchId ?? batches.items[0]?.id ?? null;

      setState((previous) => ({
        ...previous,
        loading: false,
        error: null,
        plans,
        actionLogs: actionLogs.items,
        batches: batches.items,
        selectedBatchId,
        selectedBatchDetail: null,
        selectedBatchLoading: false,
        selectedBatchError: null,
        outcomes: outcomes.items,
        feedback: null,
        lastRefreshAt: new Date().toISOString(),
      }));

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

  useLivePageRefresh({
    refresh: refreshData,
    pollIntervalMs: 10_000,
  });

  useGraphStream({
    graphType: "execution_batch",
    enabled: true,
    onTransition: (payload) => {
      if (payload.graph_type !== "execution_batch") {
        return;
      }

      const targetBatchId = payload.execution_batch_id ?? null;
      const selectedBatchId = state.selectedBatchDetail?.batch.id ?? state.selectedBatchId;
      if (!targetBatchId) {
        return;
      }
      if (state.selectedBatchDetail?.batch.id && selectedBatchId !== null && targetBatchId !== selectedBatchId) {
        return;
      }

      if (targetBatchId) {
        setLiveBatchId(targetBatchId);
        setState((previous) => {
          if (previous.selectedBatchId === targetBatchId) {
            return previous;
          }

          return {
            ...previous,
            selectedBatchId: targetBatchId,
          };
        });
      }
      if (payload.graph_snapshot !== undefined && payload.graph_snapshot !== null) {
        setLiveBatchGraph(payload.graph_snapshot);
      }
    },
  });

  useEffect(() => {
    if (state.batches.length === 0) {
      return;
    }
    const selectedBatch = state.batches.find((batch) => batch.id === state.selectedBatchId);
    if (!selectedBatch) {
      return;
    }
    if (state.selectedBatchLoading || state.selectedBatchError) {
      return;
    }
    if (state.selectedBatchDetail?.batch.id === selectedBatch.id) {
      return;
    }
    void refreshSelectedBatch(selectedBatch.id, { showLoading: true });
  }, [refreshSelectedBatch, state.batches, state.selectedBatchDetail?.batch.id, state.selectedBatchError, state.selectedBatchId, state.selectedBatchLoading]);

  useEffect(() => {
    const visibleBatchId = state.selectedBatchDetail?.batch.id ?? state.selectedBatchId ?? null;
    if (!visibleBatchId) {
      setLiveBatchId(null);
      setLiveBatchGraph(null);
      return;
    }

    if (visibleBatchId !== liveBatchId) {
      setLiveBatchId(visibleBatchId);
      setLiveBatchGraph(state.selectedBatchDetail?.execution_graph ?? null);
      return;
    }

    if (liveBatchGraph === null && state.selectedBatchDetail?.execution_graph !== null) {
      setLiveBatchGraph(state.selectedBatchDetail?.execution_graph ?? null);
    }
  }, [liveBatchGraph, liveBatchId, state.selectedBatchDetail?.batch.id, state.selectedBatchDetail?.execution_graph, state.selectedBatchId]);

  const latestBatch = state.batches[0] ?? null;
  const visibleExecutionGraph = liveBatchGraph ?? state.selectedBatchDetail?.execution_graph ?? null;
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

  const handleEvaluateFeedback = async () => {
    const activeBatch = state.batches.find((batch) => batch.id === state.selectedBatchId) ?? latestBatch;
    if (!activeBatch) {
      return;
    }
    setFeedbackBusy(true);
    try {
      const feedback = await evaluateFeedback(activeBatch.id);
      const nextLastRefreshAt = new Date().toISOString();
      setState((previous) => ({
        ...previous,
        feedback,
        error: null,
        lastRefreshAt: nextLastRefreshAt,
      }));
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
        
        <div className="flex gap-4 w-full lg:w-auto">
          <Button variant="outline" className="flex-1 lg:flex-none h-14 px-8 border-slate-200 bg-white">
            <Share2 size={18} className="mr-2" /> Chia sẻ
          </Button>
          <Button
            variant="navy"
            className="flex-1 lg:flex-none h-14 px-8 shadow-xl shadow-mekong-navy/20"
            onClick={() => void refreshData({ showLoading: true })}
          >
            <RefreshCcw size={18} className="mr-2" />
            Làm mới
          </Button>
          <div className="flex-1 lg:flex-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-[11px] font-semibold leading-relaxed text-slate-600">
            Chạy mô phỏng hiện được backend worker xử lý tự động sau khi plan được duyệt.
          </div>
        </div>
      </div>

   

      <Card variant="white" className={`rounded-4xl border border-slate-200 p-5 shadow-soft ${state.loading && state.actionLogs.length === 0 ? "hidden" : ""}`}>
        <div className="space-y-5">
          <div className="space-y-4">
            <div className="space-y-2">
              <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Execution graph</p>
              <h3 className="text-lg font-black text-mekong-navy">
                Chọn batch ở dưới rồi xem graph để hiểu nó đã chạy qua những node nào.
              </h3>
              <p className="text-sm font-semibold leading-relaxed text-slate-600">
                Graph chỉ nên đọc sau khi biết batch nào đang được chọn. Trạng thái hiện tại và feedback sẽ nằm ở cùng cụm thông tin để tránh nhìn rời rạc.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-2">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">Batch đang chọn</p>
                <p className="mt-1 text-sm font-semibold text-slate-700">
                  {state.selectedBatchDetail || liveBatchId ? "Đang xem phiên được chọn" : "Chưa chọn phiên"}
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">Graph status</p>
                <p className="mt-1 text-sm font-semibold text-slate-700">
                  {state.selectedBatchLoading ? "loading" : visibleExecutionGraph?.status ?? "pending"}
                </p>
              </div>
            </div>
            {state.selectedBatchError ? (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-[12px] font-semibold text-red-800">
                {state.selectedBatchError}
              </div>
            ) : null}
          </div>

          <div>
            {state.selectedBatchLoading && !state.selectedBatchDetail ? (
              <div className="h-72 animate-pulse rounded-4xl bg-slate-100" />
            ) : (
              <ExecutionGraphViewer
                graph={visibleExecutionGraph}
                title="Batch Execution Graph"
                subtitle="Graph from execution batch detail"
                emptyTitle="Chưa có graph batch"
                emptyDescription="Khi backend trả về execution_graph, viewer này sẽ hiển thị luồng thực thi của batch đang chọn."
              />
            )}
          </div>
        </div>
      </Card>

      <div className={`space-y-8 ${state.loading && state.actionLogs.length === 0 ? "hidden" : ""}`}>
        <div className="space-y-8">
          <Card variant="white" className="border-l-4 border-l-mekong-navy shadow-soft rounded-4xl p-8">
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
                    {state.batches.find((batch) => batch.id === state.selectedBatchId)
                      ? formatDateTimeUtil(
                          state.batches.find((batch) => batch.id === state.selectedBatchId)?.started_at ?? null,
                        )
                      : latestBatch
                        ? formatDateTimeUtil(latestBatch.started_at)
                        : "--"}
                  </span>
                </div>
                <button
                  className="text-[10px] font-black text-mekong-teal uppercase tracking-widest disabled:opacity-50"
                  disabled={!(state.batches.find((batch) => batch.id === state.selectedBatchId) ?? latestBatch) || feedbackBusy}
                  onClick={() => void handleEvaluateFeedback()}
                >
                  {feedbackBusy ? "Đang cập nhật..." : "Xem kết quả sau chạy"}
                </button>
              </div>
            </div>
          </Card>

          <Card variant="navy" padding="none" className="bg-mekong-navy text-white rounded-4xl overflow-hidden min-h-55 flex flex-col p-10 shadow-2xl relative border border-white/5">
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

        <div>
          <Card variant="white" padding="lg" className="h-full rounded-4xl shadow-soft border border-slate-100 flex flex-col">
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
                    Phiên gần nhất: {latestBatch ? formatDateTimeUtil(latestBatch.started_at) : "--"}
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

            <div className="grid grid-cols-1 gap-6 flex-1">
              {state.batches.slice(0, 4).map((batch) => {
                const isSelected = state.selectedBatchId === batch.id;
                return (
                <button
                  key={batch.id}
                  type="button"
                  onClick={() => void refreshSelectedBatch(batch.id, { showLoading: true })}
                  className={`p-6 rounded-3xl border flex flex-col justify-between text-left transition-all duration-300 ${
                    isSelected
                      ? "bg-white border-mekong-cyan/30 shadow-xl shadow-mekong-cyan/10"
                      : "bg-slate-50/50 border-slate-100 hover:bg-white hover:shadow-xl"
                  }`}
                >
                  <div>
                    <div className="flex justify-between items-start mb-5">
                      <h5 className="text-[12px] font-black text-mekong-navy uppercase tracking-[0.2em]">
                        Phiên gần đây
                      </h5>
                      <Badge variant="navy" className="text-[9px] uppercase">
                        {batch.status}
                      </Badge>
                    </div>
                    <p className="text-[13px] font-semibold text-slate-600">
                      Số bước: {batch.step_count}
                    </p>
                    <p className="text-[11px] font-black text-slate-400 uppercase tracking-widest mt-2">
                      Bắt đầu: {formatDateTimeUtil(batch.started_at)}
                    </p>
                  </div>
                </button>
                );
              })}
            </div>
          </Card>
        </div>
      </div>

      <section className={`bg-white rounded-4xl border border-slate-200 shadow-soft overflow-hidden ${state.loading && state.actionLogs.length === 0 ? "hidden" : ""}`}>
        <div className="bg-mekong-navy px-10 py-8 text-white space-y-4">
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
          <div className="space-y-3 w-full">
            <div className="relative w-full">
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
            <Button variant="outline" className="w-full border-white/20 text-white hover:bg-white/10 px-6 h-11 text-[11px]">
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
                    <p className="text-[10px] font-mono text-slate-400 font-bold">Bản ghi</p>
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
