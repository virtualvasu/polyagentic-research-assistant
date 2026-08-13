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
      <div className="grid grid-cols-3 gap-3">
        <Stat label="Words" value={wordCount} />
        <Stat label="Revisions" value={finalState.revision_number} />
        <Stat label="Sources" value={uniqueSources.length} />
      </div>

      <div className="rounded-xl border border-border bg-surface p-5 sm:p-8">
        <Markdown>{finalState.draft}</Markdown>
      </div>

      {uniqueSources.length > 0 && (
        <div className="rounded-lg border border-border bg-surface p-4">
          <h4 className="text-xs font-semibold uppercase tracking-wide text-muted mb-2">Sources</h4>
          <ul className="space-y-1 text-sm">
            {uniqueSources.map((s, i) => (
              <li key={i} className="truncate">
                <a href={s.url} className="text-accent hover:underline" target="_blank" rel="noreferrer">
                  {s.title || s.url}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex flex-wrap gap-2.5">
        <button
          onClick={handleDownload}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-surface-muted"
        >
          <Download className="size-4" />
          Download .md
        </button>
        <button
          onClick={handleSave}
          disabled={saving || saved}
          className="inline-flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-accent-foreground hover:opacity-90 disabled:opacity-60"
        >
          {saved ? <Check className="size-4" /> : <Save className="size-4" />}
          {saved ? "Saved to history" : saving ? "Saving…" : "Save to history"}
        </button>
        <button
          onClick={onStartOver}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-surface-muted ml-auto"
        >
          <RotateCcw className="size-4" />
          New research
        </button>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-surface px-4 py-3">
      <div className="text-xl font-semibold tabular-nums">{value}</div>
      <div className="text-xs text-muted">{label}</div>
    </div>
  );
}
