import { apiGet } from "./http";
import type { RiskLatestResponse, SensorReadingCollection } from "./dashboard";

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
  station_metadata: Record<string, unknown> | null;
}

export interface SensorStationCollection {
  items: SensorStationRead[];
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
