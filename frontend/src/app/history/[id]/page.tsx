import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { prisma } from "@/lib/prisma";
import { Markdown } from "@/components/Markdown";
import { DeleteReportButton } from "@/components/DeleteReportButton";

export const dynamic = "force-dynamic";

export default async function ReportDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const report = await prisma.report.findUnique({ where: { id } });
  if (!report) notFound();

  const sources = JSON.parse(report.sources) as { title: string; url: string }[];

  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10 sm:py-14 space-y-6">
      <Link href="/history" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-foreground">
        <ArrowLeft className="size-4" />
        Back to history
      </Link>

      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight">{report.topic}</h1>
          <p className="text-muted mt-1.5 text-sm">
            {report.wordCount} words &middot; {report.revisionCount} revisions &middot;{" "}
            {new Date(report.createdAt).toLocaleString()}
          </p>
        </div>
        <DeleteReportButton id={report.id} />
      </div>

      <div className="rounded-xl border border-border bg-surface p-5 sm:p-8">
        <Markdown>{report.draft}</Markdown>
      </div>

      {sources.length > 0 && (
        <div className="rounded-lg border border-border bg-surface p-4">
          <h4 className="text-xs font-semibold uppercase tracking-wide text-muted mb-2">Sources</h4>
          <ul className="space-y-1 text-sm">
            {sources.map((s, i) => (
              <li key={i} className="truncate">
                <a href={s.url} className="text-accent hover:underline" target="_blank" rel="noreferrer">
                  {s.title || s.url}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
