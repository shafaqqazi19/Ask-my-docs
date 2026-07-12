import type { QueryResponse, UploadResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export class ApiError extends Error {}

export async function askQuestion(question: string): Promise<QueryResponse> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 120_000);

  let res: Response;

  try {
    res = await fetch(`${API_BASE}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
      signal: controller.signal,
    });
  } catch {
    throw new ApiError(
      `Couldn't reach the API at ${API_BASE}. Is the FastAPI backend running?`
    );
  } finally {
    clearTimeout(timer);
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // response wasn't JSON; fall back to statusText
    }
    throw new ApiError(`Request failed (${res.status}): ${detail}`);
  }

  return res.json();
}

export async function uploadDocuments(files: File[]): Promise<UploadResponse> {
  const form = new FormData();
  for (const f of files) {
    form.append("files", f);
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
  } catch {
    throw new ApiError(`Couldn't reach the API at ${API_BASE}. Is the FastAPI backend running?`);
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // response wasn't JSON; fall back to statusText
    }
    throw new ApiError(`Upload failed (${res.status}): ${detail}`);
  }

  return res.json();
}
