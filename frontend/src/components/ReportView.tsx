"use client";

import { useState } from "react";
import { Download, Save, Check, RotateCcw } from "lucide-react";
import { Markdown } from "@/components/Markdown";
import type { ResearchState } from "@/lib/schemas";

export function ReportView({
  threadId,
  finalState,
  onStartOver,
}: {
  threadId: string;
  finalState: ResearchState;
  onStartOver: () => void;
}) {
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  const wordCount = finalState.draft.split(/\s+/).filter(Boolean).length;
  const sources = finalState.research_findings.flatMap((f) => f.sources);
  const uniqueSources = Array.from(new Map(sources.map((s) => [s.url, s])).values());

  async function handleSave() {
    setSaving(true);
    try {
      await fetch("/api/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          threadId,
          topic: finalState.main_task,
          draft: finalState.draft,
          wordCount,
          revisionCount: finalState.revision_number,
          sources: uniqueSources,
        }),
      });
      setSaved(true);
    } finally {
      setSaving(false);
    }
  }

  function handleDownload() {
    const blob = new Blob([finalState.draft], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${finalState.main_task.slice(0, 60).replace(/[^\w-]+/g, "_")}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-5">
      <div className="border border-rule bg-surface rounded-sm overflow-hidden">
        <div className="px-5 sm:px-10 pt-7 sm:pt-10 pb-5 border-b border-rule">
          <span className="font-mono text-[11px] uppercase tracking-widest text-verified">Final report</span>
          <h2 className="font-display italic text-2xl sm:text-3xl mt-1.5 leading-snug">{finalState.main_task}</h2>
          <p className="font-mono text-xs text-ink-muted mt-3">
            {wordCount} words &middot; {finalState.revision_number} revision
            {finalState.revision_number === 1 ? "" : "s"} &middot; {uniqueSources.length} sources
          </p>
        </div>

        <div className="px-5 sm:px-10 py-7 sm:py-8">
          <Markdown>{finalState.draft}</Markdown>
        </div>

        {uniqueSources.length > 0 && (
          <div className="px-5 sm:px-10 py-6 border-t border-rule">
            <h4 className="font-mono text-[11px] uppercase tracking-widest text-ink-muted mb-3">References</h4>
            <ol className="space-y-1.5 text-sm">
              {uniqueSources.map((s, i) => (
                <li key={i} className="flex gap-2.5">
                  <span className="font-mono text-ink-muted shrink-0">[{i + 1}]</span>
                  <a
                    href={s.url}
                    className="text-accent hover:underline truncate"
                    target="_blank"
                    rel="noreferrer"
                  >
                    {s.title || s.url}
                  </a>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2.5">
        <button
          onClick={handleDownload}
          className="inline-flex items-center gap-1.5 rounded-sm border border-rule px-4 py-2 text-sm font-medium hover:bg-paper-recessed"
        >
          <Download className="size-4" />
          Download .md
        </button>
        <button
          onClick={handleSave}
          disabled={saving || saved}
          className="inline-flex items-center gap-1.5 rounded-sm bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:opacity-90 disabled:opacity-60"
        >
          {saved ? <Check className="size-4" /> : <Save className="size-4" />}
          {saved ? "Saved to history" : saving ? "Saving…" : "Save to history"}
        </button>
        <button
          onClick={onStartOver}
          className="inline-flex items-center gap-1.5 rounded-sm border border-rule px-4 py-2 text-sm font-medium hover:bg-paper-recessed ml-auto"
        >
          <RotateCcw className="size-4" />
          New research
        </button>
      </div>
    </div>
  );
}
