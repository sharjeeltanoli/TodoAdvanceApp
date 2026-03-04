import { NextResponse } from "next/server";

/**
 * Diagnostic endpoint — confirms the backend URL is reachable from Vercel.
 * Returns the configured host (not secrets) and the backend's /health response.
 * Safe to expose: no secrets, just connectivity info.
 *
 * Usage: GET /api/backend-check
 */
export async function GET() {
  const raw = process.env.BACKEND_URL || "";
  const backendUrl = raw.replace(/\/+$/, "") || "http://localhost:8000";
  // Only expose host, not any path that might hint at internal structure
  let host: string;
  try {
    host = new URL(backendUrl).host;
  } catch {
    host = "(invalid URL)";
  }

  let backendStatus: unknown = null;
  let error: string | null = null;
  try {
    const res = await fetch(`${backendUrl}/health`, {
      signal: AbortSignal.timeout(5000),
    });
    backendStatus = await res.json();
  } catch (err) {
    error = (err as Error).message;
  }

  return NextResponse.json({
    backendHost: host,
    backendConfigured: !!raw,
    backendHealth: backendStatus,
    backendError: error,
  });
}
