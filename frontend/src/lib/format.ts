export function toNumber(value: unknown): number | null {
  if (value === null || value === undefined) {
    return null;
  }

  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatNumber(value: number | null, digits = 2): string {
  if (value === null) {
    return "--";
  }
  return value.toFixed(digits);
}

export function formatDateTime(
  value: string | null | undefined,
  options: Intl.DateTimeFormatOptions = {},
): string {
  if (!value) {
    return "--";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }

  return date.toLocaleString("vi-VN", {
    hour12: false,
    ...options,
  });
}

export function formatTime(
  value: string | null | undefined,
  options: Intl.DateTimeFormatOptions = {},
): string {
  if (!value) {
    return "--:--";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--:--";
  }

  return date.toLocaleTimeString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    ...options,
  });
}

export function formatCompactId(value: string | null | undefined, visibleChars = 6): string {
  if (!value) {
    return "--";
  }

  return value.length > visibleChars + 4
    ? `${value.slice(0, visibleChars)}…${value.slice(-4)}`
    : value;
}

export function formatLabel(value: string | null | undefined): string {
  if (!value) {
    return "--";
  }

  return value
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}
