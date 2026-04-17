import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Compass,
  Cpu,
  Database,
  Droplets,
  ExternalLink,
  ListChecks,
  TrendingUp,
  Waves,
  Wind,
  Zap,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { AISentinel } from "../components/dashboard/AISentinel";
import { SatelliteMap, type MapStation } from "../components/dashboard/SatelliteMap";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { getApiBaseUrl } from "../lib/api/http";
import {
  getActionLogs,
  getDashboardSummary,
  getDashboardTimeline,
  getLatestReadings,
  getLatestRisk,
  type ActionLogEntry,
  type DashboardSummary,
  type RiskLatestResponse,
  type SensorReading,
} from "../lib/api/dashboard";
import { getStations, type SensorStationRead } from "../lib/api/telemetry";
import { ApiError, type ErrorResponse } from "../lib/api/types";

type StreamStatus = "connecting" | "connected" | "disconnected";

type DashboardState = {
  loading: boolean;
  error: string | null;
  summary: DashboardSummary | null;
  risk: RiskLatestResponse | null;
  latestReading: SensorReading | null;
  latestReadings: SensorReading[];
  stations: SensorStationRead[];
  recentActions: ActionLogEntry[];
  timelineCount: number;
  streamStatus: StreamStatus;
  lastStreamAt: string | null;
};

type DashboardSnapshot = Pick<
  DashboardState,
  | "summary"
  | "risk"
  | "latestReading"
  | "latestReadings"
  | "stations"
  | "recentActions"
  | "timelineCount"
>;

type DashboardStreamSummaryPayload = {
  cursor?: number;
  summary?: DashboardSummary;
};

type DashboardStreamDomainEventPayload = {
  cursor?: number;
};

const DASHBOARD_STREAM_CURSOR_KEY = "mekong.dashboard.stream.cursor";

function toNumber(value: unknown): number | null {
  if (value === null || value === undefined) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatNumber(value: number | null, digits = 2): string {
  if (value === null) {
    return "--";
  }
  return value.toFixed(digits);
}

function formatSigned(value: number | null, digits = 2): string {
  if (value === null) {
    return "--";
  }
  return `${value > 0 ? "+" : ""}${value.toFixed(digits)}`;
}

function formatActionType(value: string): string {
  return value
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
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

function parseApiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error && typeof error === "object") {
    const maybeError = error as ErrorResponse;
    if (typeof maybeError.message === "string") {
      return maybeError.message;
    }
  }
  return "Không tải được dữ liệu dashboard.";
}

async function fetchDashboardSnapshot(signal?: AbortSignal): Promise<DashboardSnapshot> {
  const [summary, timeline, risk, readings, actionLogs, stations] = await Promise.all([
    getDashboardSummary(signal),
    getDashboardTimeline(signal),
    getLatestRisk(undefined, signal).catch((error: unknown) => {
      if (error instanceof ApiError && error.statusCode === 404) {
        return null;
      }
      throw error;
    }),
    getLatestReadings({ limit: 50 }, signal),
    getActionLogs({ limit: 3 }, signal),
    getStations({ limit: 300 }, signal),
  ]);

  return {
    summary,
    risk,
    latestReading: risk?.reading ?? readings.items[0] ?? null,
    latestReadings: readings.items,
    stations: stations.items,
    recentActions: actionLogs.items,
    timelineCount: timeline.count,
  };
}

function parseSsePayload<T>(rawData: string): T | null {
  try {
    return JSON.parse(rawData) as T;
  } catch {
    return null;
  }
}

function resolveStreamCursor(lastEventId: string, fallbackCursor?: number): number | null {
  const parsedLastEventId = Number(lastEventId);
  if (Number.isFinite(parsedLastEventId) && parsedLastEventId > 0) {
    return parsedLastEventId;
  }
  if (fallbackCursor !== undefined && Number.isFinite(fallbackCursor) && fallbackCursor > 0) {
    return fallbackCursor;
  }
  return null;
}

function getStreamStatusText(status: StreamStatus): string {
  if (status === "connected") {
    return "Realtime ON";
  }
  if (status === "connecting") {
    return "Connecting";
  }
  return "Realtime OFF";
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

export function Dashboard() {
  const navigate = useNavigate();
  const [state, setState] = useState<DashboardState>({
    loading: true,
    error: null,
    summary: null,
    risk: null,
    latestReading: null,
    latestReadings: [],
    stations: [],
    recentActions: [],
    timelineCount: 0,
    streamStatus: "connecting",
    lastStreamAt: null,
  });

  useEffect(() => {
    const abortController = new AbortController();

    const loadDashboard = async () => {
      setState((previous) => ({ ...previous, loading: true, error: null }));
      try {
        const snapshot = await fetchDashboardSnapshot(abortController.signal);
        setState((previous) => ({
          ...previous,
          ...snapshot,
          loading: false,
          error: null,
        }));
      } catch (error) {
        if (abortController.signal.aborted) {
          return;
        }
        setState((previous) => ({
          ...previous,
          loading: false,
          error: parseApiErrorMessage(error),
        }));
      }
    };

    void loadDashboard();
    return () => abortController.abort();
  }, []);

  useEffect(() => {
    let stream: EventSource | null = null;
    let reconnectTimeoutId: number | null = null;
    let refreshTimeoutId: number | null = null;
    let isDisposed = false;

    const persistCursor = (cursor: number | null) => {
      if (cursor === null) {
        return;
      }
      window.localStorage.setItem(DASHBOARD_STREAM_CURSOR_KEY, String(cursor));
    };

    const scheduleRefresh = () => {
      if (refreshTimeoutId !== null) {
        return;
      }
      refreshTimeoutId = window.setTimeout(() => {
        refreshTimeoutId = null;
        void fetchDashboardSnapshot()
          .then((snapshot) => {
            if (isDisposed) {
              return;
            }
            setState((previous) => ({
              ...previous,
              ...snapshot,
              error: null,
            }));
          })
          .catch((error: unknown) => {
            if (isDisposed) {
              return;
            }
            setState((previous) => ({
              ...previous,
              error: parseApiErrorMessage(error),
            }));
          });
      }, 700);
    };

    const connect = () => {
      if (isDisposed) {
        return;
      }

      const streamUrl = new URL(`${getApiBaseUrl()}/dashboard/stream`);
      const cursorText = window.localStorage.getItem(DASHBOARD_STREAM_CURSOR_KEY);
      const cursor = Number(cursorText ?? "0");
      if (Number.isFinite(cursor) && cursor > 0) {
        streamUrl.searchParams.set("cursor", String(cursor));
      }

      setState((previous) => ({ ...previous, streamStatus: "connecting" }));
      stream = new EventSource(streamUrl.toString());

      stream.addEventListener("open", () => {
        if (isDisposed) {
          return;
        }
        setState((previous) => ({ ...previous, streamStatus: "connected" }));
      });

      stream.addEventListener("summary", (event) => {
        if (isDisposed || !(event instanceof MessageEvent)) {
          return;
        }
        const payload = parseSsePayload<DashboardStreamSummaryPayload>(
          typeof event.data === "string" ? event.data : "",
        );
        const cursorFromEvent = resolveStreamCursor(event.lastEventId, payload?.cursor);
        persistCursor(cursorFromEvent);

        setState((previous) => ({
          ...previous,
          streamStatus: "connected",
          lastStreamAt: new Date().toISOString(),
          summary: payload?.summary ?? previous.summary,
        }));

        if (!payload?.summary) {
          scheduleRefresh();
        }
      });

      stream.addEventListener("domain_event", (event) => {
        if (isDisposed || !(event instanceof MessageEvent)) {
          return;
        }
        const payload = parseSsePayload<DashboardStreamDomainEventPayload>(
          typeof event.data === "string" ? event.data : "",
        );
        const cursorFromEvent = resolveStreamCursor(event.lastEventId, payload?.cursor);
        persistCursor(cursorFromEvent);

        setState((previous) => ({
          ...previous,
          streamStatus: "connected",
          lastStreamAt: new Date().toISOString(),
        }));
        scheduleRefresh();
      });

      stream.addEventListener("error", () => {
        if (isDisposed) {
          return;
        }
        setState((previous) => ({ ...previous, streamStatus: "disconnected" }));
        stream?.close();
        if (reconnectTimeoutId === null) {
          reconnectTimeoutId = window.setTimeout(() => {
            reconnectTimeoutId = null;
            connect();
          }, 2500);
        }
      });
    };

    connect();

    return () => {
      isDisposed = true;
      stream?.close();
      if (reconnectTimeoutId !== null) {
        window.clearTimeout(reconnectTimeoutId);
      }
      if (refreshTimeoutId !== null) {
        window.clearTimeout(refreshTimeoutId);
      }
    };
  }, []);

  const salinityGl = toNumber(
    state.risk?.assessment.salinity_gl ?? state.latestReading?.salinity_gl,
  );
  const waterLevel = toNumber(state.latestReading?.water_level_m);
  const windSpeed = toNumber(state.latestReading?.wind_speed_mps);
  const windDirection = state.latestReading?.wind_direction_deg;
  const trendDeltaGl = toNumber(state.risk?.assessment.trend_delta_gl);
  const stationCode =
    state.latestReading?.station.code ??
    state.summary?.latest_station_code ??
    "--";
  const mapStations = useMemo<MapStation[]>(() => {
    const readingsByStationId = new Map(
      state.latestReadings.map((reading) => [reading.station_id, reading] as const),
    );

    const mappedStations: Array<MapStation | null> = state.stations.map((station) => {
        const latitude = toNumber(station.latitude);
        const longitude = toNumber(station.longitude);
        if (latitude === null || longitude === null) {
          return null;
        }

        const reading = readingsByStationId.get(station.id);
        return {
          id: station.id,
          code: station.code,
          name: station.name,
          latitude,
          longitude,
          status: station.status,
          latestSalinityGl:
            reading?.salinity_gl !== null && reading?.salinity_gl !== undefined
              ? Number(reading.salinity_gl)
              : null,
          riskLevel:
            state.risk?.assessment.station_id === station.id
              ? state.risk.assessment.risk_level
              : null,
        };
      });

    return mappedStations.filter((station): station is MapStation => station !== null);
  }, [state.latestReadings, state.stations, state.risk]);

  const trendText = useMemo(() => {
    const trend = state.risk?.assessment.trend_direction;
    if (trend === "rising") {
      return "Độ mặn đang tăng";
    }
    if (trend === "falling") {
      return "Độ mặn đang giảm";
    }
    if (trend === "stable") {
      return "Độ mặn ổn định";
    }
    return "Chưa đủ dữ liệu xu hướng";
  }, [state.risk?.assessment.trend_direction]);

  const riskLevelLabel = useMemo(() => {
    const level = state.risk?.assessment.risk_level;
    if (level) {
      return `Risk: ${level}`;
    }
    return "Risk: unknown";
  }, [state.risk?.assessment.risk_level]);

  const streamBadgeText = getStreamStatusText(state.streamStatus);
  const streamBadgeClass = getStreamStatusClass(state.streamStatus);

  const fallbackActions: ActionLogEntry[] = useMemo(
    () => [
      {
        execution: {
          id: "placeholder-1",
          created_at: "",
          updated_at: "",
          action_type: "no_data",
          status: "pending",
          step_index: 0,
          started_at: null,
          completed_at: null,
          result_summary: "Chưa có action log gần đây.",
        },
        decision_log: null,
      },
    ],
    [],
  );

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {state.error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-3 text-sm font-bold text-red-700">
          {state.error}
        </div>
      ) : null}

      <section className="relative overflow-hidden bg-[#00203F] rounded-[32px] p-7 lg:p-9 text-white shadow-2xl border border-white/10">
        <div className="absolute top-0 right-0 w-[500px] h-full bg-mekong-cyan/[0.03] rounded-full blur-[120px] pointer-events-none" />
        <div className="relative z-10 flex flex-col lg:flex-row items-center justify-between gap-8">
          <div className="flex items-center gap-6 flex-1 min-w-0">
            <div className="relative flex-shrink-0">
              <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center text-mekong-cyan border border-white/10 shadow-inner">
                <Activity size={28} strokeWidth={2.5} />
              </div>
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-mekong-mint rounded-full border-2 border-[#00203F] animate-pulse" />
            </div>
            <div className="space-y-2 truncate">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] opacity-80 leading-none">
                Dashboard Realtime
              </p>
              <div className="flex items-center gap-3 flex-wrap">
                <h2 className="text-xl lg:text-2xl font-black tracking-tight whitespace-nowrap">
                  Mục tiêu độ mặn sầu riêng &lt; 0.5 g/L
                </h2>
                <Badge className="bg-mekong-mint/10 text-mekong-mint border-mekong-mint/20 text-[9px] py-0.5 px-2 italic font-bold">
                  {state.loading ? "Đang tải..." : riskLevelLabel}
                </Badge>
                <Badge className={`${streamBadgeClass} text-[9px] py-0.5 px-2 font-bold`}>
                  {streamBadgeText}
                </Badge>
              </div>
            </div>
          </div>
          <div className="flex flex-col items-center lg:items-end lg:px-12 border-l border-white/5">
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-1">
              Biến thiên hiện tại
            </p>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-black text-mekong-cyan tracking-tighter">
                {formatSigned(trendDeltaGl, 2)}
              </span>
              <span className="text-[11px] font-black text-slate-400 uppercase tracking-widest">g/L</span>
            </div>
            <p className="text-[10px] font-bold text-slate-400 mt-2">
              Last event: {formatTime(state.lastStreamAt)}
            </p>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-12 gap-8">
        <Card isHoverable className="col-span-12 lg:col-span-4 p-8 border-none shadow-soft group relative overflow-hidden bg-white min-h-[280px] flex flex-col justify-between">
          <div className="relative z-10 flex justify-between items-start">
            <div className="flex items-center gap-4">
              <div className="bg-mekong-teal/10 p-3 rounded-2xl text-mekong-teal border border-mekong-teal/20 shadow-sm">
                <Droplets size={24} strokeWidth={2.5} />
              </div>
              <div className="space-y-0.5">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] leading-none">Độ mặn trực tiếp</p>
                <Badge variant="optimal" className="bg-mekong-mint/10 text-mekong-mint border-none px-2 py-0.5 text-[9px] font-bold">
                  {stationCode}
                </Badge>
              </div>
            </div>
          </div>
          <div className="relative z-10 flex items-baseline gap-3">
            <span className="text-7xl font-black text-mekong-navy tracking-tighter leading-none">
              {formatNumber(salinityGl, 2)}
            </span>
            <span className="text-xl font-black text-slate-400 uppercase tracking-widest">g/L</span>
          </div>
          <div className="relative z-10 pt-6 border-t border-slate-50 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Activity size={14} className="text-mekong-teal" />
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">{trendText}</span>
            </div>
          </div>
        </Card>

        <Card isHoverable className="col-span-12 lg:col-span-4 p-8 border-none shadow-soft group bg-white min-h-[280px] flex flex-col justify-between border-t-4 border-t-mekong-critical/20">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-4">
              <div className="bg-slate-100 p-3 rounded-2xl text-mekong-navy border border-slate-200 shadow-sm">
                <Waves size={24} strokeWidth={2.5} />
              </div>
              <div className="space-y-0.5">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] leading-none">Mực nước thủy triều</p>
                <Badge className="bg-slate-100 text-slate-500 border-none px-2 py-0.5 text-[9px] font-bold">{stationCode}</Badge>
              </div>
            </div>
          </div>
          <div className="flex items-baseline gap-3">
            <span className="text-7xl font-black text-mekong-navy tracking-tighter leading-none">{formatNumber(waterLevel, 2)}</span>
            <span className="text-xl font-black text-slate-400 uppercase tracking-widest">m</span>
          </div>
          <div className="pt-6 border-t border-slate-50">
            <div className="flex items-center gap-2.5 px-3 py-2 bg-red-50 rounded-2xl border border-red-100/50 text-mekong-critical shadow-sm">
              <TrendingUp size={16} strokeWidth={3} />
              <div className="flex flex-col">
                <span className="text-[11px] font-black uppercase tracking-widest leading-none">
                  Dữ liệu mới nhất
                </span>
                <span className="text-[9px] font-bold opacity-70">{state.latestReading ? formatTime(state.latestReading.recorded_at) : "--:--"}</span>
              </div>
            </div>
          </div>
        </Card>

        <Card isHoverable className="col-span-12 lg:col-span-4 p-8 border-none shadow-soft group bg-white min-h-[280px] flex flex-col justify-between relative overflow-hidden">
          <div className="relative z-10 flex justify-between items-start">
            <div className="flex items-center gap-4">
              <div className="bg-slate-100 p-3 rounded-2xl text-mekong-navy border border-slate-200 shadow-sm">
                <Wind size={24} strokeWidth={2.5} />
              </div>
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] leading-none">Gió và tốc độ</p>
            </div>
          </div>
          <div className="relative z-10 flex items-center gap-10">
            <div className="flex items-baseline gap-2">
              <span className="text-7xl font-black text-mekong-navy tracking-tighter leading-none">{formatNumber(windSpeed, 1)}</span>
              <span className="text-sm font-black text-slate-400 uppercase">m/s</span>
            </div>
            <div className="h-14 w-px bg-slate-100" />
            <div className="flex flex-col">
              <span className="text-4xl font-black text-mekong-navy tracking-tighter">
                {windDirection === null || windDirection === undefined ? "--" : `${windDirection}°`}
              </span>
              <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Hướng gió</span>
            </div>
          </div>
          <div className="relative z-10 pt-6 border-t border-slate-50 flex items-center gap-2">
            <Compass size={14} strokeWidth={2.5} className="text-slate-400" />
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-widest leading-none">
              Từ cảm biến gần nhất
            </span>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-12 gap-8 items-start">
        <div className="col-span-12 lg:col-span-8">
          <Card padding="none" className="h-[520px] relative overflow-hidden rounded-[40px] shadow-soft border-none">
            <div className="absolute top-8 left-8 z-10 bg-white/90 backdrop-blur-xl p-6 rounded-[28px] shadow-2xl border border-white/50 ring-1 ring-black/5">
              <h3 className="text-lg font-black text-mekong-navy tracking-tighter leading-none mb-1">Bản đồ điểm nóng XNM</h3>
              <p className="text-[10px] font-black text-mekong-slate uppercase tracking-[0.15em]">
                Mốc dòng thời gian: {state.timelineCount}
              </p>
            </div>
            <div className="w-full h-full">
              <SatelliteMap
                zoom={12}
                showControls={false}
                stations={mapStations}
                selectedStationId={state.latestReading?.station_id ?? null}
              />
            </div>
            <button
              className="absolute bottom-8 left-8 z-10 bg-mekong-navy text-white px-6 py-3 rounded-xl font-black text-xs flex items-center gap-2 shadow-2xl hover:bg-mekong-teal transition-all"
              onClick={() => navigate("/map")}
            >
              Mở bản đồ toàn cảnh <ExternalLink size={16} />
            </button>
          </Card>
        </div>
        <div className="col-span-12 lg:col-span-4 space-y-8">
          <AISentinel />
        </div>
      </div>

      <div className="grid grid-cols-12 gap-8 items-stretch">
        <Card variant="white" className="col-span-12 lg:col-span-8 p-8 border-none shadow-soft flex flex-col rounded-[32px]">
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-mekong-navy rounded-xl text-mekong-cyan shadow-md">
                <Zap size={20} fill="currentColor" />
              </div>
              <h3 className="text-lg font-black text-mekong-navy uppercase tracking-tighter leading-none">Hành động tự trị gần đây</h3>
            </div>
            <button
              className="text-[10px] font-black text-mekong-teal uppercase tracking-widest flex items-center gap-1.5 hover:text-mekong-navy border-b border-mekong-teal/20 pb-0.5 transition-colors"
              onClick={() => navigate("/logs")}
            >
              Xem toàn bộ nhật ký <ArrowUpRight size={12} />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {(state.recentActions.length > 0 ? state.recentActions : fallbackActions).map((action) => (
              <div
                key={action.execution.id}
                className="flex flex-col justify-between gap-6 p-8 rounded-[32px] bg-slate-50/50 border-l-[8px] border-mekong-navy group hover:bg-white hover:shadow-2xl transition-all"
              >
                <div className="flex justify-between items-center relative z-10">
                  <span className="text-[12px] font-black text-slate-400 uppercase tracking-[0.2em]">
                    {formatTime(action.execution.started_at ?? action.execution.created_at)}
                  </span>
                  <Badge className="bg-slate-100 text-slate-600 border-none text-[9px] px-2 py-0.5 uppercase">
                    {action.execution.status}
                  </Badge>
                </div>
                <div className="space-y-3 relative z-10">
                  <h4 className="text-[17px] font-black text-mekong-navy group-hover:text-mekong-teal leading-none uppercase tracking-tight">
                    {formatActionType(action.execution.action_type)}
                  </h4>
                  <p className="text-[13px] text-slate-500 font-semibold leading-relaxed opacity-90">
                    {action.execution.result_summary ?? action.decision_log?.summary ?? "Không có mô tả kết quả."}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card variant="white" className="col-span-12 lg:col-span-4 p-8 border-none shadow-soft rounded-[32px] flex flex-col">
          <div className="flex items-center gap-3 mb-6 border-b border-slate-50 pb-4">
            <ListChecks size={20} className="text-mekong-navy" />
            <h3 className="text-xs font-black text-mekong-navy uppercase tracking-[0.15em]">Trạng thái vận hành</h3>
          </div>
          <div className="flex-1 flex flex-col justify-center space-y-5">
            {[
              { icon: Activity, label: "Sự cố đang mở", value: state.summary?.open_incidents ?? 0, color: "text-mekong-critical" },
              { icon: Database, label: "Chờ phê duyệt", value: state.summary?.pending_approvals ?? 0, color: "text-mekong-navy" },
              { icon: Cpu, label: "Mô phỏng hôm nay", value: state.summary?.simulated_executions_today ?? 0, color: "text-mekong-mint" },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between group cursor-default">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-slate-50 rounded-lg text-slate-400 group-hover:text-mekong-teal transition-all">
                    <item.icon size={27} strokeWidth={2.5} />
                  </div>
                  <span className="text-[12px] font-bold text-slate-500">{item.label}</span>
                </div>
                <span className={`text-[13px] font-black ${item.color} tracking-tighter`}>{item.value}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

export default Dashboard;
