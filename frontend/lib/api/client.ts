import axios, { AxiosError } from "axios";

import type { ApiErrorEnvelope } from "@/lib/types";

/**
 * The one Axios instance the whole app shares. Every endpoint module
 * in lib/api/ imports THIS client rather than importing axios
 * directly — that's what keeps the base URL, timeout, and error
 * shaping defined in exactly one place.
 */
export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000",
  timeout: 30_000,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * A normalized, UI-friendly error. Components never need to know
 * about Axios or the backend's raw error envelope — they only ever
 * see `message` (safe to display) and `code` (safe to branch on).
 */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number | null;

  constructor(message: string, code: string, status: number | null) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

/**
 * Convert any error thrown by an apiClient call into an ApiError.
 * Every function in lib/api/ wraps its request in try/catch and calls
 * this in the catch block, so UI code only ever has to handle one
 * error type regardless of what actually went wrong underneath
 * (network failure, backend validation error, unexpected exception).
 */
export function toApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorEnvelope>;
    const envelope = axiosError.response?.data;

    if (envelope?.error) {
      return new ApiError(envelope.error.message, envelope.error.code, axiosError.response?.status ?? null);
    }

    if (axiosError.code === "ECONNABORTED") {
      return new ApiError("The request timed out. Is the backend running?", "TIMEOUT", null);
    }

    if (!axiosError.response) {
      return new ApiError(
        "Couldn't reach the backend. Is it running on the configured address?",
        "NETWORK_ERROR",
        null
      );
    }

    return new ApiError(axiosError.message, "UNKNOWN_ERROR", axiosError.response.status);
  }

  return new ApiError("Something unexpected went wrong.", "UNKNOWN_ERROR", null);
}
