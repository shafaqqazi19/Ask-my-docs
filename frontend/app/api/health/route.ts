import { NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8001";

export async function GET() {
  try {
    const res = await fetch(`${BACKEND}/health`, { cache: "no-store" });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json(
      { status: "error", detail: "Backend unreachable" },
      { status: 503 },
    );
  }
}
