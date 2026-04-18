type CacheEntry<T> = {
  value: T;
  updatedAt: number;
};

const memoryCache = new Map<string, CacheEntry<unknown>>();

function getSessionStorage(): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

export function readPageCache<T>(key: string): CacheEntry<T> | null {
  const inMemory = memoryCache.get(key);
  if (inMemory) {
    return inMemory as CacheEntry<T>;
  }

  const storage = getSessionStorage();
  if (!storage) {
    return null;
  }

  const rawValue = storage.getItem(key);
  if (!rawValue) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawValue) as CacheEntry<T>;
    if (
      typeof parsed !== "object" ||
      parsed === null ||
      typeof parsed.updatedAt !== "number" ||
      !Number.isFinite(parsed.updatedAt)
    ) {
      return null;
    }
    memoryCache.set(key, parsed);
    return parsed;
  } catch {
    return null;
  }
}

export function writePageCache<T>(key: string, value: T): CacheEntry<T> {
  const entry: CacheEntry<T> = {
    value,
    updatedAt: Date.now(),
  };

  memoryCache.set(key, entry);

  const storage = getSessionStorage();
  if (storage) {
    try {
      storage.setItem(key, JSON.stringify(entry));
    } catch {
      // Ignore quota or serialization failures.
    }
  }

  return entry;
}

export function invalidatePageCache(key: string): void {
  memoryCache.delete(key);

  const storage = getSessionStorage();
  if (storage) {
    try {
      storage.removeItem(key);
    } catch {
      // Ignore storage failures when clearing cache.
    }
  }
}

export function invalidatePageCaches(keys: readonly string[]): void {
  keys.forEach((key) => invalidatePageCache(key));
}

export function isPageCacheFresh<T>(entry: CacheEntry<T> | null, maxAgeMs: number): boolean {
  if (!entry) {
    return false;
  }
  return Date.now() - entry.updatedAt <= maxAgeMs;
}

export type { CacheEntry as PageCacheEntry };
