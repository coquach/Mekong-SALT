import { apiGet } from "./http";

export interface DashboardSummary {
  open_incidents: number;
  pending_approvals: number;
  active_notifications: number;
  latest_risk_level: string | null;
  latest_salinity_dsm: string | number | null;
  latest_salinity_gl: string | number | null;
  latest_station_code: string | null;
  simulated_executions_today: number;
}

export interface DashboardTimelineItem {
  assessed_at: string;
  station_code: string | null;
  risk_level: string;
  salinity_dsm: string | number | null;
  salinity_gl: string | number | null;
}

export interface DashboardTimeline {
  items: DashboardTimelineItem[];
  count: number;
}

export interface StationSummary {
  id: string;
  region_id: string;
  code: string;
  name: string;
  station_type: string;
  status: string;
}

export interface SensorReading {
  id: string;
  created_at: string;
  updated_at: string;
  station_id: string;
  recorded_at: string;
  salinity_dsm: string | number;
  salinity_gl: string | number | null;
  water_level_m: string | number;
  wind_speed_mps: string | number | null;
  wind_direction_deg: number | null;
  flow_rate_m3s: string | number | null;
  temperature_c: string | number | null;
  battery_level_pct: string | number | null;
  source: string;
  context_payload: Record<string, unknown> | null;
  station: StationSummary;
}

export interface SensorReadingCollection {
  items: SensorReading[];
  count: number;
}

export interface RiskAssessment {
  id: string;
  created_at: string;
  updated_at: string;
  region_id: string;
  station_id: string | null;
  assessed_at: string;
  risk_level: "safe" | "warning" | "danger" | "critical";
  salinity_dsm: string | number | null;
  salinity_gl: string | number | null;
  trend_direction: "rising" | "falling" | "stable" | "unknown";
  trend_delta_dsm: string | number | null;
  trend_delta_gl: string | number | null;
  summary: string;
}

export interface RiskLatestResponse {
  assessment: RiskAssessment;
  reading: SensorReading | null;
  weather_snapshot: Record<string, unknown> | null;
}

export interface ActionExecution {
  id: string;
  created_at: string;
  updated_at: string;
  action_type: string;
  status: string;
  step_index: number;
  started_at: string | null;
  completed_at: string | null;
  result_summary: string | null;
}

export interface DecisionLog {
  summary: string;
}

export interface ActionLogEntry {
  execution: ActionExecution;
  decision_log: DecisionLog | null;
}

export interface ActionLogCollection {
  items: ActionLogEntry[];
  count: number;
}

export function getDashboardSummary(signal?: AbortSignal): Promise<DashboardSummary> {
  return apiGet<DashboardSummary>("/dashboard/summary", { signal });
}

export function getDashboardTimeline(signal?: AbortSignal): Promise<DashboardTimeline> {
  return apiGet<DashboardTimeline>("/dashboard/timeline", { signal });
}

export function getLatestRisk(
  query?: { station_code?: string; region_code?: string },
  signal?: AbortSignal,
): Promise<RiskLatestResponse> {
  return apiGet<RiskLatestResponse>("/risk/latest", { query, signal });
}

export function getLatestReadings(
  query?: { station_code?: string; region_code?: string; limit?: number },
  signal?: AbortSignal,
): Promise<SensorReadingCollection> {
  return apiGet<SensorReadingCollection>("/readings/latest", { query, signal });
}

export function getActionLogs(
  query?: { region_code?: string; limit?: number },
  signal?: AbortSignal,
): Promise<ActionLogCollection> {
  return apiGet<ActionLogCollection>("/actions/logs", { query, signal });
}
