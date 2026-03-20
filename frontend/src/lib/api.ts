import type { PredictionResponse } from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchPrediction(
  ticker: string,
  days: number = 30
): Promise<PredictionResponse> {
  const url = `${API_BASE}/api/predict/quick?ticker=${encodeURIComponent(ticker)}&days=${days}`;
  const res = await fetch(url, { cache: "no-store" });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }

  return res.json() as Promise<PredictionResponse>;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}
