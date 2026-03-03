import { NextResponse } from "next/server";

/**
 * Endpoint that pings the backend /health to prevent Render cold starts.
 * Called on page load and by external uptime monitors (e.g. UptimeRobot).
 */
export async function GET() {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

  if (!backendUrl) {
    return NextResponse.json(
      { status: "error", detail: "NEXT_PUBLIC_BACKEND_URL not configured" },
      { status: 500 },
    );
  }

  try {
    const response = await fetch(`${backendUrl}/health`, {
      signal: AbortSignal.timeout(10_000),
    });
    const data = await response.json();
    return NextResponse.json({ status: "ok", backend: data });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { status: "error", detail: message },
      { status: 502 },
    );
  }
}
