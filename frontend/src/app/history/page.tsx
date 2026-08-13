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
    <div className="mx-auto max-w-3xl px-4 sm:px-6 py-12 sm:py-16">
      <div className="mb-8">
        <h1 className="font-display italic text-3xl sm:text-4xl tracking-tight">Saved reports</h1>
        <p className="text-ink-muted mt-2.5">Reports you chose to keep, stored locally via Prisma.</p>
      </div>

      {reports.length === 0 ? (
        <div className="border border-dashed border-rule rounded-sm py-16 flex flex-col items-center gap-2 text-ink-muted">
          <Inbox className="size-6" />
          <p className="text-sm">No saved reports yet.</p>
          <Link href="/" className="text-sm text-accent hover:underline">
            Start a research run
          </Link>
        </div>
      ) : (
        <ol className="border border-rule bg-surface rounded-sm overflow-hidden">
          {reports.map((r, i) => (
            <li key={r.id} className={i !== 0 ? "border-t border-rule" : ""}>
              <Link
                href={`/history/${r.id}`}
                className="flex items-center gap-3.5 px-4 sm:px-5 py-4 hover:bg-paper-recessed transition-colors"
              >
                <FileText className="size-4 text-ink-muted shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="font-medium truncate">{r.topic}</p>
                  <p className="font-mono text-xs text-ink-muted mt-1">
                    {r.wordCount} words &middot; {r.revisionCount} revisions &middot;{" "}
                    {new Date(r.createdAt).toLocaleDateString()}
                  </p>
                </div>
              </Link>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
