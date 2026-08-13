import { CheckCircle2, XCircle, ArrowRight, FileText, Search, UserCheck } from "lucide-react";
import type { TimelineEntry } from "@/hooks/useResearchStream";
import type { ResearchBrief } from "@/lib/schemas";

const NODE_LABEL: Record<string, string> = {
  supervisor: "Supervisor",
  researcher: "Researcher",
  human_review: "Review",
  writer: "Writer",
  critiquer: "Critiquer",
};

export function ActivityTimeline({ timeline }: { timeline: TimelineEntry[] }) {
  return (
    <ol className="space-y-2.5">
      {timeline.map((entry, i) => (
        <li
          key={i}
          className="border border-rule bg-surface rounded-sm px-4 py-3.5 entry-in"
        >
          <div className="flex items-center justify-between mb-1.5">
            <span className="font-mono text-[11px] uppercase tracking-widest text-ink-muted">
              {NODE_LABEL[entry.node] ?? entry.node}
            </span>
          </div>
          <NodeBody node={entry.node} output={entry.output} />
        </li>
      ))}
    </ol>
  );
}

function NodeBody({ node, output }: { node: string; output: Record<string, unknown> }) {
  switch (node) {
    case "supervisor": {
      const next = String(output.next_step ?? "");
      const task = String(output.current_sub_task ?? "");
      return (
        <p className="text-sm flex items-center gap-1.5">
          <ArrowRight className="size-3.5 text-accent shrink-0" />
          Routed to <span className="font-medium">{next}</span>
          {task && <span className="text-ink-muted"> &mdash; {task}</span>}
        </p>
      );
    }
    case "researcher": {
      const findings = output.research_findings as ResearchBrief[] | undefined;
      const brief = findings?.[findings.length - 1];
      if (!brief) return null;
      return (
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-1.5 text-ink-muted font-mono text-xs">
            <Search className="size-3.5 shrink-0" />
            <span>{brief.sub_queries.join(" · ")}</span>
          </div>
          <ul className="list-disc pl-5 space-y-1">
            {brief.bullets.slice(0, 3).map((b, i) => (
              <li key={i}>{b}</li>
            ))}
            {brief.bullets.length > 3 && <li className="text-ink-muted">+{brief.bullets.length - 3} more</li>}
          </ul>
        </div>
      );
    }
    case "writer": {
      const rev = Number(output.revision_number ?? 0);
      const draft = String(output.draft ?? "");
      return (
        <p className="text-sm flex items-center gap-1.5">
          <FileText className="size-3.5 text-accent shrink-0" />
          Draft v{rev} written &mdash; {draft.split(/\s+/).filter(Boolean).length} words
        </p>
      );
    }
    case "critiquer": {
      const approved = Boolean(output.critique_approved);
      const notes = String(output.critique_notes ?? "");
      return (
        <div className="text-sm space-y-1.5">
          <p className="flex items-center gap-1.5">
            {approved ? (
              <CheckCircle2 className="size-3.5 text-verified shrink-0" />
            ) : (
              <XCircle className="size-3.5 text-accent shrink-0" />
            )}
            {approved ? "Approved" : "Revisions requested"}
          </p>
          {!approved && <p className="text-ink-muted whitespace-pre-line">{notes}</p>}
        </div>
      );
    }
    case "human_review": {
      const approved = Boolean(output.hitl_approved);
      return (
        <p className="text-sm flex items-center gap-1.5">
          <UserCheck className="size-3.5 text-accent shrink-0" />
          {approved ? "You approved the findings" : "You requested another search"}
        </p>
      );
    }
    default:
      return null;
  }
}
