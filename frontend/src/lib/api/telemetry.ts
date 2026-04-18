import { apiGet } from "./http";
import type { RiskLatestResponse, SensorReadingCollection } from "./dashboard";

export interface StationMarkerMetadata {
  icon?: string;
  color?: string;
  tone?: string;
  label?: string;
}

export interface StationMetadata {
  display_name?: string;
  operational_role?: string;
  owner?: string;
  connectivity?: string;
  coverage_radius_km?: number;
  marker?: StationMarkerMetadata;
  notes?: string;
  [key: string]: unknown;
  sensor_package?: string[];
  reference_water_body?: string;
  sampling_interval_minutes?: number;
  calibration_cycle_days?: number;
}

export interface SensorStationRead {
  id: string;
  created_at: string;
  updated_at: string;
  region_id: string;
  code: string;
  name: string;
  station_type: string;
  status: "active" | "inactive" | "maintenance";
  latitude: string | number;
  longitude: string | number;
  location_description: string | null;
  installed_at: string | null;
  station_metadata: StationMetadata | null;
}

export interface SensorStationCollection {
  items: SensorStationRead[];
  count: number;
}

export interface GateMarkerMetadata {
  icon?: string;
  color?: string;
  tone?: string;
  label?: string;
}

export interface GateMetadata {
  display_name?: string;
  operational_role?: string;
  controller?: string;
  control_channel?: string;
  marker?: GateMarkerMetadata;
  notes?: string;
  [key: string]: unknown;
}

export interface SensorStationSummary {
  id: string;
  region_id: string;
  code: string;
  name: string;
  station_type: string;
  status: "active" | "inactive" | "maintenance";
}

export interface GateRead {
  id: string;
  created_at: string;
  updated_at: string;
  region_id: string;
  station_id: string | null;
  code: string;
  name: string;
  gate_type: string;
  status: "open" | "closed" | "transitioning" | "maintenance";
  latitude: string | number;
  longitude: string | number;
  location_description: string | null;
  last_operated_at: string | null;
  gate_metadata: GateMetadata | null;
  station: SensorStationSummary | null;
}

export interface GateCollection {
  items: GateRead[];
  count: number;
}

export interface IncidentRead {
  id: string;
  created_at: string;
  updated_at: string;
  region_id: string;
  station_id: string | null;
  risk_assessment_id: string | null;
  title: string;
  description: string;
  severity: "safe" | "warning" | "danger" | "critical";
  status:
    | "open"
    | "investigating"
    | "pending_plan"
    | "pending_approval"
    | "approved"
    | "executing"
    | "resolved"
    | "closed";
  source: string;
  opened_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  created_by: string | null;
}

export interface IncidentCollection {
  items: IncidentRead[];
  count: number;
}

export interface AuditLogRead {
  id: string;
  created_at: string;
  updated_at: string;
  event_type: string;
  actor_name: string;
  actor_role: string | null;
  region_id: string | null;
  incident_id: string | null;
  action_plan_id: string | null;
  action_execution_id: string | null;
  occurred_at: string;
  summary: string;
  payload: Record<string, unknown> | null;
}

export interface AuditLogCollection {
  items: AuditLogRead[];
  count: number;
}

export function getStations(
  query?: { limit?: number },
  signal?: AbortSignal,
): Promise<SensorStationCollection> {
  return apiGet<SensorStationCollection>("/stations", { query, signal });
}

export function getGates(
  query?: { limit?: number; region_code?: string },
  signal?: AbortSignal,
): Promise<GateCollection> {
  return apiGet<GateCollection>("/gates", { query, signal });
}

export function getReadingHistory(
  query?: {
    station_id?: string;
    station_code?: string;
    region_id?: string;
    region_code?: string;
    start_at?: string;
    end_at?: string;
    limit?: number;
  },
  signal?: AbortSignal,
): Promise<SensorReadingCollection> {
  return apiGet<SensorReadingCollection>("/readings/history", { query, signal });
}

export function getLatestRisk(
  query?: {
    station_id?: string;
    station_code?: string;
    region_id?: string;
    region_code?: string;
  },
  signal?: AbortSignal,
): Promise<RiskLatestResponse> {
  return apiGet<RiskLatestResponse>("/risk/latest", { query, signal });
}

export function getIncidents(
  query?: {
    status?: string;
    region_id?: string;
    limit?: number;
  },
  signal?: AbortSignal,
): Promise<IncidentCollection> {
  return apiGet<IncidentCollection>("/incidents", { query, signal });
}

export function getAuditLogs(
  query?: {
    incident_id?: string;
    plan_id?: string;
    limit?: number;
  },
  signal?: AbortSignal,
): Promise<AuditLogCollection> {
  return apiGet<AuditLogCollection>("/audit/logs", { query, signal });
}
