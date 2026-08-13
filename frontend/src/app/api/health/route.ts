import { NextResponse } from "next/server";
import { BACKEND_URL } from "@/lib/config";

export async function GET() {
  try {
    const backendRes = await fetch(`${BACKEND_URL}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    if (!backendRes.ok) {
      return NextResponse.json({ reachable: false }, { status: 200 });
    }
    const data = await backendRes.json();
    return NextResponse.json({ reachable: true, ...data });
  } catch {
    return NextResponse.json({ reachable: false }, { status: 200 });
  }
}
