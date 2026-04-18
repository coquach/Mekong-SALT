import { invalidatePageCaches } from "./pageCache";

export const DASHBOARD_CACHE_KEY = "mekong.cache.dashboard";
export const STRATEGY_CACHE_KEY = "mekong.cache.strategy";
export const ACTION_LOGS_CACHE_KEY = "mekong.cache.action-logs";
export const NOTIFICATIONS_CACHE_KEY = "mekong.cache.notifications";
export const HISTORY_CACHE_KEY = "mekong.cache.history";
export const INTERACTIVE_MAP_CACHE_KEY = "mekong.cache.interactive-map";

const OPERATIONAL_PAGE_CACHE_KEYS = [
  DASHBOARD_CACHE_KEY,
  STRATEGY_CACHE_KEY,
  ACTION_LOGS_CACHE_KEY,
  NOTIFICATIONS_CACHE_KEY,
  HISTORY_CACHE_KEY,
  INTERACTIVE_MAP_CACHE_KEY,
] as const;

export function invalidateOperationalPageCaches(): void {
  invalidatePageCaches(OPERATIONAL_PAGE_CACHE_KEYS);
}