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

export interface OpenMeteoWeatherSnapshot {
  observed_at: string;
  wind_speed_mps: number | null;
  wind_direction_deg: number | null;
  tide_level_m: number | null;
  rainfall_mm: number | null;
  condition_summary: string | null;
  source_payload: {
    weather: Record<string, unknown> | null;
    marine: Record<string, unknown> | null;
    provider: string;
  };
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

function resolveOpenMeteoBaseUrl(envValue: string | undefined, fallback: string): string {
  return (envValue ?? fallback).replace(/\/+$/, "");
}

function toNumber(value: unknown): number | null {
  if (value === null || value === undefined) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function normalizeObservedAt(value: unknown): string | null {
  if (typeof value !== "string" || value.length === 0) {
    return null;
  }
  return value.endsWith("Z") ? value : `${value}Z`;
}

async function fetchOpenMeteoJson(url: URL, signal?: AbortSignal): Promise<Record<string, unknown>> {
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(`Open-Meteo request failed with status ${response.status}.`);
  }
  return (await response.json()) as Record<string, unknown>;
}

export async function fetchOpenMeteoWeatherSnapshot(
  params: { latitude: number; longitude: number },
  signal?: AbortSignal,
): Promise<OpenMeteoWeatherSnapshot | null> {
  const weatherBaseUrl = resolveOpenMeteoBaseUrl(
    import.meta.env.VITE_OPEN_METEO_WEATHER_BASE_URL,
    "https://api.open-meteo.com/v1/forecast",
  );
  const marineBaseUrl = resolveOpenMeteoBaseUrl(
    import.meta.env.VITE_OPEN_METEO_MARINE_BASE_URL,
    "https://marine-api.open-meteo.com/v1/marine",
  );

  const weatherUrl = new URL(weatherBaseUrl);
  weatherUrl.searchParams.set("latitude", String(params.latitude));
  weatherUrl.searchParams.set("longitude", String(params.longitude));
  weatherUrl.searchParams.set("current", "wind_speed_10m,wind_direction_10m,precipitation");
  weatherUrl.searchParams.set("timezone", "UTC");

  const marineUrl = new URL(marineBaseUrl);
  marineUrl.searchParams.set("latitude", String(params.latitude));
  marineUrl.searchParams.set("longitude", String(params.longitude));
  marineUrl.searchParams.set("current", "sea_level_height_msl");
  marineUrl.searchParams.set("timezone", "UTC");

  try {
    const [weatherPayload, marinePayload] = await Promise.all([
      fetchOpenMeteoJson(weatherUrl, signal),
      fetchOpenMeteoJson(marineUrl, signal),
    ]);

    const weatherCurrent = (weatherPayload.current ?? {}) as Record<string, unknown>;
    const marineCurrent = (marinePayload.current ?? {}) as Record<string, unknown>;
    const observedAt = normalizeObservedAt(weatherCurrent.time ?? marineCurrent.time);

    if (observedAt === null) {
      return null;
    }

    const windSpeedKmh = toNumber(weatherCurrent.wind_speed_10m);
    const windSpeedMps = windSpeedKmh === null ? null : Number((windSpeedKmh / 3.6).toFixed(2));
    const tideLevel = toNumber(marineCurrent.sea_level_height_msl);

    return {
      observed_at: observedAt,
      wind_speed_mps: windSpeedMps,
      wind_direction_deg: toNumber(weatherCurrent.wind_direction_10m),
      tide_level_m: tideLevel,
      rainfall_mm: toNumber(weatherCurrent.precipitation),
      condition_summary:
        windSpeedKmh === null || tideLevel === null
          ? null
          : `wind=${windSpeedKmh} km/h, tide=${tideLevel} m`,
      source_payload: {
        provider: "open-meteo",
        weather: weatherCurrent,
        marine: marineCurrent,
      },
    };
  } catch {
    return null;
  }
}

export function getActionLogs(
  query?: { region_code?: string; limit?: number },
  signal?: AbortSignal,
): Promise<ActionLogCollection> {
  return apiGet<ActionLogCollection>("/actions/logs", { query, signal });
}
