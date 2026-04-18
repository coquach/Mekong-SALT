import { useEffect, useRef } from "react";

import { isPageCacheFresh, type PageCacheEntry } from "../cache/pageCache";

type PageRefreshOptions = {
  signal?: AbortSignal;
  showLoading?: boolean;
};

type UsePageCacheRefreshOptions<TCache> = {
  cacheEntry: PageCacheEntry<TCache> | null;
  maxAgeMs: number;
  refresh: (options?: PageRefreshOptions) => Promise<void>;
  refreshToken?: unknown;
  refreshOnVisible?: boolean;
};

export function usePageCacheRefresh<TCache>({
  cacheEntry,
  maxAgeMs,
  refresh,
  refreshToken,
  refreshOnVisible = true,
}: UsePageCacheRefreshOptions<TCache>): boolean {
  const shouldShowLoading = cacheEntry === null || !isPageCacheFresh(cacheEntry, maxAgeMs);
  const refreshRef = useRef(refresh);

  useEffect(() => {
    refreshRef.current = refresh;
  }, [refresh]);

  useEffect(() => {
    const abortController = new AbortController();

    void refreshRef.current({
      signal: abortController.signal,
      showLoading: shouldShowLoading,
    });

    return () => abortController.abort();
  }, [refreshToken, shouldShowLoading]);

  useEffect(() => {
    if (!refreshOnVisible) {
      return;
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        void refreshRef.current({ showLoading: false });
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [refreshOnVisible]);

  return shouldShowLoading;
}