import { API_BASE_URL } from "../config";
import type { ApiError } from "./types";

export class ApiRequestError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function parseError(response: Response): Promise<never> {
  let message = response.statusText;
  let code = "http_error";
  try {
    const body = (await response.json()) as ApiError;
    message = body.error.message;
    code = body.error.code;
  } catch {
    // keep status text when the body is not the standard error envelope
  }
  throw new ApiRequestError(response.status, code, message);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiRequestError(0, "network_error", "Unable to reach the API");
  }
  if (!response.ok) {
    await parseError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiRequestError(response.status, "http_error", "API returned a non-JSON response");
  }
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path);
}

export function apiPost<T, B>(path: string, body: B): Promise<T> {
  return request<T>(path, { method: "POST", body: JSON.stringify(body) });
}

export function apiPatch<T, B>(path: string, body: B): Promise<T> {
  return request<T>(path, { method: "PATCH", body: JSON.stringify(body) });
}
