import { ApiError, type ErrorResponse, type SuccessResponse } from "./types";

const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(
  /\/+$/,
  "",
);

export function getApiBaseUrl(): string {
  return apiBaseUrl;
}

type QueryValue = string | number | boolean | null | undefined;

type RequestOptions = Omit<RequestInit, "body"> & {
  query?: Record<string, QueryValue>;
  body?: unknown;
};

function toUrl(path: string, query?: Record<string, QueryValue>): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${apiBaseUrl}${normalizedPath}`);

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value === null || value === undefined || value === "") {
        return;
      }
      url.searchParams.set(key, String(value));
    });
  }

  return url.toString();
}

async function parseJson(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return null;
  }
  return response.json();
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const method = options.method ?? "GET";
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (options.headers) {
    Object.assign(headers, options.headers as Record<string, string>);
  }

  let payloadBody: BodyInit | undefined;
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    payloadBody = JSON.stringify(options.body);
  }

  const response = await fetch(toUrl(path, options.query), {
    ...options,
    method,
    headers,
    body: payloadBody,
  });

  const payload = await parseJson(response);

  if (!response.ok) {
    const errorPayload = payload as ErrorResponse | null;
    throw new ApiError({
      message: errorPayload?.message ?? `Request failed with status ${response.status}.`,
      statusCode: response.status,
      code: errorPayload?.error?.code,
      details: errorPayload?.error?.details,
      requestId: errorPayload?.meta?.request_id ?? null,
    });
  }

  const successPayload = payload as SuccessResponse<T> | null;
  if (!successPayload || successPayload.success !== true) {
    throw new ApiError({
      message: "Unexpected API response format.",
      statusCode: response.status,
      code: "invalid_response_format",
      details: payload,
    });
  }

  return successPayload.data;
}

export async function apiGet<T>(
  path: string,
  options: Omit<RequestOptions, "method" | "body"> = {},
): Promise<T> {
  return apiRequest<T>(path, {
    ...options,
    method: "GET",
  });
}

export async function apiPost<T>(
  path: string,
  body?: unknown,
  options: Omit<RequestOptions, "method" | "body"> = {},
): Promise<T> {
  return apiRequest<T>(path, {
    ...options,
    method: "POST",
    body,
  });
}

export async function apiPatch<T>(
  path: string,
  body?: unknown,
  options: Omit<RequestOptions, "method" | "body"> = {},
): Promise<T> {
  return apiRequest<T>(path, {
    ...options,
    method: "PATCH",
    body,
  });
}
