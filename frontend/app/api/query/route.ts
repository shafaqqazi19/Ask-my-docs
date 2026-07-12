import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8001";

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 120_000);

  let backendRes: Response;
  try {
    backendRes = await fetch(`${BACKEND}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch {
    return NextResponse.json({ detail: "Backend unreachable" }, { status: 502 });
  } finally {
    clearTimeout(timer);
  }

  const text = await backendRes.text();
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    return NextResponse.json({ detail: "Invalid response from backend" }, { status: 502 });
  }

  return NextResponse.json(data, { status: backendRes.status });
}
