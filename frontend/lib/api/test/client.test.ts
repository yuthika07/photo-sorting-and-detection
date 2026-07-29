import { describe, expect, it } from "vitest";

import { ApiError, toApiError } from "@/lib/api/client";

/**
 * Constructs an object shaped exactly like what axios's own
 * isAxiosError() checks for (a plain object with isAxiosError: true)
 * rather than importing a real network layer — this is what keeps
 * these tests fast and independent of any actual HTTP behavior.
 */
function fakeAxiosError(overrides: Record<string, unknown>) {
  return { isAxiosError: true, message: "Request failed", ...overrides };
}

describe("toApiError", () => {
  it("extracts code/message from the backend's standard error envelope", () => {
    const error = fakeAxiosError({
      response: {
        status: 404,
        data: { error: { code: "NOT_FOUND", message: "No person found for id(s): [999]" } },
      },
    });

    const result = toApiError(error);

    expect(result).toBeInstanceOf(ApiError);
    expect(result.code).toBe("NOT_FOUND");
    expect(result.message).toBe("No person found for id(s): [999]");
    expect(result.status).toBe(404);
  });

  it("maps a missing response (network failure) to NETWORK_ERROR", () => {
    const error = fakeAxiosError({ response: undefined, code: "ECONNREFUSED" });

    const result = toApiError(error);

    expect(result.code).toBe("NETWORK_ERROR");
    expect(result.status).toBeNull();
    expect(result.message).toMatch(/couldn't reach the backend/i);
  });

  it("maps a request timeout to TIMEOUT", () => {
    const error = fakeAxiosError({ response: undefined, code: "ECONNABORTED" });

    const result = toApiError(error);

    expect(result.code).toBe("TIMEOUT");
  });

  it("falls back to UNKNOWN_ERROR for a response with no error envelope", () => {
    const error = fakeAxiosError({ response: { status: 500, data: {} } });

    const result = toApiError(error);

    expect(result.code).toBe("UNKNOWN_ERROR");
    expect(result.status).toBe(500);
  });

  it("handles a completely non-axios error safely", () => {
    const result = toApiError(new Error("something else entirely"));

    expect(result).toBeInstanceOf(ApiError);
    expect(result.code).toBe("UNKNOWN_ERROR");
    expect(result.status).toBeNull();
  });

  it("handles a thrown non-Error value safely", () => {
    const result = toApiError("just a string, not even an Error");

    expect(result).toBeInstanceOf(ApiError);
    expect(result.code).toBe("UNKNOWN_ERROR");
  });
});
