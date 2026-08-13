import { NextRequest, NextResponse } from "next/server";
import { BACKEND_URL } from "@/lib/config";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ threadId: string }> }
) {
  const { threadId } = await params;
  const backendRes = await fetch(`${BACKEND_URL}/api/research/${threadId}/state`, {
    cache: "no-store",
  });

  if (!backendRes.ok) {
    const text = await backendRes.text().catch(() => "");
    return NextResponse.json({ error: text || "Not found" }, { status: backendRes.status });
  }

  const data = await backendRes.json();
  return NextResponse.json(data);
}
