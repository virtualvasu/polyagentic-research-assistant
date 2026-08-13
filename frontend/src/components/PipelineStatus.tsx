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
    <ol className="flex items-stretch gap-1.5 sm:gap-2">
      {STAGES.map((stage, i) => {
        const isActive = stage.key === activeNode;
        const isDone = visited.has(stage.key) && !isActive;
        return (
          <li key={stage.key} className="flex-1 min-w-0">
            <div
              className={clsx(
                "rounded-lg border px-2.5 py-2 text-xs sm:text-sm flex items-center gap-1.5 transition-colors",
                isActive && "border-accent bg-accent/10 text-accent",
                isDone && "border-success/40 bg-success/5 text-success",
                !isActive && !isDone && "border-border text-muted"
              )}
            >
              <span className="shrink-0">
                {isDone ? (
                  <Check className="size-3.5" />
                ) : isActive ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <span className="inline-block size-3.5 text-center leading-none text-[10px]">{i + 1}</span>
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
