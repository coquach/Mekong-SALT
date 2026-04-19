import { apiGet, apiPost } from "./http";
import type { ActionLogCollection } from "./dashboard";
import type { ExecutionGraphRead } from "./graph";

export interface ExecutionBatchRead {
  id: string;
  plan_id: string;
  region_id: string;
  status: string;
  simulated: boolean;
  requested_by: string | null;
  idempotency_key: string | null;
  started_at: string | null;
  completed_at: string | null;
  step_count: number;
}

export interface ExecutionBatchCollection {
  items: ExecutionBatchRead[];
  count: number;
}

export interface ActionExecutionRead {
  id: string;
  created_at: string;
  updated_at: string;
  plan_id: string;
  batch_id: string | null;
  region_id: string;
  action_type: string;
  status: string;
  simulated: boolean;
  step_index: number;
  started_at: string | null;
  completed_at: string | null;
  result_summary: string | null;
}

export interface ExecutionBatchDetail {
  batch: ExecutionBatchRead;
  executions: ActionExecutionRead[];
  count: number;
  execution_graph: ExecutionGraphRead | null;
}

export interface ActionOutcomeRead {
  id: string;
  created_at: string;
  updated_at: string;
  execution_id: string;
  recorded_at: string;
  pre_metrics: Record<string, unknown> | null;
  post_metrics: Record<string, unknown> | null;
  status:
    | "success"
    | "partial_success"
    | "failed_execution"
    | "failed_plan"
    | "inconclusive";
  summary: string;
}

export interface ActionOutcomeCollection {
  items: ActionOutcomeRead[];
  count: number;
}

export interface FeedbackEvaluation {
  outcome_class:
    | "success"
    | "partial_success"
    | "failed_execution"
    | "failed_plan"
    | "inconclusive";
  status_legacy:
    | "improved"
    | "not_improved"
    | "no_change"
    | "insufficient_new_observation";
  baseline_salinity_dsm: number | null;
  baseline_salinity_gl: number | null;
  latest_salinity_dsm: number | null;
  latest_salinity_gl: number | null;
  delta_dsm: number | null;
  delta_gl: number | null;
  summary: string;
  replan_recommended: boolean;
  replan_reason: string | null;
}

export interface FeedbackSnapshotRead {
  id: string;
  snapshot_kind: "before" | "after";
  captured_at: string;
  salinity_dsm: number | null;
  salinity_gl: number | null;
  water_level_m: number | null;
}

export interface FeedbackLifecycleRead {
  evaluation: FeedbackEvaluation;
  before_snapshot: FeedbackSnapshotRead | null;
  after_snapshot: FeedbackSnapshotRead | null;
  feedback: {
    outcome_class: FeedbackEvaluation["outcome_class"];
    status: "improved" | "not_improved" | "no_change" | "insufficient_new_observation";
    summary: string;
    replan_recommended: boolean;
    replan_reason: string | null;
  };
}

export function getActionLogs(
  query?: { limit?: number; region_code?: string; plan_id?: string },
  signal?: AbortSignal,
): Promise<ActionLogCollection> {
  return apiGet<ActionLogCollection>("/actions/logs", { query, signal });
}

export function getExecutionBatches(
  query?: { limit?: number },
  signal?: AbortSignal,
): Promise<ExecutionBatchCollection> {
  return apiGet<ExecutionBatchCollection>("/execution-batches", { query, signal });
}

export function getExecutionBatchDetail(
  batchId: string,
  signal?: AbortSignal,
): Promise<ExecutionBatchDetail> {
  return apiGet<ExecutionBatchDetail>(`/execution-batches/${batchId}`, { signal });
}

export function simulateExecutionBatch(
  planId: string,
  payload?: { idempotency_key?: string | null },
  signal?: AbortSignal,
): Promise<{
  batch: ExecutionBatchRead;
  executions: ActionExecutionRead[];
  idempotent_replay: boolean;
  execution_graph: ExecutionGraphRead | null;
}> {
  return apiPost(`/execution-batches/plans/${planId}/simulate`, payload ?? {}, { signal });
}

export function getActionOutcomes(
  query?: { limit?: number },
  signal?: AbortSignal,
): Promise<ActionOutcomeCollection> {
  return apiGet<ActionOutcomeCollection>("/action-outcomes", { query, signal });
}

export function evaluateFeedback(
  batchId: string,
  signal?: AbortSignal,
): Promise<FeedbackLifecycleRead> {
  return apiPost<FeedbackLifecycleRead>(
    `/feedback/execution-batches/${batchId}/evaluate`,
    {},
    { signal },
  );
}

export function getLatestFeedback(
  batchId: string,
  signal?: AbortSignal,
): Promise<FeedbackLifecycleRead> {
  return apiGet<FeedbackLifecycleRead>(`/feedback/execution-batches/${batchId}/latest`, { signal });
}
