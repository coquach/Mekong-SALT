import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Clock3, FileText, Link as LinkIcon, MapPinned, Search } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import { EmptyState, InlineError, SkeletonCards } from "../components/ui/AsyncState";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { getMemoryCases, type MemoryCaseRead } from "../lib/api/memoryCases";

type MemoryCaseCitation = {
  citation?: string;
  title?: string;
  source?: string;
  evidence_source?: string;
  source_uri?: string;
  memory_case_id?: string;
  incident_id?: string;
  plan_id?: string;
  execution_id?: string;
  occurred_at?: string;
  score?: number | string;
  rank?: number;
  raw_citation?: string;
};

type MemoryCasesLocationState = {
  sourceTitle?: string | null;
  sourceSubtitle?: string | null;
  sourceGraphType?: string | null;
  sourceGraphStatus?: string | null;
  sourceGraphSummary?: string | null;
  memoryCases?: MemoryCaseCitation[];
};

function formatCitationScore(value: number | string | undefined): string {
  if (typeof value === "number") {
    return value.toFixed(2);
  }
  if (typeof value === "string" && value.trim().length > 0) {
    return value.trim();
  }
  return "--";
}

function formatMemoryCaseTitle(citation: MemoryCaseCitation): string {
  const title = citation.title ?? citation.citation ?? citation.raw_citation;
  if (typeof title === "string" && title.trim().length > 0) {
    return title.trim();
  }
  return "Memory case";
}

function formatShortId(value: string | null | undefined): string {
  if (!value) {
    return "--";
  }
  return value.length > 8 ? `${value.slice(0, 8)}…` : value;
}

function formatDatetime(value: string | null | undefined): string {
  if (!value) {
    return "--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("vi-VN", { hour12: false });
}

function isApiMemoryCase(value: MemoryCaseRead | MemoryCaseCitation): value is MemoryCaseRead {
  return Object.prototype.hasOwnProperty.call(value, "outcome_class");
}

function normalizeGraphMemoryCases(items: MemoryCaseCitation[]): MemoryCaseCitation[] {
  return items.map((item) => ({
    citation: item.citation,
    title: item.title,
    source: item.source ?? item.evidence_source,
    evidence_source: item.evidence_source,
    source_uri: item.source_uri,
    memory_case_id: item.memory_case_id,
    incident_id: item.incident_id,
    plan_id: item.plan_id,
    execution_id: item.execution_id,
    occurred_at: item.occurred_at,
    score: item.score,
    rank: item.rank,
    raw_citation: item.raw_citation,
  }));
}

function normalizeApiMemoryCases(items: MemoryCaseRead[]): MemoryCaseCitation[] {
  return items.map((item) => ({
    title: item.objective ?? item.summary,
    citation: item.summary,
    memory_case_id: item.id,
    incident_id: item.incident_id ?? undefined,
    plan_id: item.action_plan_id ?? undefined,
    execution_id: item.action_execution_id ?? undefined,
    occurred_at: item.occurred_at,
    score: undefined,
    raw_citation: undefined,
  }));
}

export default function MemoryCases() {
  const location = useLocation();
  const state = (location.state as MemoryCasesLocationState | null) ?? null;
  const graphMemoryCases = useMemo(() => normalizeGraphMemoryCases(state?.memoryCases ?? []), [state?.memoryCases]);
  const [apiMemoryCases, setApiMemoryCases] = useState<MemoryCaseCitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    setLoading(true);
    setError(null);

    void getMemoryCases({ limit: 24 }, controller.signal)
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        setApiMemoryCases(normalizeApiMemoryCases(response.items));
      })
      .catch((fetchError) => {
        if (controller.signal.aborted) {
          return;
        }
        setError(fetchError instanceof Error ? fetchError.message : "Không tải được memory case.");
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, []);

  const memoryCases = apiMemoryCases.length > 0 ? apiMemoryCases : graphMemoryCases;
  const displayedCount = memoryCases.length;

  return (
    <div className="mx-auto flex w-full max-w-425 flex-col gap-6 px-4 py-6 lg:px-10">
      <Card variant="white" className="rounded-4xl border border-slate-100 p-6 shadow-soft">
        <div className="space-y-3">
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Memory cases</p>
          <h1 className="text-2xl font-black tracking-tight text-mekong-navy md:text-4xl">Trang riêng cho memory case</h1>
          <p className="max-w-3xl text-sm font-medium leading-relaxed text-slate-600 md:text-base">
            Trang này tải danh sách memory case từ backend API và có thể nhận thêm ngữ cảnh khi bạn mở nó từ graph retrieval.
          </p>
        </div>
      </Card>

      <Card variant="navy" className="rounded-4xl border border-white/10 bg-[#00203F] p-6 shadow-2xl">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-mekong-cyan">
              <MapPinned size={14} />
              <p className="text-[10px] font-black uppercase tracking-[0.2em]">Nguồn hiển thị</p>
            </div>
            <h2 className="text-lg font-black text-white">{state?.sourceTitle ?? "Memory case backend"}</h2>
            <p className="max-w-3xl text-[13px] leading-relaxed text-slate-300">
              {state?.sourceSubtitle ?? "Trang này lấy dữ liệu từ API /memory-cases. Nếu bạn mở từ graph, phần state chỉ dùng để truyền ngữ cảnh nguồn."}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {state?.sourceGraphType ? (
              <Badge className="bg-white/10 text-slate-200 border-white/10 text-[9px] px-2 py-0.5 font-bold uppercase">
                {state.sourceGraphType}
              </Badge>
            ) : null}
            {state?.sourceGraphStatus ? (
              <Badge className="bg-white/10 text-slate-200 border-white/10 text-[9px] px-2 py-0.5 font-bold uppercase">
                {state.sourceGraphStatus}
              </Badge>
            ) : null}
            <Badge className="bg-white/10 text-slate-200 border-white/10 text-[9px] px-2 py-0.5 font-bold uppercase">
              {displayedCount} cases
            </Badge>
          </div>
        </div>

        {state?.sourceGraphSummary ? (
          <div className="mt-5 rounded-3xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center gap-2 text-mekong-cyan">
              <Clock3 size={14} />
              <p className="text-[10px] font-black uppercase tracking-[0.2em]">Tóm tắt nguồn</p>
            </div>
            <p className="mt-2 text-[13px] leading-relaxed text-slate-100">{state.sourceGraphSummary}</p>
          </div>
        ) : null}

        <div className="mt-5 flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-60">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input
              type="text"
              readOnly
              value="API list only"
              aria-label="Memory case search placeholder"
              placeholder="Danh sách memory case từ backend API"
              className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 pl-11 text-[12px] font-semibold text-slate-300 outline-none"
            />
          </div>
          <Button variant="outline" className="h-11 border-white/10 bg-white/5 px-4 text-[10px] font-black uppercase tracking-[0.14em] text-white">
            <span>{loading ? "Đang tải..." : "Đã đồng bộ"}</span>
          </Button>
        </div>
      </Card>

      {error ? <InlineError title="Không tải được memory case" message={error} /> : null}

      {loading && displayedCount === 0 ? <SkeletonCards count={2} /> : null}

      {!loading && displayedCount === 0 ? (
        <EmptyState
          title="Chưa có memory case"
          description="Backend chưa trả về memory case nào cho truy vấn hiện tại. Khi có execution feedback hoặc retrieval trace, danh sách sẽ xuất hiện ở đây."
        />
      ) : null}

      {displayedCount > 0 ? (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {memoryCases.map((citation, index) => (
            <Card key={`${citation.memory_case_id ?? index}-${index}`} variant="white" className="rounded-4xl border border-slate-100 p-5 shadow-soft">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 space-y-1">
                  <div className="flex items-center gap-2 text-mekong-cyan">
                    <FileText size={14} />
                    <p className="text-[9px] font-black uppercase tracking-[0.2em]">Memory case #{String(citation.rank ?? index + 1)}</p>
                  </div>
                  <h3 className="text-sm font-black uppercase tracking-[0.08em] text-mekong-navy line-clamp-2">
                    {formatMemoryCaseTitle(citation)}
                  </h3>
                </div>
                {citation.score !== undefined ? (
                  <Badge variant="optimal" className="text-[8px] px-2 py-0.5 font-bold uppercase">
                    {formatCitationScore(citation.score)}
                  </Badge>
                ) : null}
              </div>

              <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                  <p className="text-[9px] font-black uppercase tracking-[0.16em] text-slate-400">memory_case_id</p>
                  <p className="mt-1 text-sm font-semibold text-slate-700">{formatShortId(citation.memory_case_id)}</p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                  <p className="text-[9px] font-black uppercase tracking-[0.16em] text-slate-400">occurred_at</p>
                  <p className="mt-1 text-sm font-semibold text-slate-700">{formatDatetime(citation.occurred_at)}</p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                  <p className="text-[9px] font-black uppercase tracking-[0.16em] text-slate-400">incident_id</p>
                  <p className="mt-1 text-sm font-semibold text-slate-700">{formatShortId(citation.incident_id)}</p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                  <p className="text-[9px] font-black uppercase tracking-[0.16em] text-slate-400">plan_id</p>
                  <p className="mt-1 text-sm font-semibold text-slate-700">{formatShortId(citation.plan_id)}</p>
                </div>
              </div>

              {citation.citation ? (
                <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-[13px] leading-relaxed text-slate-700">
                  {citation.citation}
                </div>
              ) : null}

              {citation.source_uri ? (
                <div className="mt-4 flex flex-wrap items-center gap-2 text-[11px] font-semibold text-slate-500">
                  <LinkIcon size={13} />
                  <span className="break-all">{citation.source_uri}</span>
                </div>
              ) : null}

              {isApiMemoryCase(citation) ? (
                <div className="mt-4 rounded-2xl border border-slate-100 bg-slate-50/80 p-4 space-y-2">
                  <p className="text-[9px] font-black uppercase tracking-[0.16em] text-slate-400">API summary</p>
                  <p className="text-sm font-semibold leading-relaxed text-slate-700">{citation.summary}</p>
                  <p className="text-[11px] font-semibold text-slate-500">
                    Outcome: {citation.outcome_class}
                    {citation.severity ? ` · Severity: ${citation.severity}` : ""}
                  </p>
                  {citation.keywords && citation.keywords.length > 0 ? (
                    <div className="flex flex-wrap gap-2 pt-1">
                      {citation.keywords.slice(0, 5).map((keyword) => (
                        <Badge key={keyword} variant="neutral" className="text-[8px] uppercase">
                          {keyword}
                        </Badge>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : null}
            </Card>
          ))}
        </div>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to="/strategy"
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-[#00203F] px-4 py-2 text-[10px] font-black uppercase tracking-[0.14em] text-white transition-colors hover:border-mekong-cyan/40 hover:text-mekong-cyan"
        >
          <ArrowLeft size={14} />
          Quay lại điều phối
        </Link>
        <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-slate-500">
          Memory case list được lấy từ API backend
        </p>
      </div>
    </div>
  );
}