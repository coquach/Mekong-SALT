import { useMemo, useState } from "react";
import { Bell, CheckCheck, Mail, MessageSquare, RefreshCcw } from "lucide-react";

import { EmptyState, InlineError, SkeletonCards } from "../components/ui/AsyncState";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { PageHeading } from "../components/ui/PageHeading";
import { getApiErrorMessage } from "../lib/api/error";
import { getNotifications, markNotificationRead, type NotificationRead } from "../lib/api/notifications";
import { formatDateTime, formatTime } from "../lib/format";
import { useLivePageRefresh } from "../lib/hooks/useLivePageRefresh";

type NotificationsState = {
  loading: boolean;
  error: string | null;
  items: NotificationRead[];
  lastRefreshAt: string | null;
};

function isNotificationRead(notification: NotificationRead): boolean {
  return Boolean(notification.payload && typeof notification.payload.read === "boolean" && notification.payload.read);
}

function channelLabel(channel: string): string {
  const labels: Record<string, string> = {
    dashboard: "Bảng điều khiển",
    sms_mock: "SMS",
    zalo_mock: "Zalo",
    email_mock: "Email",
  };
  return labels[channel] ?? channel;
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    sent: "Đã gửi",
    pending: "Đang chờ",
    failed: "Lỗi gửi",
  };
  return labels[status] ?? status;
}

function channelIcon(channel: string) {
  if (channel === "email_mock") {
    return Mail;
  }
  if (channel === "sms_mock" || channel === "zalo_mock") {
    return MessageSquare;
  }
  return Bell;
}

function statusBadgeVariant(status: string): "optimal" | "warning" | "critical" | "navy" {
  if (status === "sent") {
    return "optimal";
  }
  if (status === "pending") {
    return "warning";
  }
  if (status === "failed") {
    return "critical";
  }
  return "navy";
}

export function Notifications() {
  const [state, setState] = useState<NotificationsState>(() => {
    return {
      loading: true,
      error: null,
      items: [],
      lastRefreshAt: null,
    };
  });
  const [busyId, setBusyId] = useState<string | null>(null);

  const refreshData = async (options?: { signal?: AbortSignal; showLoading?: boolean }) => {
    const signal = options?.signal;
    const showLoading = options?.showLoading ?? false;

    if (showLoading) {
      setState((previous) => ({ ...previous, loading: true, error: null }));
    }

    try {
      const response = await getNotifications({ limit: 200 }, signal);
      const nextLastRefreshAt = new Date().toISOString();
      setState({
        loading: false,
        error: null,
        items: response.items,
        lastRefreshAt: nextLastRefreshAt,
      });
    } catch (error) {
      if (signal?.aborted) {
        return;
      }
      setState((previous) => ({
        ...previous,
        loading: false,
        error: getApiErrorMessage(error, "Không tải được danh sách thông báo."),
      }));
    }
  };

  useLivePageRefresh({
    refresh: refreshData,
    pollIntervalMs: 10_000,
  });

  const totalCount = state.items.length;
  const unreadCount = useMemo(
    () => state.items.filter((notification) => !isNotificationRead(notification)).length,
    [state.items],
  );
  const sentCount = useMemo(
    () => state.items.filter((notification) => notification.status === "sent").length,
    [state.items],
  );
  const failedCount = useMemo(
    () => state.items.filter((notification) => notification.status === "failed").length,
    [state.items],
  );

  const handleMarkRead = async (notificationId: string) => {
    setBusyId(notificationId);
    try {
      const updatedNotification = await markNotificationRead(notificationId);
      const nextLastRefreshAt = new Date().toISOString();
      setState((previous) => {
        const nextItems = previous.items.map((item) => (item.id === updatedNotification.id ? updatedNotification : item));
        return {
          ...previous,
          items: nextItems,
          lastRefreshAt: nextLastRefreshAt,
        };
      });
    } catch (error) {
      setState((previous) => ({
        ...previous,
        error: getApiErrorMessage(error, "Không cập nhật được trạng thái thông báo."),
      }));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      <PageHeading
        trailing={
          <Badge variant="neutral" className="text-[9px]">
            Đồng bộ lúc {formatTime(state.lastRefreshAt)}
          </Badge>
        }
      />

      {state.error ? (
        <InlineError
          title="Lỗi thông báo"
          message={state.error}
          onRetry={() => void refreshData({ showLoading: true })}
        />
      ) : null}

      {state.loading && state.items.length === 0 ? <SkeletonCards count={3} /> : null}

      <div className={`grid grid-cols-1 gap-6 lg:grid-cols-4 ${state.loading && state.items.length === 0 ? "hidden" : ""}`}>
        <Card variant="white" className="rounded-4xl border border-slate-100 p-6 shadow-soft">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-mekong-navy/10 p-3 text-mekong-navy">
              <Bell size={20} />
            </div>
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Tổng số</p>
              <p className="text-2xl font-black text-mekong-navy">{totalCount}</p>
            </div>
          </div>
        </Card>

        <Card variant="white" className="rounded-4xl border border-slate-100 p-6 shadow-soft">
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Chưa đọc</p>
          <p className="mt-2 text-2xl font-black text-mekong-critical">{unreadCount}</p>
        </Card>

        <Card variant="white" className="rounded-4xl border border-slate-100 p-6 shadow-soft">
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Đã gửi</p>
          <p className="mt-2 text-2xl font-black text-mekong-mint">{sentCount}</p>
        </Card>

        <Card variant="white" className="rounded-4xl border border-slate-100 p-6 shadow-soft">
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Lỗi gửi</p>
          <p className="mt-2 text-2xl font-black text-amber-500">{failedCount}</p>
        </Card>
      </div>

      <Card
        variant="white"
        className={`rounded-4xl border border-slate-100 p-6 shadow-soft ${
          state.loading && state.items.length === 0 ? "hidden" : ""
        }`}
      >
        <div className="flex flex-col gap-4 border-b border-slate-100 pb-5 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="text-xl font-black uppercase tracking-tighter leading-none">Danh sách thông báo</h3>
            <p className="mt-2 text-[11px] font-bold uppercase tracking-[0.15em] text-slate-400">
              {unreadCount} mục chưa đọc • {sentCount} mục đã gửi
            </p>
          </div>

          <Button
            variant="outline"
            className="h-11 rounded-xl border-slate-200 bg-white"
            onClick={() => void refreshData({ showLoading: true })}
          >
            <RefreshCcw size={16} className="mr-2" />
            Làm mới
          </Button>
        </div>

        <div className="mt-6 space-y-3">
          {state.items.length > 0 ? (
            state.items.map((notification) => {
              const Icon = channelIcon(notification.channel);
              const read = isNotificationRead(notification);

              return (
                <div
                  key={notification.id}
                  className={`rounded-3xl border p-4 transition-colors ${
                    read ? "border-slate-100 bg-slate-50/70" : "border-mekong-cyan/20 bg-white"
                  }`}
                >
                  <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant={statusBadgeVariant(notification.status)} className="text-[9px] uppercase">
                          {statusLabel(notification.status)}
                        </Badge>
                        <Badge variant="neutral" className="text-[9px] uppercase">
                          {channelLabel(notification.channel)}
                        </Badge>
                        {read ? (
                          <Badge variant="optimal" className="text-[9px] uppercase">
                            Đã đọc
                          </Badge>
                        ) : (
                          <Badge variant="warning" className="text-[9px] uppercase">
                            Chưa đọc
                          </Badge>
                        )}
                      </div>

                      <div className="mt-3 flex items-start gap-3">
                        <div className="rounded-2xl bg-mekong-navy/10 p-3 text-mekong-navy">
                          <Icon size={18} />
                        </div>
                        <div className="min-w-0">
                          <h4 className="text-base font-black text-mekong-navy">
                            {notification.subject ?? "Thông báo vận hành"}
                          </h4>
                          <p className="mt-1 text-sm leading-relaxed text-slate-600">{notification.message}</p>
                        </div>
                      </div>

                      <div className="mt-4 grid gap-2 text-[11px] font-bold uppercase tracking-[0.14em] text-slate-400 sm:grid-cols-2">
                        <span>Người nhận: {notification.recipient}</span>
                        <span>Gửi lúc: {formatDateTime(notification.sent_at ?? notification.created_at)}</span>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2 md:items-end">
                      <Button
                        variant="navy"
                        size="sm"
                        disabled={read || busyId === notification.id}
                        onClick={() => void handleMarkRead(notification.id)}
                      >
                        <CheckCheck size={16} className="mr-2" />
                        {busyId === notification.id ? "Đang cập nhật..." : read ? "Đã đọc" : "Đánh dấu đã đọc"}
                      </Button>
                      <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-400">
                        #{notification.id.slice(0, 8)}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <EmptyState
              title="Chưa có thông báo"
              description="Thông báo vận hành sẽ xuất hiện tại đây khi backend phát sinh sự kiện mới."
              actionLabel="Làm mới"
              onAction={() => void refreshData({ showLoading: true })}
            />
          )}
        </div>
      </Card>
    </div>
  );
}

export default Notifications;
