import { Check, Loader2 } from "lucide-react";
import { clsx } from "clsx";
import type { RunStatus, TimelineEntry } from "@/hooks/useResearchStream";

const STAGES = [
  { key: "supervisor", label: "Supervisor" },
  { key: "researcher", label: "Researcher" },
  { key: "human_review", label: "Review" },
  { key: "writer", label: "Writer" },
  { key: "critiquer", label: "Critiquer" },
] as const;

export function PipelineStatus({
  status,
  timeline,
}: {
  status: RunStatus;
  timeline: TimelineEntry[];
}) {
  const visited = new Set(timeline.map((t) => t.node));
  if (status === "paused") visited.add("human_review");
  const activeNode =
    status === "running" ? timeline[timeline.length - 1]?.node : status === "paused" ? "human_review" : null;

  return (
    <ol className="flex border border-rule bg-surface rounded-sm overflow-hidden">
      {STAGES.map((stage, i) => {
        const isActive = stage.key === activeNode;
        const isDone = visited.has(stage.key) && !isActive;
        return (
          <li key={stage.key} className={clsx("flex-1 min-w-0", i !== 0 && "border-l border-rule")}>
            <div
              className={clsx(
                "px-2 sm:px-3 py-2.5 text-xs sm:text-sm flex items-center gap-1.5 transition-colors",
                isActive && "bg-accent-wash text-accent-strong",
                isDone && "text-verified",
                !isActive && !isDone && "text-ink-muted"
              )}
            >
              <span className="shrink-0 font-mono">
                {isDone ? (
                  <Check className="size-3.5" />
                ) : isActive ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <span className="text-[11px]">0{i + 1}</span>
                )}
              </span>
              <span className="truncate font-medium">{stage.label}</span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
