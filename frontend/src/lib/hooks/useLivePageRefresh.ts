import { useCallback, useEffect, useRef } from "react";

type PageRefreshOptions = {
  signal?: AbortSignal;
  showLoading?: boolean;
};

type UseLivePageRefreshOptions = {
  refresh: (options?: PageRefreshOptions) => Promise<void>;
  refreshToken?: unknown;
  refreshOnVisible?: boolean;
  refreshOnOnline?: boolean;
  pollIntervalMs?: number;
};

export function useLivePageRefresh({
  refresh,
  refreshToken,
  refreshOnVisible = true,
  refreshOnOnline = true,
  pollIntervalMs,
}: UseLivePageRefreshOptions): void {
  const refreshRef = useRef(refresh);
  const refreshTaskRef = useRef<AbortController | null>(null);

  useEffect(() => {
    refreshRef.current = refresh;
  }, [refresh]);

  useEffect(() => {
    return () => {
      refreshTaskRef.current?.abort();
    };
  }, []);

  const runRefresh = useCallback((options?: PageRefreshOptions) => {
    refreshTaskRef.current?.abort();

    const controller = new AbortController();
    refreshTaskRef.current = controller;

    void refreshRef.current({
      signal: controller.signal,
      showLoading: options?.showLoading ?? false,
    }).finally(() => {
      if (refreshTaskRef.current === controller) {
        refreshTaskRef.current = null;
      }
    });
  }, []);

  useEffect(() => {
    runRefresh({
      showLoading: true,
    });
  }, [refreshToken, runRefresh]);

  useEffect(() => {
    if (!refreshOnVisible) {
      return;
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        runRefresh({ showLoading: false });
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [refreshOnVisible, runRefresh]);

  useEffect(() => {
    if (!refreshOnOnline) {
      return;
    }

    const handleOnline = () => {
      runRefresh({ showLoading: false });
    };

    window.addEventListener("online", handleOnline);
    return () => window.removeEventListener("online", handleOnline);
  }, [refreshOnOnline, runRefresh]);

  useEffect(() => {
    if (pollIntervalMs === undefined || pollIntervalMs <= 0) {
      return;
    }

    const intervalId = window.setInterval(() => {
      if (document.visibilityState === "visible" && navigator.onLine) {
        runRefresh({ showLoading: false });
      }
    }, pollIntervalMs);

    return () => window.clearInterval(intervalId);
  }, [pollIntervalMs, runRefresh]);
}
