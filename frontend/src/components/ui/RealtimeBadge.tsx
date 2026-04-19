import { Activity } from "lucide-react";

import { Badge } from "./Badge";

type RealtimeMode = "sse" | "polling" | "static";

interface RealtimeBadgeProps {
  mode: RealtimeMode;
  className?: string;
}

function getRealtimeLabel(mode: RealtimeMode): string {
  if (mode === "sse") {
    return "Trực tiếp (SSE)";
  }
  if (mode === "polling") {
    return "Cập nhật định kỳ";
  }
  return "Tĩnh";
}

function getRealtimeVariant(mode: RealtimeMode): "optimal" | "info" | "neutral" {
  if (mode === "sse") {
    return "optimal";
  }
  if (mode === "polling") {
    return "info";
  }
  return "neutral";
}

export function RealtimeBadge({ mode, className }: RealtimeBadgeProps) {
  return (
    <Badge variant={getRealtimeVariant(mode)} className={className}>
      <Activity size={10} />
      {getRealtimeLabel(mode)}
    </Badge>
  );
}
