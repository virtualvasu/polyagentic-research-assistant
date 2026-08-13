"use client";

import { useState } from "react";
import { PauseCircle, Check, RotateCcw } from "lucide-react";
import type { ResearchBrief } from "@/lib/schemas";

function briefToText(brief: ResearchBrief): string {
  const bullets = brief.bullets.map((b) => `- ${b}`).join("\n");
  const sources = brief.sources.map((s) => `- [${s.title}](${s.url})`).join("\n");
  return `${bullets}${sources ? `\n\nSources:\n${sources}` : ""}`;
}

export function HitlPanel({
  brief,
  onApprove,
  onResearch,
}: {
  brief: ResearchBrief;
  onApprove: (editedText: string) => void;
  onResearch: (query: string) => void;
}) {
  const [editedText, setEditedText] = useState(() => briefToText(brief));
  const [query, setQuery] = useState("");
  const [showResearch, setShowResearch] = useState(false);

  return (
    <div className="rounded-xl border border-accent/30 bg-accent/5 p-5 space-y-4">
      <div className="flex items-start gap-2.5">
        <PauseCircle className="size-5 text-accent shrink-0 mt-0.5" />
        <div>
          <h3 className="font-semibold">Review the research findings</h3>
          <p className="text-sm text-muted mt-0.5">
            The Researcher is done. Edit anything below before the Writer drafts the report, or run another search.
          </p>
        </div>
      </div>

      <textarea
        value={editedText}
        onChange={(e) => setEditedText(e.target.value)}
        rows={10}
        className="w-full rounded-lg border border-border bg-surface px-3.5 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-accent/50"
      />

      <div className="flex flex-wrap items-center gap-2.5">
        <button
          onClick={() => onApprove(editedText)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-accent-foreground hover:opacity-90"
        >
          <Check className="size-4" />
          Approve &amp; continue
        </button>
        <button
          onClick={() => setShowResearch((v) => !v)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-surface-muted"
        >
          <RotateCcw className="size-4" />
          Re-search
        </button>
      </div>

      {showResearch && (
        <div className="flex flex-wrap items-center gap-2.5 pt-1">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Refined search query&hellip;"
            className="flex-1 min-w-48 rounded-lg border border-border bg-surface px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
          />
          <button
            onClick={() => query.trim() && onResearch(query.trim())}
            disabled={!query.trim()}
            className="rounded-lg bg-foreground text-background px-4 py-2 text-sm font-medium disabled:opacity-40"
          >
            Run search
          </button>
        </div>
      )}
    </div>
  );
}
