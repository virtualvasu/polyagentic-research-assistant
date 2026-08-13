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
    <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10 sm:py-14 space-y-5">
      <Link href="/history" className="inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-ink">
        <ArrowLeft className="size-4" />
        Back to history
      </Link>

      <div className="border border-rule bg-surface rounded-sm overflow-hidden">
        <div className="px-5 sm:px-10 pt-7 sm:pt-10 pb-5 border-b border-rule flex items-start justify-between gap-4">
          <div className="min-w-0">
            <span className="font-mono text-[11px] uppercase tracking-widest text-ink-muted">Saved report</span>
            <h1 className="font-display italic text-2xl sm:text-3xl mt-1.5 leading-snug">{report.topic}</h1>
            <p className="font-mono text-xs text-ink-muted mt-3">
              {report.wordCount} words &middot; {report.revisionCount} revisions &middot;{" "}
              {new Date(report.createdAt).toLocaleString()}
            </p>
          </div>
          <DeleteReportButton id={report.id} />
        </div>

        <div className="px-5 sm:px-10 py-7 sm:py-8">
          <Markdown>{report.draft}</Markdown>
        </div>

        {sources.length > 0 && (
          <div className="px-5 sm:px-10 py-6 border-t border-rule">
            <h4 className="font-mono text-[11px] uppercase tracking-widest text-ink-muted mb-3">References</h4>
            <ol className="space-y-1.5 text-sm">
              {sources.map((s, i) => (
                <li key={i} className="flex gap-2.5">
                  <span className="font-mono text-ink-muted shrink-0">[{i + 1}]</span>
                  <a href={s.url} className="text-accent hover:underline truncate" target="_blank" rel="noreferrer">
                    {s.title || s.url}
                  </a>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}
