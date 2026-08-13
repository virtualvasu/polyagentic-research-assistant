"use client";

import { useState } from "react";
import { Check, RotateCcw } from "lucide-react";
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
    <div className="border border-accent/35 bg-surface rounded-sm overflow-hidden">
      <div className="flex items-start justify-between gap-4 px-4 sm:px-5 py-3.5 border-b border-accent/25 bg-accent-wash">
        <div>
          <span className="font-mono text-[11px] uppercase tracking-widest text-accent-strong">
            03 &middot; Awaiting your review
          </span>
          <h3 className="font-display italic text-xl mt-0.5">The Researcher is done</h3>
        </div>
        <span className="shrink-0 font-mono text-[10px] uppercase tracking-wider border border-accent/40 text-accent-strong rounded-sm px-2 py-1 rotate-2">
          Flagged
        </span>
      </div>

      <div className="px-4 sm:px-5 py-4 space-y-4">
        <p className="text-sm text-ink-muted">
          Edit anything below before the Writer drafts the report, or run another search.
        </p>

        <textarea
          value={editedText}
          onChange={(e) => setEditedText(e.target.value)}
          rows={10}
          className="w-full rounded-sm border border-rule bg-paper px-3.5 py-2.5 text-sm font-mono leading-relaxed focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50"
        />

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => onApprove(editedText)}
            className="inline-flex items-center gap-1.5 rounded-sm bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:opacity-90"
          >
            <Check className="size-4" />
            Approve &amp; continue
          </button>
          <button
            onClick={() => setShowResearch((v) => !v)}
            className="inline-flex items-center gap-1.5 rounded-sm border border-rule px-4 py-2 text-sm font-medium hover:bg-paper-recessed"
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
              className="flex-1 min-w-48 rounded-sm border border-rule bg-paper px-3.5 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50"
            />
            <button
              onClick={() => query.trim() && onResearch(query.trim())}
              disabled={!query.trim()}
              className="rounded-sm bg-ink text-paper px-4 py-2 text-sm font-medium disabled:opacity-40"
            >
              Run search
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
