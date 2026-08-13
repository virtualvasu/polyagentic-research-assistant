import { NextRequest, NextResponse } from "next/server";
import { BACKEND_URL } from "@/lib/config";
import { resumeActionSchema } from "@/lib/schemas";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ threadId: string }> }
) {
  const { threadId } = await params;
  const body = await request.json().catch(() => null);
  const parsed = resumeActionSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }

  const backendRes = await fetch(`${BACKEND_URL}/api/research/${threadId}/resume`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(parsed.data),
  });

  if (!backendRes.ok || !backendRes.body) {
    const text = await backendRes.text().catch(() => "");
    return NextResponse.json({ error: text || "Backend unavailable" }, { status: backendRes.status || 502 });
  }

  return new Response(backendRes.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
