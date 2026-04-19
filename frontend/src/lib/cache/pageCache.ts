type CacheEntry<T> = {
  value: T;
  updatedAt: number;
};

const CACHE_STORAGE_PREFIX = "mekong.page-cache.v1:";
const memoryCache = new Map<string, CacheEntry<unknown>>();

function isBrowserEnvironment(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function toStorageKey(key: string): string {
  return `${CACHE_STORAGE_PREFIX}${key}`;
}

function readStoredEntry<T>(key: string): CacheEntry<T> | null {
  if (!isBrowserEnvironment()) {
    return null;
  }

  try {
    const rawValue = window.localStorage.getItem(toStorageKey(key));
    if (rawValue === null) {
      return null;
    }

    const parsed = JSON.parse(rawValue) as Partial<CacheEntry<T>> | null;
    if (
      parsed === null ||
      typeof parsed !== "object" ||
      typeof parsed.updatedAt !== "number" ||
      !Object.prototype.hasOwnProperty.call(parsed, "value")
    ) {
      window.localStorage.removeItem(toStorageKey(key));
      return null;
    }

    const entry = {
      value: parsed.value as T,
      updatedAt: parsed.updatedAt,
    };
    memoryCache.set(key, entry as CacheEntry<unknown>);
    return entry;
  } catch {
    window.localStorage.removeItem(toStorageKey(key));
    return null;
  }
}

function persistEntry<T>(key: string, entry: CacheEntry<T>): void {
  memoryCache.set(key, entry as CacheEntry<unknown>);

  if (!isBrowserEnvironment()) {
    return;
  }

  try {
    window.localStorage.setItem(toStorageKey(key), JSON.stringify(entry));
  } catch {
    // Ignore storage quota / serialization issues and keep the in-memory copy.
  }
}

export function readPageCache<T>(key: string): CacheEntry<T> | null {
  const memoryEntry = memoryCache.get(key);
  if (memoryEntry !== undefined) {
    return memoryEntry as CacheEntry<T>;
  }

  return readStoredEntry<T>(key);
}

export function writePageCache<T>(key: string, value: T): CacheEntry<T> {
  const entry: CacheEntry<T> = {
    value,
    updatedAt: Date.now(),
  };

  persistEntry(key, entry);
  return entry;
}

export function invalidatePageCache(key: string): void {
  memoryCache.delete(key);

  if (!isBrowserEnvironment()) {
    return;
  }

  try {
    window.localStorage.removeItem(toStorageKey(key));
  } catch {
    // Ignore storage failures; the in-memory copy is already cleared.
  }
}

export function invalidatePageCaches(keys: readonly string[]): void {
  keys.forEach((key) => invalidatePageCache(key));
}

export function isPageCacheFresh<T>(entry: CacheEntry<T> | null, maxAgeMs: number): boolean {
  if (entry === null || maxAgeMs <= 0) {
    return false;
  }

  return Date.now() - entry.updatedAt <= maxAgeMs;
}

export type { CacheEntry as PageCacheEntry };
