import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Compass,
  Cpu,
  ChevronRight,
  Database,
  Droplets,
  ExternalLink,
  TrendingUp,
  Waves,
  Wind,
  Zap,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { SatelliteMap, type MapGate, type MapStation } from "../components/dashboard/SatelliteMap";
import { EmptyState, InlineError, SkeletonCards } from "../components/ui/AsyncState";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { PageHeading } from "../components/ui/PageHeading";
import { getApiBaseUrl } from "../lib/api/http";
import {
  getActionLogs,
  getDashboardSummary,
  getDashboardTimeline,
  getLatestReadings,
  getLatestRisk,
  type ActionLogEntry,
  type DashboardSummary,
  fetchOpenMeteoWeatherSnapshot,
  type RiskLatestResponse,
  type SensorReading,
  type OpenMeteoWeatherSnapshot,
} from "../lib/api/dashboard";
import { getGates, getStations, type GateRead, type SensorStationRead } from "../lib/api/telemetry";
import {
  decidePlan,
  getAgentRuns,
  getPlans,
  type ActionPlanRead,
  type AgentRunRead,
} from "../lib/api/strategy";
import { simulateExecutionBatch } from "../lib/api/operations";
import { ApiError, type ErrorResponse } from "../lib/api/types";

type StreamStatus = "connecting" | "connected" | "disconnected";

type LiveActivityKind = "reading" | "risk" | "action" | "agent" | "stream";
type LiveActivityFilter = LiveActivityKind | "all";

type LiveActivityEntry = {
  id: string;
  time: string;
  kind: LiveActivityKind;
  title: string;
  detail: string;
  badge: string;
};

type DashboardState = {
  loading: boolean;
  error: string | null;
  summary: DashboardSummary | null;
  risk: RiskLatestResponse | null;
  latestReading: SensorReading | null;
  latestReadings: SensorReading[];
  stations: SensorStationRead[];
  gates: GateRead[];
  plans: ActionPlanRead[];
  recentActions: ActionLogEntry[];
  agentRuns: AgentRunRead[];
  liveEvents: LiveActivityEntry[];
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
  | "gates"
  | "plans"
  | "recentActions"
  | "agentRuns"
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

type PlanningTrace = {
  incident_decision?: {
    decision?: string;
    reason?: string;
  };
  plan_decision?: {
    decision?: string;
    reason?: string;
    action_plan_id?: string;
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
  planning_transition_log?: Array<{
    node?: string;
    status?: string;
  }>;
};

function formatCompactId(value: string | null | undefined): string {
  if (!value) {
    return "--";
  }
  return value.length > 10 ? `${value.slice(0, 6)}…${value.slice(-4)}` : value;
}

function getPlanningTrace(run: AgentRunRead | null): PlanningTrace | null {
  if (!run || typeof run.trace !== "object" || run.trace === null || Array.isArray(run.trace)) {
    return null;
  }
  return run.trace as PlanningTrace;
}

function getRunObjective(run: AgentRunRead | null): string | null {
  if (!run || typeof run.payload !== "object" || run.payload === null || Array.isArray(run.payload)) {
    return null;
  }
  const request = (run.payload as Record<string, unknown>).request;
  if (!request || typeof request !== "object" || Array.isArray(request)) {
    return null;
  }
  const objective = (request as Record<string, unknown>).objective;
  return typeof objective === "string" ? objective : null;
}

function getLatestPlanningRun(runs: AgentRunRead[]): AgentRunRead | null {
  return (
    runs.find((run) => run.run_type === "plan_generation" && run.trace) ??
    runs.find((run) => run.trace) ??
    runs[0] ??
    null
  );
}

function getActivityBadgeClass(kind: LiveActivityKind): string {
  if (kind === "reading") {
    return "bg-mekong-cyan/10 text-mekong-teal border-mekong-cyan/20";
  }
  if (kind === "risk") {
    return "bg-red-50 text-mekong-critical border-red-100";
  }
  if (kind === "action") {
    return "bg-slate-100 text-mekong-navy border-slate-200";
  }
  if (kind === "agent") {
    return "bg-mekong-mint/10 text-mekong-mint border-mekong-mint/20";
  }
  return "bg-slate-100 text-mekong-slate border-slate-200";
}

function getActivityLabel(kind: LiveActivityKind): string {
  if (kind === "reading") {
    return "sensor";
  }
  if (kind === "risk") {
    return "risk";
  }
  if (kind === "action") {
    return "action";
  }
  if (kind === "agent") {
    return "trace";
  }
  return "stream";
}

function getFilterLabel(filter: LiveActivityFilter): string {
  if (filter === "all") {
    return "Tất cả";
  }
  if (filter === "reading") {
    return "Sensor";
  }
  if (filter === "risk") {
    return "Risk";
  }
  if (filter === "action") {
    return "Action";
  }
  if (filter === "agent") {
    return "Trace";
  }
  return "Stream";
}

function buildStreamPulseEvent(cursor: number | null): LiveActivityEntry {
  return {
    id: `stream-${cursor ?? Date.now()}`,
    time: new Date().toISOString(),
    kind: "stream",
    title: "Backend stream đã phát tín hiệu",
    detail:
      cursor !== null
        ? `Cursor ${cursor} đã được ghi nhận, đang đồng bộ dữ liệu liên quan.`
        : "Backend vừa phát một domain event mới.",
    badge: getActivityLabel("stream"),
  };
}

function buildReadingEvent(reading: SensorReading): LiveActivityEntry {
  return {
    id: `reading-${reading.id}`,
    time: reading.recorded_at,
    kind: "reading",
    title: `Cảm biến ${reading.station.code}`,
    detail: `${formatNumber(toNumber(reading.salinity_gl), 2)} g/L · ${formatNumber(
      toNumber(reading.water_level_m),
      2,
    )} m`,
    badge: getActivityLabel("reading"),
  };
}

function buildRiskEvent(risk: RiskLatestResponse): LiveActivityEntry {
  return {
    id: `risk-${risk.assessment.id}`,
    time: risk.assessment.assessed_at,
    kind: "risk",
    title: `Rủi ro ${risk.assessment.risk_level}`,
    detail: risk.assessment.summary,
    badge: getActivityLabel("risk"),
  };
}

function buildActionEvent(action: ActionLogEntry): LiveActivityEntry {
  return {
    id: `action-${action.execution.id}`,
    time: action.execution.completed_at ?? action.execution.started_at ?? action.execution.created_at,
    kind: "action",
    title: formatActionType(action.execution.action_type),
    detail: action.execution.result_summary ?? action.decision_log?.summary ?? "Chưa có mô tả kết quả.",
    badge: getActivityLabel("action"),
  };
}

function buildAgentEvent(run: AgentRunRead): LiveActivityEntry {
  const trace = getPlanningTrace(run);
  const transitionCount = trace?.planning_transition_log?.length ?? 0;
  const planReason = trace?.plan_decision?.reason ?? trace?.incident_decision?.reason ?? null;
  const objective = getRunObjective(run);

  return {
    id: `agent-${run.id}`,
    time: run.finished_at ?? run.started_at,
    kind: "agent",
    title: `Agent trace · ${run.status}`,
    detail:
      objective !== null
        ? `Mục tiêu: ${objective}${planReason ? ` • ${planReason}` : ""}`
        : planReason ?? `${transitionCount} node đã hoàn tất`,
    badge: getActivityLabel("agent"),
  };
}

function sortLiveEvents(entries: LiveActivityEntry[]): LiveActivityEntry[] {
  return [...entries].sort((left, right) => {
    const leftTime = new Date(left.time).getTime();
    const rightTime = new Date(right.time).getTime();
    return rightTime - leftTime;
  });
}

function buildSeedLiveEvents(snapshot: DashboardSnapshot): LiveActivityEntry[] {
  const entries: LiveActivityEntry[] = [];
  const latestAgentRun = getLatestPlanningRun(snapshot.agentRuns);

  if (latestAgentRun !== null) {
    entries.push(buildAgentEvent(latestAgentRun));
  }
  if (snapshot.recentActions[0] !== undefined) {
    entries.push(buildActionEvent(snapshot.recentActions[0]));
  }
  if (snapshot.risk !== null) {
    entries.push(buildRiskEvent(snapshot.risk));
  }
  if (snapshot.latestReading !== null) {
    entries.push(buildReadingEvent(snapshot.latestReading));
  }

  return sortLiveEvents(entries).slice(0, 8);
}

function collectDeltaLiveEvents(previous: DashboardState, next: DashboardSnapshot): LiveActivityEntry[] {
  const entries: LiveActivityEntry[] = [];

  if (previous.latestReading?.id !== next.latestReading?.id && next.latestReading !== null) {
    entries.push(buildReadingEvent(next.latestReading));
  }
  if (previous.risk?.assessment.id !== next.risk?.assessment.id && next.risk !== null) {
    entries.push(buildRiskEvent(next.risk));
  }
  if (
    previous.recentActions[0]?.execution.id !== next.recentActions[0]?.execution.id &&
    next.recentActions[0] !== undefined
  ) {
    entries.push(buildActionEvent(next.recentActions[0]));
  }

  const previousAgentRun = getLatestPlanningRun(previous.agentRuns);
  const nextAgentRun = getLatestPlanningRun(next.agentRuns);
  if (previousAgentRun?.id !== nextAgentRun?.id && nextAgentRun !== null) {
    entries.push(buildAgentEvent(nextAgentRun));
  }

  return sortLiveEvents(entries).slice(0, 8);
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
  const [summaryResult, timelineResult, riskResult, readingsResult, actionLogsResult, stationsResult, gatesResult, plansResult, agentRunsResult] =
    await Promise.allSettled([
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
      getGates({ limit: 100 }, signal),
      getPlans({ limit: 50 }, signal),
      getAgentRuns({ limit: 8 }, signal),
    ]);

  const summary = summaryResult.status === "fulfilled" ? summaryResult.value : {
    open_incidents: 0,
    pending_approvals: 0,
    active_notifications: 0,
    latest_risk_level: null,
    latest_salinity_dsm: null,
    latest_salinity_gl: null,
    latest_station_code: null,
    simulated_executions_today: 0,
  };
  const timeline = timelineResult.status === "fulfilled" ? timelineResult.value : { items: [], count: 0 };
  const risk = riskResult.status === "fulfilled" ? riskResult.value : null;
  const readings = readingsResult.status === "fulfilled" ? readingsResult.value : { items: [], count: 0 };
  const actionLogs = actionLogsResult.status === "fulfilled" ? actionLogsResult.value : { items: [], count: 0 };
  const stations = stationsResult.status === "fulfilled" ? stationsResult.value : { items: [], count: 0 };
  const gates = gatesResult.status === "fulfilled" ? gatesResult.value : { items: [], count: 0 };
  const plans = plansResult.status === "fulfilled" ? plansResult.value : [];
  const agentRuns = agentRunsResult.status === "fulfilled" ? agentRunsResult.value : { items: [], count: 0 };

  return {
    summary,
    risk,
    latestReading: risk?.reading ?? readings.items[0] ?? null,
    latestReadings: readings.items,
    stations: stations.items,
    gates: gates.items,
    plans,
    recentActions: actionLogs.items,
    agentRuns: agentRuns.items,
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
    return "Realtime bật";
  }
  if (status === "connecting") {
    return "Đang kết nối";
  }
  return "Realtime tắt";
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
  const [activityFilter, setActivityFilter] = useState<LiveActivityFilter>("all");
  const [reloadVersion, setReloadVersion] = useState(0);
  const [plcBusy, setPlcBusy] = useState(false);
  const [plcStatusMessage, setPlcStatusMessage] = useState<string | null>(null);
  const [weatherSnapshot, setWeatherSnapshot] = useState<OpenMeteoWeatherSnapshot | null>(null);
  const [state, setState] = useState<DashboardState>({
    loading: true,
    error: null,
    summary: null,
    risk: null,
    latestReading: null,
    latestReadings: [],
    stations: [],
    gates: [],
    plans: [],
    recentActions: [],
    agentRuns: [],
    liveEvents: [],
    timelineCount: 0,
    streamStatus: "connecting",
    lastStreamAt: null,
  });
  const weatherStationCode = state.latestReading?.station.code ?? state.summary?.latest_station_code ?? null;
  const weatherStation = useMemo(
    () => {
      if (!weatherStationCode) {
        return null;
      }
      return state.stations.find((station) => station.code === weatherStationCode) ?? null;
    },
    [state.stations, weatherStationCode],
  );

  useEffect(() => {
    if (!weatherStation) {
      setWeatherSnapshot(null);
      return;
    }

    const latitude = toNumber(weatherStation.latitude);
    const longitude = toNumber(weatherStation.longitude);
    if (latitude === null || longitude === null) {
      setWeatherSnapshot(null);
      return;
    }

    const abortController = new AbortController();

    void fetchOpenMeteoWeatherSnapshot({ latitude, longitude }, abortController.signal)
      .then((snapshot) => {
        if (abortController.signal.aborted) {
          return;
        }
        setWeatherSnapshot(snapshot);
      })
      .catch(() => {
        if (abortController.signal.aborted) {
          return;
        }
        setWeatherSnapshot(null);
      });

    return () => abortController.abort();
  }, [reloadVersion, weatherStation]);

  useEffect(() => {
    const abortController = new AbortController();

    const loadDashboard = async () => {
      setState((previous) => ({ ...previous, loading: true, error: null }));
      try {
        const snapshot = await fetchDashboardSnapshot(abortController.signal);
        setState((previous) => ({
          ...previous,
          ...snapshot,
          liveEvents: buildSeedLiveEvents(snapshot),
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
  }, [reloadVersion]);

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
              liveEvents: (() => {
                const deltaEvents = collectDeltaLiveEvents(previous, snapshot);
                return deltaEvents.length
                  ? [...deltaEvents, ...previous.liveEvents].slice(0, 8)
                  : previous.liveEvents;
              })(),
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
        setState((previous) => ({ ...previous, streamStatus: "connected", error: null }));
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
          error: null,
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
          liveEvents: [buildStreamPulseEvent(cursorFromEvent), ...previous.liveEvents].slice(0, 8),
          error: null,
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
  const activeWeatherSnapshot = weatherSnapshot;
  const waterLevel = toNumber(
    activeWeatherSnapshot?.tide_level_m ?? state.latestReading?.water_level_m,
  );
  const windSpeed = toNumber(
    activeWeatherSnapshot?.wind_speed_mps ?? state.latestReading?.wind_speed_mps,
  );
  const windDirection =
    activeWeatherSnapshot?.wind_direction_deg ?? state.latestReading?.wind_direction_deg;
  const weatherSourceLabel = activeWeatherSnapshot ? "Open-Meteo" : "Cảm biến";
  const weatherObservedAt = activeWeatherSnapshot?.observed_at ?? state.latestReading?.recorded_at ?? null;
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
          stationType: station.station_type,
          stationMetadata: station.station_metadata,
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

  const mapGates = useMemo<MapGate[]>(() => {
    return state.gates.flatMap((gate) => {
        const latitude = toNumber(gate.latitude);
        const longitude = toNumber(gate.longitude);
        if (latitude === null || longitude === null) {
            return [] as MapGate[];
        }

        return [
          {
          id: gate.id,
          code: gate.code,
          name: gate.name,
          latitude,
          longitude,
          gateType: gate.gate_type,
          status: gate.status,
          gateMetadata: gate.gate_metadata,
          locationDescription: gate.location_description,
          lastOperatedAt: gate.last_operated_at,
          station: gate.station,
          },
        ];
      });
  }, [state.gates]);

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
      const labels: Record<string, string> = {
        safe: "An toàn",
        warning: "Cảnh báo",
        danger: "Nguy cơ cao",
        critical: "Khẩn cấp",
      };
      return `Rủi ro: ${labels[level] ?? level}`;
    }
    return "Rủi ro: chưa rõ";
  }, [state.risk?.assessment.risk_level]);

  const latestPendingApprovalPlan = useMemo(
    () => state.plans.find((plan) => plan.status === "pending_approval") ?? null,
    [state.plans],
  );
  const latestApprovedPlan = useMemo(
    () => state.plans.find((plan) => plan.status === "approved") ?? null,
    [state.plans],
  );
  const controlPlan = latestPendingApprovalPlan ?? latestApprovedPlan;
  const controlPlanStatusText = controlPlan ? controlPlan.status.replace(/_/g, " ") : "không có plan";
  const visibleLiveEvents = useMemo(
    () =>
      activityFilter === "all"
        ? state.liveEvents
        : state.liveEvents.filter((event) => event.kind === activityFilter),
    [activityFilter, state.liveEvents],
  );
  const liveEventCounts = useMemo(
    () => ({
      all: state.liveEvents.length,
      reading: state.liveEvents.filter((event) => event.kind === "reading").length,
      risk: state.liveEvents.filter((event) => event.kind === "risk").length,
      action: state.liveEvents.filter((event) => event.kind === "action").length,
      agent: state.liveEvents.filter((event) => event.kind === "agent").length,
      stream: state.liveEvents.filter((event) => event.kind === "stream").length,
    }),
    [state.liveEvents],
  );

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
  const isBootstrapping = state.loading && state.summary === null && state.latestReading === null;

  const handlePlcDemo = async () => {
    if (!controlPlan) {
      setPlcStatusMessage("Không có plan pending/approved để mô phỏng PLC.");
      return;
    }

    setPlcBusy(true);
    setPlcStatusMessage(null);

    try {
      if (controlPlan.status === "pending_approval") {
        await decidePlan(
          controlPlan.id,
          {
            decision: "approved",
            comment: "Phê duyệt từ Dashboard để chạy mô phỏng PLC.",
          },
          { actorName: "dashboard-operator" },
        );
      }

      await simulateExecutionBatch(controlPlan.id, {
        idempotency_key: `dashboard-plc:${controlPlan.id}:${Date.now()}`,
      });

      setPlcStatusMessage(`Đã mô phỏng PLC cho plan ${formatCompactId(controlPlan.id)}.`);
      setReloadVersion((previous) => previous + 1);
    } catch (error) {
      const message = parseApiErrorMessage(error);
      setPlcStatusMessage(message);
      setState((previous) => ({ ...previous, error: message }));
    } finally {
      setPlcBusy(false);
    }
  };

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      <PageHeading
        trailing={
          state.lastStreamAt ? (
            <Badge variant="neutral" className="text-[9px]">
              Last stream {formatTime(state.lastStreamAt)}
            </Badge>
          ) : undefined
        }
      />

      {state.error ? (
        <InlineError
          title="Lỗi đồng bộ dashboard"
          message={state.error}
          onRetry={() => setReloadVersion((previous) => previous + 1)}
        />
      ) : null}

      {isBootstrapping ? (
        <>
          <SkeletonCards count={3} />
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="h-96 animate-pulse rounded-4xl bg-slate-200/70" />
            <div className="h-96 animate-pulse rounded-4xl bg-slate-200/70" />
          </div>
        </>
      ) : null}

      <section
        className={`relative overflow-hidden rounded-4xl border border-white/10 bg-linear-to-br from-[#00203F] via-[#002845] to-[#05304b] px-6 py-6 text-white shadow-2xl lg:px-8 lg:py-7 ${isBootstrapping ? "hidden" : ""}`}
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(117,231,254,0.15),transparent_34%),radial-gradient(circle_at_bottom_left,rgba(0,200,180,0.10),transparent_28%)] pointer-events-none" />
        <div className="relative z-10 grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px] lg:items-center">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2 text-[10px] font-black uppercase tracking-[0.24em] text-slate-300">
              <Activity size={13} className="text-mekong-cyan" />
              <span>Dashboard thời gian thực</span>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <h2 className="max-w-4xl text-[clamp(1.35rem,2vw,2.05rem)] font-black leading-[1.08] tracking-tight">
                Mục tiêu độ mặn sầu riêng &lt; 0.5 g/L
              </h2>
              <Badge className="border border-white/15 bg-white/10 px-2.5 py-1 text-[9px] font-bold text-white shadow-none">
                {state.loading ? "Đang tải..." : riskLevelLabel}
              </Badge>
              <Badge className={`border border-white/15 ${streamBadgeClass} px-2.5 py-1 text-[9px] font-bold shadow-none`}>
                {streamBadgeText}
              </Badge>
            </div>

            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-300">
              Chỉ số hiện tại, xu hướng và luồng realtime được gom vào một màn để operator nhìn nhanh:
              đang xảy ra gì, có cần can thiệp không, và dữ liệu nào đang đẩy quyết định hiện tại.
            </p>

            <div className="mt-5 flex flex-wrap gap-3">
              <Button variant="cyan" size="sm" onClick={() => navigate("/map")}>
                Bản đồ
              </Button>
              <Button variant="outline" size="sm" onClick={() => navigate("/strategy")}>
                Điều phối
              </Button>
              <Button variant="navy" size="sm" onClick={() => navigate("/logs")}>
                Nhật ký
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setReloadVersion((previous) => previous + 1)}>
                Làm mới
              </Button>
            </div>
          </div>

          <div className="grid gap-3 rounded-3xl border border-white/10 bg-white/5 p-4 shadow-[0_12px_48px_-24px_rgba(0,0,0,0.8)] backdrop-blur-sm sm:grid-cols-3 lg:grid-cols-1">
            <div className="rounded-2xl border border-white/10 bg-black/10 px-4 py-3">
              <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Biến thiên hiện tại</p>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-3xl font-black tracking-tight text-mekong-cyan">
                  {formatSigned(trendDeltaGl, 2)}
                </span>
                <span className="text-[11px] font-black uppercase tracking-widest text-slate-300">g/L</span>
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-black/10 px-4 py-3">
              <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Lần phát tín hiệu</p>
              <p className="mt-2 text-xl font-black tracking-tight text-white">
                {formatTime(state.lastStreamAt)}
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-black/10 px-4 py-3">
              <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Trạng thái dòng</p>
              <p className="mt-2 text-sm font-black leading-snug text-white">
                {trendText}
              </p>
            </div>
          </div>
        </div>
      </section>

      <div className={`grid grid-cols-12 gap-6 ${isBootstrapping ? "hidden" : ""}`}>
        <Card isHoverable className="col-span-12 lg:col-span-4 p-8 border-none shadow-soft group relative overflow-hidden bg-white min-h-70 flex flex-col justify-between">
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

        <Card isHoverable className="col-span-12 lg:col-span-4 p-8 border-none shadow-soft group bg-white min-h-70 flex flex-col justify-between border-t-4 border-t-mekong-critical/20">
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
                <span className="text-[9px] font-bold opacity-70">
                  {weatherSourceLabel} · {formatTime(weatherObservedAt)}
                </span>
              </div>
            </div>
          </div>
        </Card>

        <Card isHoverable className="col-span-12 lg:col-span-4 p-8 border-none shadow-soft group bg-white min-h-70 flex flex-col justify-between relative overflow-hidden">
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
              {weatherSourceLabel} · {formatTime(weatherObservedAt)}
            </span>
          </div>
        </Card>
      </div>

      <div className={`grid grid-cols-12 gap-6 items-start ${isBootstrapping ? "hidden" : ""}`}>
        <div className="col-span-12 xl:col-span-7">
          <Card padding="none" className="h-130 relative overflow-hidden rounded-[40px] shadow-soft border-none">
            <div className="absolute top-8 left-8 z-10 bg-white/90 backdrop-blur-xl p-6 rounded-card shadow-2xl border border-white/50 ring-1 ring-black/5">
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
                gates={mapGates}
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
        <div className="col-span-12 xl:col-span-5">
          <div className="space-y-6 lg:sticky lg:top-24 lg:max-h-[calc(100vh-7rem)] lg:overflow-y-auto lg:pr-1 custom-scrollbar">
            <Card variant="white" className="p-6 border-none shadow-soft rounded-4xl">
              <div className="flex items-start justify-between gap-4 mb-5">
                <div>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.18em]">Điều phối nhanh</p>
                  <h3 className="mt-1 text-sm font-black text-mekong-navy uppercase tracking-[0.15em]">
                    Một chạm tới màn hình chính
                  </h3>
                </div>
                <Badge className="bg-mekong-mint/10 text-mekong-mint border-none text-[9px] py-0.5 px-2 font-bold uppercase">
                  Live
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Button variant="cyan" size="sm" onClick={() => navigate("/map")} className="justify-start h-11">
                  Bản đồ
                </Button>
                <Button variant="outline" size="sm" onClick={() => navigate("/strategy")} className="justify-start h-11">
                  Strategy
                </Button>
                <Button variant="navy" size="sm" onClick={() => navigate("/logs")} className="justify-start h-11">
                  Nhật ký
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setReloadVersion((previous) => previous + 1)} className="justify-start h-11">
                  Làm mới
                </Button>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-2">
                <div className="rounded-2xl bg-slate-50/80 border border-slate-100 p-3">
                  <p className="text-[9px] font-black uppercase tracking-[0.14em] text-slate-400">Sự cố</p>
                  <p className="mt-2 text-lg font-black text-mekong-critical">{state.summary?.open_incidents ?? 0}</p>
                </div>
                <div className="rounded-2xl bg-slate-50/80 border border-slate-100 p-3">
                  <p className="text-[9px] font-black uppercase tracking-[0.14em] text-slate-400">Chờ duyệt</p>
                  <p className="mt-2 text-lg font-black text-mekong-navy">{state.summary?.pending_approvals ?? 0}</p>
                </div>
                <div className="rounded-2xl bg-slate-50/80 border border-slate-100 p-3">
                  <p className="text-[9px] font-black uppercase tracking-[0.14em] text-slate-400">Mô phỏng</p>
                  <p className="mt-2 text-lg font-black text-mekong-mint">{state.summary?.simulated_executions_today ?? 0}</p>
                </div>
              </div>
            </Card>

            <Card variant="white" className="p-6 border-none shadow-soft rounded-4xl">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <h3 className="text-xs font-black text-mekong-navy uppercase tracking-[0.15em]">
                  Điều khiển mô phỏng PLC
                </h3>
                <p className="mt-1 text-[10px] font-bold text-slate-400 uppercase tracking-[0.15em]">
                  Plan hiện tại: {controlPlan ? formatCompactId(controlPlan.id) : "--"}
                </p>
              </div>
              <Badge className="bg-slate-100 text-slate-500 border-none px-2 py-0.5 text-[9px] font-bold uppercase">
                {controlPlanStatusText}
              </Badge>
            </div>

            <div className="space-y-3">
              <p className="text-[12px] font-semibold text-slate-500 leading-relaxed">
                Dùng FE để gọi backend approve/simulate. Khi plan chạy xong, gate thật sẽ đổi status và map tự cập nhật.
              </p>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={plcBusy || controlPlan === null}
                  onClick={() => void handlePlcDemo()}
                  className="inline-flex items-center gap-2 rounded-full bg-mekong-navy px-4 py-2 text-[10px] font-black uppercase tracking-[0.15em] text-white shadow-md transition-all hover:bg-mekong-teal disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {plcBusy ? "Đang chạy..." : controlPlan?.status === "pending_approval" ? "Phê duyệt & mô phỏng" : "Mô phỏng plan approved"}
                </button>
                <button
                  type="button"
                  disabled={plcBusy}
                  onClick={() => setReloadVersion((previous) => previous + 1)}
                  className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-[10px] font-black uppercase tracking-[0.15em] text-mekong-navy transition-all hover:border-mekong-teal/30 hover:text-mekong-teal disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Làm mới
                </button>
              </div>
              <p className="min-h-5 text-[10px] font-bold uppercase tracking-[0.15em] text-slate-400">
                {plcStatusMessage ?? "Chưa chạy mô phỏng."}
              </p>
            </div>
            </Card>
          </div>
        </div>
      </div>

      <div className={`grid grid-cols-12 gap-8 items-stretch ${isBootstrapping ? "hidden" : ""}`}>
        <Card variant="white" className="col-span-12 lg:col-span-8 p-8 border-none shadow-soft flex flex-col rounded-4xl">
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
                className="flex flex-col justify-between gap-6 p-8 rounded-4xl bg-slate-50/50 border-l-8 border-mekong-navy group hover:bg-white hover:shadow-2xl transition-all"
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

        <Card variant="white" className="col-span-12 lg:col-span-4 p-8 border-none shadow-soft rounded-4xl flex flex-col min-h-105">
          <div className="flex items-center justify-between gap-3 mb-5 border-b border-slate-50 pb-4">
            <div className="flex items-center gap-3">
              <Activity size={20} className="text-mekong-navy" />
              <div>
                <h3 className="text-xs font-black text-mekong-navy uppercase tracking-[0.15em]">Luồng cập nhật trực tiếp</h3>
                <p className="mt-1 text-[10px] font-bold text-slate-400 uppercase tracking-[0.15em]">
                  {visibleLiveEvents.length}/{state.liveEvents.length} event đang hiển thị
                </p>
              </div>
            </div>
            <Badge className={`${streamBadgeClass} text-[9px] py-0.5 px-2 font-bold`}>
              {streamBadgeText}
            </Badge>
          </div>

          <div className="flex flex-wrap gap-2 mb-5">
            {[
              { key: "all" as const, label: getFilterLabel("all"), count: liveEventCounts.all },
              { key: "reading" as const, label: getFilterLabel("reading"), count: liveEventCounts.reading },
              { key: "risk" as const, label: getFilterLabel("risk"), count: liveEventCounts.risk },
              { key: "action" as const, label: getFilterLabel("action"), count: liveEventCounts.action },
              { key: "agent" as const, label: getFilterLabel("agent"), count: liveEventCounts.agent },
              { key: "stream" as const, label: getFilterLabel("stream"), count: liveEventCounts.stream },
            ].map((filter) => {
              const isActive = activityFilter === filter.key;
              return (
                <button
                  key={filter.key}
                  type="button"
                  onClick={() => setActivityFilter(filter.key)}
                  className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-[9px] font-black uppercase tracking-[0.15em] transition-all ${
                    isActive
                      ? "border-mekong-navy bg-mekong-navy text-white shadow-md"
                      : "border-slate-200 bg-slate-50 text-slate-500 hover:border-mekong-teal/30 hover:text-mekong-navy"
                  }`}
                >
                  <span>{filter.label}</span>
                  <span className={`rounded-full px-1.5 py-0.5 text-[8px] ${isActive ? "bg-white/15" : "bg-white"}`}>
                    {filter.count}
                  </span>
                </button>
              );
            })}
          </div>

          <div className="grid grid-cols-3 gap-3 mb-6">
            {[
              { icon: Activity, label: "Sự cố đang mở", value: state.summary?.open_incidents ?? 0, color: "text-mekong-critical" },
              { icon: Database, label: "Chờ phê duyệt", value: state.summary?.pending_approvals ?? 0, color: "text-mekong-navy" },
              { icon: Cpu, label: "Mô phỏng hôm nay", value: state.summary?.simulated_executions_today ?? 0, color: "text-mekong-mint" },
            ].map((item) => (
              <div key={item.label} className="rounded-2xl bg-slate-50/70 border border-slate-100 p-3">
                <div className="flex items-center gap-2 text-slate-400 mb-2">
                  <item.icon size={14} strokeWidth={2.5} />
                  <span className="text-[9px] font-black uppercase tracking-[0.15em]">{item.label}</span>
                </div>
                <span className={`text-[16px] font-black ${item.color} tracking-tighter`}>{item.value}</span>
              </div>
            ))}
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto pr-1 custom-scrollbar space-y-3">
            {(visibleLiveEvents.length > 0 ? visibleLiveEvents : []).map((event) => (
              <div
                key={event.id}
                className="group rounded-2xl border border-slate-100 bg-slate-50/70 p-4 transition-all hover:border-mekong-teal/20 hover:bg-white hover:shadow-lg"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <Badge className={`${getActivityBadgeClass(event.kind)} text-[9px] px-2 py-0.5 font-bold`}>
                      {event.badge}
                    </Badge>
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                      {formatTime(event.time)}
                    </span>
                  </div>
                  <ChevronRight size={14} className="text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                </div>
                <h4 className="mt-3 text-sm font-black text-mekong-navy group-hover:text-mekong-teal leading-snug">
                  {event.title}
                </h4>
                <p className="mt-2 text-[12px] text-slate-500 leading-relaxed">
                  {event.detail}
                </p>
                <p className="mt-3 text-[9px] font-black uppercase tracking-[0.2em] text-slate-400">
                  #{formatCompactId(event.id)}
                </p>
              </div>
            ))}

            {state.liveEvents.length === 0 ? (
              <EmptyState
                title="Đang chờ event đầu tiên"
                description="Khi sensor stream hoặc agent run mới xuất hiện, danh sách này sẽ tự cập nhật."
                actionLabel="Tải lại dữ liệu"
                onAction={() => setReloadVersion((previous) => previous + 1)}
              />
            ) : visibleLiveEvents.length === 0 ? (
              <EmptyState
                title="Không có event phù hợp"
                description="Hãy đổi filter để xem một nhóm khác trong luồng realtime."
              />
            ) : null}
          </div>
        </Card>
      </div>
    </div>
  );
}

export default Dashboard;
