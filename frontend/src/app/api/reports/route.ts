import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { saveReportSchema } from "@/lib/schemas";

export async function GET() {
  const reports = await prisma.report.findMany({
    orderBy: { createdAt: "desc" },
    select: {
      id: true,
      threadId: true,
      topic: true,
      wordCount: true,
      revisionCount: true,
      createdAt: true,
    },
  });
  return NextResponse.json(reports);
}

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => null);
  const parsed = saveReportSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }

  const { threadId, topic, draft, wordCount, revisionCount, sources } = parsed.data;

  const report = await prisma.report.upsert({
    where: { threadId },
    create: { threadId, topic, draft, wordCount, revisionCount, sources: JSON.stringify(sources) },
    update: { draft, wordCount, revisionCount, sources: JSON.stringify(sources) },
  });

  return NextResponse.json(report, { status: 201 });
}
