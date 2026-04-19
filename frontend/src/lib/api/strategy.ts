import { apiGet, apiPatch, apiPost } from "./http";
import type { ExecutionGraphRead } from "./graph";

export interface GoalThresholds {
  warning_threshold_dsm: number | null;
  critical_threshold_dsm: number | null;
  warning_threshold_gl: number | null;
  critical_threshold_gl: number | null;
}

export interface MonitoringGoalRead {
  id: string;
  created_at: string;
  updated_at: string;
  name: string;
  description: string | null;
  region_id: string;
  station_id: string | null;
  objective: string;
  provider: "mock" | "gemini" | null;
  thresholds: GoalThresholds;
  evaluation_interval_minutes: number;
  is_active: boolean;
  last_run_at: string | null;
  last_run_status: string | null;
  last_run_plan_id: string | null;
  last_processed_reading_id: string | null;
}

export interface MonitoringGoalCollection {
  items: MonitoringGoalRead[];
  count: number;
}

export interface ActionPlanRead {
  id: string;
  created_at: string;
  updated_at: string;
  region_id: string;
  risk_assessment_id: string;
  incident_id: string | null;
  status:
    | "draft"
    | "validated"
    | "pending_approval"
    | "approved"
    | "rejected"
    | "simulated"
    | "closed";
  objective: string;
  generated_by: string;
  model_provider: string | null;
  summary: string;
  assumptions: Record<string, unknown> | null;
  plan_steps: Array<Record<string, unknown>>;
  validation_result: Record<string, unknown> | null;
  approval_explanation: string | null;
}

export interface ApprovalRead {
  id: string;
  created_at: string;
  updated_at: string;
  plan_id: string;
  decided_by_name: string;
  decision: "approved" | "rejected";
  comment: string | null;
  decided_at: string;
}

export interface ApprovalCollection {
  items: ApprovalRead[];
  count: number;
}

export interface ApprovalDecisionResponse {
  approval: ApprovalRead;
  plan: ActionPlanRead;
}

export interface ObservationSnapshotRead {
  id: string;
  created_at: string;
  updated_at: string;
  agent_run_id: string;
  captured_at: string;
  source: string;
  region_id: string | null;
  station_id: string | null;
  reading_id: string | null;
  weather_snapshot_id: string | null;
  payload: Record<string, unknown>;
}

export interface AgentRunRead {
  id: string;
  created_at: string;
  updated_at: string;
  run_type: string;
  trigger_source: string;
  status: string;
  payload: Record<string, unknown>;
  trace: Record<string, unknown> | null;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
  region_id: string | null;
  station_id: string | null;
  risk_assessment_id: string | null;
  incident_id: string | null;
  action_plan_id: string | null;
  observation_snapshot: ObservationSnapshotRead | null;
  execution_graph: ExecutionGraphRead | null;
}

export interface AgentRunCollection {
  items: AgentRunRead[];
  count: number;
}

export interface UpdateGoalPayload {
  objective?: string;
  evaluation_interval_minutes?: number;
  is_active?: boolean;
}

export function getGoals(
  query?: { limit?: number; is_active?: boolean },
  signal?: AbortSignal,
): Promise<MonitoringGoalCollection> {
  return apiGet<MonitoringGoalCollection>("/goals", { query, signal });
}

export function getPlans(
  query?: { limit?: number },
  signal?: AbortSignal,
): Promise<ActionPlanRead[]> {
  return apiGet<ActionPlanRead[]>("/plans", { query, signal });
}

export function decidePlan(
  planId: string,
  payload: { decision: "approved" | "rejected"; comment?: string | null },
  options?: { actorName?: string; signal?: AbortSignal },
): Promise<ApprovalDecisionResponse> {
  return apiPost<ApprovalDecisionResponse>(
    `/approvals/plans/${planId}/decision`,
    {
      decision: payload.decision,
      comment: payload.comment ?? null,
    },
    {
      query: {
        actor_name: options?.actorName ?? "operator",
      },
      signal: options?.signal,
    },
  );
}

export function getPlanApprovalHistory(
  planId: string,
  signal?: AbortSignal,
): Promise<ApprovalCollection> {
  return apiGet<ApprovalCollection>(`/approvals/plans/${planId}/history`, { signal });
}

export function getAgentRuns(
  query?: { limit?: number },
  signal?: AbortSignal,
): Promise<AgentRunCollection> {
  return apiGet<AgentRunCollection>("/agent/runs", { query, signal });
}

export function getAgentRun(runId: string, signal?: AbortSignal): Promise<AgentRunRead> {
  return apiGet<AgentRunRead>(`/agent/runs/${runId}`, { signal });
}

export function updateGoal(
  goalId: string,
  payload: UpdateGoalPayload,
  signal?: AbortSignal,
): Promise<MonitoringGoalRead> {
  return apiPatch<MonitoringGoalRead>(`/goals/${goalId}`, payload, { signal });
}
