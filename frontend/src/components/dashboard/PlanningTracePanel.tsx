import { useMemo, useState } from "react";

import { AlertTriangle, ChevronDown, ChevronUp, ShieldCheck } from "lucide-react";

import { PlanningTraceDetails } from "./PlanningTrace";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { type AgentRunRead } from "../../lib/api/strategy";
import { formatTime } from "../../lib/format";

type StreamStatus = "connecting" | "connected" | "disconnected";

interface PlanningTracePanelProps {
  agentRun: AgentRunRead | null;
  streamStatus: StreamStatus;
  lastStreamAt: string | null;
  executionGraph?: import("../../lib/api/graph").ExecutionGraphRead | null;
}

export function PlanningTracePanel({ agentRun, streamStatus, lastStreamAt, executionGraph }: PlanningTracePanelProps) {
  const [showDetails, setShowDetails] = useState(false);

  const decisionTone = useMemo(() => {
    if (!agentRun) {
      return "neutral";
    }
    if (agentRun.status === "failed") {
      return "critical";
    }
    if (agentRun.status === "succeeded" || agentRun.status === "completed") {
      return "optimal";
    }
    return "warning";
  }, [agentRun]);

  const summaryText = useMemo(() => {
    if (!agentRun) {
      return "Chưa có planning run hợp lệ để hiển thị trace chi tiết.";
    }
    if (agentRun.error_message) {
      return `Run gần nhất đang có lỗi: ${agentRun.error_message}`;
    }
    if (agentRun.status === "failed") {
      return "Run gần nhất thất bại, nên đọc summary trước khi mở trace.";
    }
    return "Run hiện tại sẵn sàng cho operator mở trace chi tiết khi cần.";
  }, [agentRun]);

  return (
    <Card variant="navy" className="h-full p-8 rounded-4xl border border-white/5">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="space-y-2 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <p className="text-lg font-black text-white">Planning Trace</p>
            <Badge variant={decisionTone as "critical" | "warning" | "optimal" | "neutral"} className="text-[9px] py-0.5 px-2 font-bold">
              {agentRun?.status ?? "no run"}
            </Badge>
            <Badge className="bg-white/10 text-slate-200 border-white/10 text-[9px] py-0.5 px-2 font-bold">
              {streamStatus}
            </Badge>
          </div>
          <p className="text-sm leading-relaxed text-slate-300 max-w-3xl">{summaryText}</p>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
            Cập nhật lúc {formatTime(lastStreamAt)}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => setShowDetails((previous) => !previous)}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-[10px] font-black uppercase tracking-[0.16em] text-white transition-all hover:bg-white/10"
          >
            {showDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {showDetails ? "Ẩn trace" : "Mở trace chi tiết"}
          </button>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">Trạng thái</p>
          <p className="mt-2 text-sm font-black text-white">{agentRun?.status ?? "Chưa có run"}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">An toàn hiển thị</p>
          <p className="mt-2 text-sm font-black text-white">Có lớp bảo vệ</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">Khuyến nghị</p>
          <p className="mt-2 text-sm font-black text-white">Đọc summary trước</p>
        </div>
      </div>

      {showDetails ? (
        <div className="mt-5 rounded-3xl border border-white/10 bg-black/10 p-4 space-y-4">
          <div className="flex items-center gap-2 text-mekong-cyan">
            <ShieldCheck size={16} />
            <p className="text-[10px] font-black uppercase tracking-[0.2em]">Trace chi tiết</p>
          </div>
          <div className="rounded-2xl border border-amber-200/20 bg-amber-100/10 px-4 py-3 text-[12px] leading-relaxed text-amber-100">
            <AlertTriangle size={14} className="mb-1 inline-block mr-2 align-text-bottom" />
            Chỉ mở khi cần đọc sâu. Phần bên dưới vẫn tách riêng để không làm rối màn tổng quan.
          </div>
          <PlanningTraceDetails
            agentRun={agentRun}
            streamStatus={streamStatus}
            lastStreamAt={lastStreamAt}
            executionGraph={executionGraph}
          />
        </div>
      ) : null}
    </Card>
  );
}
