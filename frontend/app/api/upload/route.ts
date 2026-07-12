import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8001";

export async function POST(request: NextRequest) {
  let formData: FormData;
  try {
    formData = await request.formData();
  } catch {
    return NextResponse.json({ detail: "Invalid form data" }, { status: 400 });
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 300_000);

  let backendRes: Response;
  try {
    backendRes = await fetch(`${BACKEND}/upload`, {
      method: "POST",
      body: formData,
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
