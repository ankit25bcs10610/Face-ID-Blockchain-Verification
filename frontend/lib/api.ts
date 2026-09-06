import type { HealthResponse, PipelineResponse } from "./types";

const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";
const healthEndpoint = process.env.NEXT_PUBLIC_HEALTH_ENDPOINT ?? "/health";
const pipelineEndpoint = process.env.NEXT_PUBLIC_PIPELINE_ENDPOINT ?? "/pipeline/run";
const verifyEndpoint = process.env.NEXT_PUBLIC_VERIFY_ENDPOINT ?? "/verify";

function endpoint(path: string) {
  return `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(endpoint(path), {
    ...init,
    headers: { Accept: "application/json", ...(init?.headers ?? {}) }
  });
  const contentType = response.headers.get("content-type") ?? "";
  const body = contentType.includes("json") ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = typeof body === "object" && body && "detail" in body ? String(body.detail) : response.statusText;
    const error = new Error(detail || "The backend request failed") as Error & { status?: number };
    error.status = response.status;
    throw error;
  }
  return body as T;
}

export function getHealth() {
  return request<HealthResponse>(healthEndpoint);
}

export function runPipeline(file: File, signal?: AbortSignal) {
  const form = new FormData();
  form.append("file", file, file.name);
  return request<PipelineResponse>(pipelineEndpoint, { method: "POST", body: form, signal });
}

export function verifyEvidence(file: File, signal?: AbortSignal) {
  const form = new FormData();
  form.append("file", file, file.name);
  return request<import("./types").VerificationResponse>(verifyEndpoint, { method: "POST", body: form, signal });
}
