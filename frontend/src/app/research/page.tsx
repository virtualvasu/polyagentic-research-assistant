"use client";

import { AlertCircle, RotateCcw } from "lucide-react";
import { useResearchStream } from "@/hooks/useResearchStream";
import { TopicForm } from "@/components/TopicForm";
import { PipelineManifest } from "@/components/PipelineManifest";
import { PipelineStatus } from "@/components/PipelineStatus";
import { ActivityTimeline } from "@/components/ActivityTimeline";
import { HitlPanel } from "@/components/HitlPanel";
import { ReportView } from "@/components/ReportView";

export default function ResearchPage() {
  const { status, threadId, timeline, latestBrief, finalState, errorMessage, start, resume, reset } =
    useResearchStream();

  if (status === "idle") {
    return (
      <div className="mx-auto max-w-4xl px-4 sm:px-6 py-12 sm:py-16">
        <div className="max-w-xl mb-10">
          <h1 className="font-display italic text-3xl sm:text-4xl tracking-tight">
            What should the agents research?
          </h1>
          <p className="text-ink-muted mt-2.5 leading-relaxed">
            Five agents work a single topic through a supervised LangGraph pipeline, with one checkpoint where you
            see the raw findings before a word of the report gets written.
          </p>
        </div>

        <div className="grid lg:grid-cols-[1.1fr_0.9fr] gap-6 items-start">
          <TopicForm onStart={start} />
          <PipelineManifest />
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10 sm:py-14 space-y-6">
      <PipelineStatus status={status} timeline={timeline} />

      {status === "error" && errorMessage && (
        <div className="rounded-sm border border-danger/30 bg-danger-wash px-4 py-3 text-sm text-danger flex items-start gap-2.5">
          <AlertCircle className="size-4 mt-0.5 shrink-0" />
          <div className="flex-1">
            <p className="font-medium">The run hit an error</p>
            <p className="mt-0.5">{errorMessage}</p>
          </div>
          <button
            onClick={reset}
            className="inline-flex items-center gap-1.5 shrink-0 rounded-sm border border-danger/30 px-2.5 py-1 text-xs font-medium hover:bg-danger/10"
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
        <h2 className="font-mono text-[11px] uppercase tracking-widest text-ink-muted mb-3">Activity</h2>
        <ActivityTimeline timeline={timeline} />
      </div>
    </div>
  );
}
