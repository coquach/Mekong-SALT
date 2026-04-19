import { useEffect, useRef, useState } from "react";

import { getApiBaseUrl } from "../api/http";
import type { ExecutionGraphRead } from "../api/graph";

type GraphStreamStatus = "connecting" | "connected" | "disconnected";

export type GraphTransitionEventPayload = {
  event_type?: string;
  graph_type?: string;
  node?: string;
  status?: string;
  at?: string;
  summary?: string | null;
  details?: Record<string, unknown>;
  run_id?: string | null;
  plan_id?: string | null;
  incident_id?: string | null;
  execution_batch_id?: string | null;
  graph_snapshot?: ExecutionGraphRead | null;
};

type UseGraphStreamOptions = {
  graphType?: string;
  enabled?: boolean;
  onTransition?: (payload: GraphTransitionEventPayload) => void;
};

function parsePayload(rawData: string): GraphTransitionEventPayload | null {
  try {
    const parsed = JSON.parse(rawData) as GraphTransitionEventPayload;
    if (!parsed || typeof parsed !== "object") {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function useGraphStream({
  graphType,
  enabled = true,
  onTransition,
}: UseGraphStreamOptions): {
  streamStatus: GraphStreamStatus;
  lastStreamAt: string | null;
} {
  const [streamStatus, setStreamStatus] = useState<GraphStreamStatus>("connecting");
  const [lastStreamAt, setLastStreamAt] = useState<string | null>(null);
  const onTransitionRef = useRef(onTransition);

  useEffect(() => {
    onTransitionRef.current = onTransition;
  }, [onTransition]);

  useEffect(() => {
    if (!enabled) {
      setStreamStatus("disconnected");
      return;
    }

    let stream: EventSource | null = null;
    let reconnectTimeoutId: number | null = null;
    let isDisposed = false;

    const connect = () => {
      if (isDisposed) {
        return;
      }

      const streamUrl = new URL(`${getApiBaseUrl()}/graphs/stream`);
      if (graphType) {
        streamUrl.searchParams.set("graph_type", graphType);
      }

      setStreamStatus("connecting");
      stream = new EventSource(streamUrl.toString());

      stream.addEventListener("open", () => {
        if (isDisposed) {
          return;
        }
        setStreamStatus("connected");
      });

      stream.addEventListener("graph_transition", (event) => {
        if (isDisposed || !(event instanceof MessageEvent)) {
          return;
        }

        const payload = parsePayload(typeof event.data === "string" ? event.data : "");
        if (!payload) {
          return;
        }

        setStreamStatus("connected");
        setLastStreamAt(payload.at ?? new Date().toISOString());
        onTransitionRef.current?.(payload);
      });

      stream.addEventListener("error", () => {
        if (isDisposed) {
          return;
        }

        setStreamStatus("disconnected");
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
    };
  }, [enabled, graphType]);

  return { streamStatus, lastStreamAt };
}
