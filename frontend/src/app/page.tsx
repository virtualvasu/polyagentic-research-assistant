"use client";

import { AlertCircle, RotateCcw } from "lucide-react";
import { useResearchStream } from "@/hooks/useResearchStream";
import { TopicForm } from "@/components/TopicForm";
import { PipelineStatus } from "@/components/PipelineStatus";
import { ActivityTimeline } from "@/components/ActivityTimeline";
import { HitlPanel } from "@/components/HitlPanel";
import { ReportView } from "@/components/ReportView";

export default function Home() {
  const { status, threadId, timeline, latestBrief, finalState, errorMessage, start, resume, reset } =
    useResearchStream();

  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10 sm:py-14 space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight">
          {status === "idle" ? "What should the agents research?" : "Research in progress"}
        </h1>
        <p className="text-muted mt-1.5">
          A Supervisor, Researcher, Writer, and Critiquer collaborate through a LangGraph workflow &mdash; with a
          human checkpoint before any writing begins.
        </p>
      </div>

      {status === "idle" && <TopicForm onStart={start} />}

      {status !== "idle" && (
        <div className="space-y-6">
          <PipelineStatus status={status} timeline={timeline} />

          {status === "error" && errorMessage && (
            <div className="rounded-lg border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger flex items-start gap-2.5">
              <AlertCircle className="size-4 mt-0.5 shrink-0" />
              <div className="flex-1">
                <p className="font-medium">The run hit an error</p>
                <p className="mt-0.5">{errorMessage}</p>
              </div>
              <button
                onClick={reset}
                className="inline-flex items-center gap-1.5 shrink-0 rounded-md border border-danger/30 px-2.5 py-1 text-xs font-medium hover:bg-danger/10"
              >
                <RotateCcw className="size-3.5" />
                Start over
              </button>
            </div>
          )}

          {status === "paused" && latestBrief && (
            <HitlPanel
              brief={latestBrief}
              onApprove={(edited) => resume("approve", { editedText: edited })}
              onResearch={(query) => resume("research", { query })}
            />
          )}

          {status === "completed" && finalState && threadId && (
            <ReportView threadId={threadId} finalState={finalState} onStartOver={reset} />
          )}

          <div>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-muted mb-3">Activity</h2>
            <ActivityTimeline timeline={timeline} />
          </div>
        </div>
      )}
    </div>
  );
}
