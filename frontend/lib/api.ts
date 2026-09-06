import type { HealthResponse, PipelineResponse } from "./types";

const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";
const healthEndpoint = process.env.NEXT_PUBLIC_HEALTH_ENDPOINT ?? "/health";
const pipelineEndpoint = process.env.NEXT_PUBLIC_PIPELINE_ENDPOINT ?? "/pipeline/run";
const verifyEndpoint = process.env.NEXT_PUBLIC_VERIFY_ENDPOINT ?? "/verify";

function endpoint(path: string) {
  return `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

function extractError(body: unknown, fallback: string): { message: string; code?: string } {
  if (typeof body === "object" && body !== null) {
    const record = body as Record<string, unknown>;
    // The API returns { error: { code, message } }.
    const nested = record.error;
    if (typeof nested === "object" && nested !== null) {
      const inner = nested as Record<string, unknown>;
      if (typeof inner.message === "string") {
        return { message: inner.message, code: typeof inner.code === "string" ? inner.code : undefined };
      }
    }
    if (typeof record.detail === "string") return { message: record.detail };
  }
  if (typeof body === "string" && body.trim()) return { message: body };
  return { message: fallback };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(endpoint(path), {
      ...init,
      headers: { Accept: "application/json", ...(init?.headers ?? {}) }
    });
  } catch {
    const error = new Error(
      `Cannot reach the API at ${baseUrl || "(no API URL configured)"}. Check that the backend is running.`
    ) as Error & { code?: string };
    error.code = "API_UNREACHABLE";
    throw error;
  }
  const contentType = response.headers.get("content-type") ?? "";
  const body = contentType.includes("json") ? await response.json() : await response.text();
  if (!response.ok) {
    const { message, code } = extractError(body, response.statusText || "The backend request failed");
    const error = new Error(message) as Error & { status?: number; code?: string };
    error.status = response.status;
    error.code = code;
    throw error;
  }
  return body as T;
}

export function getHealth() {
  return request<HealthResponse>(healthEndpoint);
}

export type EvidenceSummary = {
  evidence_id: string;
  platform?: string | null;
  post_url?: string | null;
  final_confidence?: number | null;
  face_similarity?: number | null;
  verification_timestamp?: string | null;
};

export function listEvidence() {
  return request<{ count: number; records: EvidenceSummary[] }>("/evidence");
}

export function readEvidenceRecord(id: string) {
  return request<Record<string, unknown>>(`/evidence/${encodeURIComponent(id)}`);
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
