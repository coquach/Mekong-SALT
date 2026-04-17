export interface ApiMeta {
  request_id: string | null;
  timestamp: string;
}

export interface SuccessResponse<T> {
  success: true;
  message: string;
  data: T;
  meta: ApiMeta;
}

export interface ErrorDetail {
  code: string;
  details: unknown;
}

export interface ErrorResponse {
  success: false;
  message: string;
  error: ErrorDetail;
  meta: ApiMeta;
}

export class ApiError extends Error {
  statusCode: number;
  code: string;
  details: unknown;
  requestId: string | null;

  constructor(params: {
    message: string;
    statusCode: number;
    code?: string;
    details?: unknown;
    requestId?: string | null;
  }) {
    super(params.message);
    this.name = "ApiError";
    this.statusCode = params.statusCode;
    this.code = params.code ?? "unknown_error";
    this.details = params.details;
    this.requestId = params.requestId ?? null;
  }
}
