import { ApiError, type ErrorResponse } from "./types";

export function getApiErrorMessage(error: unknown, fallbackMessage: string): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error && typeof error === "object") {
    const maybeError = error as ErrorResponse;
    if (typeof maybeError.message === "string") {
      return maybeError.message;
    }
  }

  return fallbackMessage;
}
