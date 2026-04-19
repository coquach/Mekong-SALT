import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Terminal } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { ExecutionGraphViewer } from "../components/graph/ExecutionGraphViewer";
import { InlineError, SkeletonCards } from "../components/ui/AsyncState";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { PageHeading } from "../components/ui/PageHeading";
import { getApiErrorMessage } from "../lib/api/error";
import { getApiBaseUrl } from "../lib/api/http";
import { getAgentRun, type AgentRunRead } from "../lib/api/strategy";

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

function buildRunMessage(run: AgentRunRead | null): string {
  if (!run) {
    return "";
  }

  if (run.error_message) {
    return run.error_message;
  }

  if (run.trace && typeof run.trace === "object") {
    const trace = run.trace as {
      incident_decision?: { decision?: string };
      plan_decision?: { decision?: string };
      retrieval_trace?: { total_evidence?: number };
      planning_transition_log?: Array<{ node?: string }>;
    };

    const segments = [
      trace.incident_decision?.decision ? `incident:${trace.incident_decision.decision}` : null,
      trace.plan_decision?.decision ? `plan:${trace.plan_decision.decision}` : null,
      typeof trace.retrieval_trace?.total_evidence === "number"
        ? `${trace.retrieval_trace.total_evidence} evidence`
        : null,
      trace.planning_transition_log?.length ? `${trace.planning_transition_log.length} nodes` : null,
    ].filter((segment): segment is string => Boolean(segment));

    if (segments.length > 0) {
      return segments.join(" · ");
    }
  }

  return JSON.stringify(run.payload).slice(0, 220);
}

export default function RunGraphDetail() {
  const { runId } = useParams<{ runId: string }>();
  const [state, setState] = useState<{
    runId: string | null;
    run: AgentRunRead | null;
    loading: boolean;
    error: string | null;
  }>(() => ({
    runId: runId ?? null,
    run: null,
    loading: Boolean(runId),
    error: null,
  }));

  const missingRunId = runId === undefined;

  useEffect(() => {
    if (!runId) {
      return;
    }

    let cancelled = false;

    void getAgentRun(runId)
      .then((response) => {
        if (cancelled) {
          return;
        }
        setState({
          runId,
          run: response,
          loading: false,
          error: null,
        });
      })
      .catch((caughtError) => {
        if (cancelled) {
          return;
        }
        setState({
          runId,
          run: null,
          loading: false,
          error: getApiErrorMessage(caughtError, "Không tải được chi tiết run."),
        });
      });

    return () => {
      cancelled = true;
    };
  }, [runId]);

  const isStale = state.runId !== (runId ?? null);
  const run = isStale ? null : state.run;
  const loading = missingRunId ? false : state.loading || isStale;
  const error = missingRunId ? "Thiếu runId trên đường dẫn." : state.error;
  const graph = run?.execution_graph ?? null;
  const runMessage = useMemo(() => buildRunMessage(run), [run]);
  const backendBaseUrl = getApiBaseUrl();
  const runApiUrl = runId ? `${backendBaseUrl}/agent/runs/${runId}` : null;

  if (missingRunId) {
    return (
      <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <PageHeading
          trailing={
            <Link
              to="/strategy"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-[10px] font-black uppercase tracking-[0.14em] text-mekong-navy shadow-sm transition-all hover:border-mekong-cyan/30 hover:text-mekong-teal"
            >
              <ArrowLeft size={14} />
              Quay lại điều phối
            </Link>
          }
        />

        <InlineError
          title="Thiếu runId"
          message="Không thể tải chi tiết run khi đường dẫn không có runId."
        />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <PageHeading
        trailing={
          <Link
            to="/strategy"
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-[10px] font-black uppercase tracking-[0.14em] text-mekong-navy shadow-sm transition-all hover:border-mekong-cyan/30 hover:text-mekong-teal"
          >
            <ArrowLeft size={14} />
            Quay lại điều phối
          </Link>
        }
      />

      {error ? (
        <InlineError
          title="Lỗi chi tiết run"
          message={error}
          onRetry={() => {
            if (!runId) {
              return;
            }

            setState((previous) => ({
              ...previous,
              runId,
              loading: true,
              error: null,
            }));

            void getAgentRun(runId)
              .then((response) => {
                setState({
                  runId,
                  run: response,
                  loading: false,
                  error: null,
                });
              })
              .catch((caughtError) => {
                setState({
                  runId,
                  run: null,
                  loading: false,
                  error: getApiErrorMessage(caughtError, "Không tải được chi tiết run."),
                });
              });
          }}
        />
      ) : null}

      {loading && !run ? <SkeletonCards count={2} /> : null}

      {!loading && run ? (
        <>
          <Card variant="white" className="rounded-4xl border border-slate-200 p-6 shadow-soft">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-2">
                <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Run detail</p>
                <h1 className="text-3xl lg:text-4xl font-black text-mekong-navy tracking-tighter leading-none uppercase">
                  {run.run_type}
                </h1>
                <p className="text-sm font-semibold leading-relaxed text-slate-600 max-w-4xl">
                  {runMessage || "Graph snapshot của run này đang được chuẩn hóa từ backend."}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2 shrink-0">
                <Badge variant="navy" className="text-[9px] uppercase">
                  {run.status}
                </Badge>
                <Badge variant="neutral" className="text-[9px] uppercase">
                  {run.id.slice(0, 8)}
                </Badge>
                <Badge variant="neutral" className="text-[9px] uppercase">
                  {formatDatetime(run.started_at)}
                </Badge>
              </div>
            </div>

            <div className="mt-5 rounded-3xl border border-mekong-cyan/20 bg-mekong-cyan/5 p-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div className="space-y-1">
                  <p className="text-[9px] font-black uppercase tracking-[0.22em] text-mekong-cyan">Backend source</p>
                  <p className="text-sm font-semibold text-slate-700">
                    Trang này gọi trực tiếp backend qua API detail của agent run để lấy trace và execution_graph.
                  </p>
                  <p className="text-[11px] font-black uppercase tracking-[0.16em] text-slate-500">
                    GET {runApiUrl ?? "--"}
                  </p>
                </div>
                {runApiUrl ? (
                  <a
                    href={runApiUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center justify-center rounded-xl border border-mekong-cyan/20 bg-white px-3 py-2 text-[10px] font-black uppercase tracking-[0.14em] text-mekong-navy transition-all hover:border-mekong-cyan/40 hover:text-mekong-teal"
                  >
                    Mở JSON backend
                  </a>
                ) : null}
              </div>
            </div>

            <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-3">
              <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                <p className="text-[9px] font-black uppercase tracking-[0.22em] text-slate-400">Trace</p>
                <p className="mt-2 text-sm font-semibold text-slate-700 line-clamp-3">
                  {run.trace ? "Execution graph and trace summary are available." : "Run này chưa có trace."}
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                <p className="text-[9px] font-black uppercase tracking-[0.22em] text-slate-400">Execution graph</p>
                <p className="mt-2 text-sm font-semibold text-slate-700">
                  {graph ? `${graph.nodes.length} nodes · ${graph.edges.length} edges` : "Chưa có execution graph."}
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                <p className="text-[9px] font-black uppercase tracking-[0.22em] text-slate-400">Timeline</p>
                <p className="mt-2 text-sm font-semibold text-slate-700">
                  Start {formatDatetime(run.started_at)} · Finish {formatDatetime(run.finished_at)}
                </p>
              </div>
            </div>
          </Card>

          <ExecutionGraphViewer
            graph={graph}
            title="Run Execution Graph"
            subtitle={`run ${run.id.slice(0, 8)} · detail view`}
            emptyTitle="Chưa có execution graph"
            emptyDescription="Run này chưa trả về execution_graph từ backend hoặc graph chưa được chuẩn hóa."
          />

          <Card variant="white" className="rounded-4xl border border-slate-200 p-6 shadow-soft">
            <div className="flex items-center gap-3 text-mekong-navy">
              <Terminal size={18} />
              <h3 className="text-sm font-black uppercase tracking-[0.18em]">Run metadata</h3>
            </div>
            <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
                <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400">Trigger</p>
                <p className="mt-2 text-sm font-semibold text-slate-700">{run.trigger_source}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
                <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400">Plan</p>
                <p className="mt-2 text-sm font-semibold text-slate-700">{run.action_plan_id ?? "--"}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
                <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400">Incident</p>
                <p className="mt-2 text-sm font-semibold text-slate-700">{run.incident_id ?? "--"}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
                <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400">Region</p>
                <p className="mt-2 text-sm font-semibold text-slate-700">{run.region_id ?? "--"}</p>
              </div>
            </div>
          </Card>
        </>
      ) : null}
    </div>
  );
}
