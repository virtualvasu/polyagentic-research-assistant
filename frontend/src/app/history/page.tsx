import Link from "next/link";
import { FileText, Inbox } from "lucide-react";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

export default async function HistoryPage() {
  const reports = await prisma.report.findMany({
    orderBy: { createdAt: "desc" },
    select: { id: true, topic: true, wordCount: true, revisionCount: true, createdAt: true },
  });

  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10 sm:py-14 space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight">Saved reports</h1>
        <p className="text-muted mt-1.5">Reports you chose to keep, stored locally via Prisma.</p>
      </div>

      {reports.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-16 flex flex-col items-center gap-2 text-muted">
          <Inbox className="size-6" />
          <p className="text-sm">No saved reports yet.</p>
          <Link href="/" className="text-sm text-accent hover:underline">
            Start a research run
          </Link>
        </div>
      ) : (
        <ul className="space-y-2.5">
          {reports.map((r) => (
            <li key={r.id}>
              <Link
                href={`/history/${r.id}`}
                className="flex items-center gap-3 rounded-lg border border-border bg-surface px-4 py-3.5 hover:border-accent/40 hover:bg-surface-muted transition-colors"
              >
                <FileText className="size-4 text-muted shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="font-medium truncate">{r.topic}</p>
                  <p className="text-xs text-muted mt-0.5">
                    {r.wordCount} words &middot; {r.revisionCount} revisions &middot;{" "}
                    {new Date(r.createdAt).toLocaleDateString()}
                  </p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
