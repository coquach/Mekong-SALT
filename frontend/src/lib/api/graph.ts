export type ExecutionGraphNodeStatus =
  | "pending"
  | "active"
  | "completed"
  | "skipped"
  | "failed"
  | "blocked";

export type ExecutionGraphStatus = "pending" | "running" | "completed" | "blocked" | "failed";

export interface ExecutionGraphNodeRead {
  id: string;
  label: string;
  kind: string;
  status: ExecutionGraphNodeStatus;
  step_index: number | null;
  started_at: string | null;
  completed_at: string | null;
  summary: string | null;
  details: Record<string, unknown> | null;
}

export interface ExecutionGraphEdgeRead {
  source: string;
  target: string;
  label: string | null;
  status: string | null;
}

export interface ExecutionGraphRead {
  graph_type: string;
  status: ExecutionGraphStatus;
  current_node: string | null;
  summary: string | null;
  started_at: string | null;
  completed_at: string | null;
  nodes: ExecutionGraphNodeRead[];
  edges: ExecutionGraphEdgeRead[];
  metadata: Record<string, unknown>;
}
