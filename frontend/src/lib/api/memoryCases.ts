import { apiGet } from "./http";

export interface MemoryCaseRead {
  id: string;
  created_at: string;
  updated_at: string;
  region_id: string;
  station_id: string | null;
  risk_assessment_id: string | null;
  incident_id: string | null;
  action_plan_id: string | null;
  action_execution_id: string | null;
  decision_log_id: string | null;
  objective: string | null;
  severity: string | null;
  outcome_class: string;
  outcome_status_legacy: string | null;
  summary: string;
  context_payload: Record<string, unknown> | null;
  action_payload: Record<string, unknown> | null;
  outcome_payload: Record<string, unknown> | null;
  keywords: string[] | null;
  occurred_at: string;
}

export interface MemoryCaseCollection {
  items: MemoryCaseRead[];
  count: number;
}

export function getMemoryCases(
  query?: {
    region_id?: string;
    station_id?: string;
    severity?: string;
    q?: string;
    limit?: number;
  },
  signal?: AbortSignal,
): Promise<MemoryCaseCollection> {
  return apiGet<MemoryCaseCollection>("/memory-cases", { query, signal });
}