import type {
  EmailAnalyzeRequest,
  EmailAnalyzeResponse,
  LoginRequest,
  RegisterRequest,
  ScanRequest,
  ScanResponse,
  User,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/**
 * Thrown by every function in this module on a non-2xx response. Callers
 * catch this (not a returned error shape) — see analyzeEmail/scanText.
 */
export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Low-level fetch wrapper: sets JSON headers and sends the httpOnly session
 * cookie cross-origin (credentials: "include"). The JWT itself is never
 * readable from JS — the browser attaches it automatically.
 */
export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
}

/**
 * Reads a failed response's body and throws ApiError. FastAPI's `detail`
 * is either a string (HTTPException, e.g. 401/409/501) or an array of
 * Pydantic validation-error objects (422) — normalize both to one message.
 */
async function throwApiError(response: Response): Promise<never> {
  let message = response.statusText || `Request failed with status ${response.status}`;
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") {
      message = body.detail;
    } else if (Array.isArray(body?.detail)) {
      message =
        body.detail
          .map((e: { msg?: string }) => e.msg)
          .filter(Boolean)
          .join("; ") || message;
    }
  } catch {
    // Body wasn't JSON (or was empty) — fall back to statusText/status above.
  }
  throw new ApiError(response.status, message);
}

/** POST /auth/register — throws ApiError on any non-2xx response (e.g. 409 duplicate email). */
export async function registerUser(request: RegisterRequest): Promise<User> {
  const response = await apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    await throwApiError(response);
  }

  return response.json() as Promise<User>;
}

/**
 * POST /auth/login — throws ApiError on any non-2xx response (e.g. 401 invalid
 * credentials). On success the backend sets an httpOnly session cookie; the
 * returned User is informational only, nothing here is stored client-side.
 */
export async function loginUser(request: LoginRequest): Promise<User> {
  const response = await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    await throwApiError(response);
  }

  return response.json() as Promise<User>;
}

/** POST /auth/logout — clears the httpOnly session cookie server-side. */
export async function logoutUser(): Promise<void> {
  const response = await apiFetch("/auth/logout", { method: "POST" });

  if (!response.ok) {
    await throwApiError(response);
  }
}

/** POST /email-analyzer/analyze — throws ApiError on any non-2xx response. */
export async function analyzeEmail(request: EmailAnalyzeRequest): Promise<EmailAnalyzeResponse> {
  const response = await apiFetch("/email-analyzer/analyze", {
    method: "POST",
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    await throwApiError(response);
  }

  return response.json() as Promise<EmailAnalyzeResponse>;
}

/** POST /guardian-scanner/scan — throws ApiError on any non-2xx response. */
export async function scanText(request: ScanRequest): Promise<ScanResponse> {
  const response = await apiFetch("/guardian-scanner/scan", {
    method: "POST",
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    await throwApiError(response);
  }

  return response.json() as Promise<ScanResponse>;
}
