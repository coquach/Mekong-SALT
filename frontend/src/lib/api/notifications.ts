import { apiGet, apiPatch } from "./http";

export interface NotificationRead {
  id: string;
  incident_id: string | null;
  execution_id: string | null;
  created_at: string;
  updated_at: string;
  channel: string;
  status: string;
  recipient: string;
  subject: string | null;
  message: string;
  payload: Record<string, unknown> | null;
  sent_at: string | null;
}

export interface NotificationCollection {
  items: NotificationRead[];
  count: number;
}

export function getNotifications(
  query?: { limit?: number },
  signal?: AbortSignal,
): Promise<NotificationCollection> {
  return apiGet<NotificationCollection>("/notifications", { query, signal });
}

export function markNotificationRead(
  notificationId: string,
  signal?: AbortSignal,
): Promise<NotificationRead> {
  return apiPatch<NotificationRead>(`/notifications/${notificationId}/read`, undefined, { signal });
}
