"use client";

import { useCallback, useRef, useState } from "react";
import { readSSE } from "@/lib/sse";
import type { ResearchBrief, ResearchState, StartResearchInput } from "@/lib/schemas";

export type RunStatus = "idle" | "running" | "paused" | "completed" | "error";

export interface TimelineEntry {
  node: string;
  output: Record<string, unknown>;
  ts: number;
}

interface State {
  status: RunStatus;
  threadId: string | null;
  timeline: TimelineEntry[];
  latestBrief: ResearchBrief | null;
  finalState: ResearchState | null;
  errorMessage: string | null;
}

const initialState: State = {
  status: "idle",
  threadId: null,
  timeline: [],
  latestBrief: null,
  finalState: null,
  errorMessage: null,
};

export function useResearchStream() {
  const [state, setState] = useState<State>(initialState);
  const threadIdRef = useRef<string | null>(null);

  const consume = useCallback(async (response: Response) => {
    if (!response.ok) {
      const body = await response.json().catch(() => ({ error: response.statusText }));
      setState((s) => ({ ...s, status: "error", errorMessage: String(body.error || "Request failed") }));
      return;
    }

    for await (const evt of readSSE(response)) {
      switch (evt.event) {
        case "thread": {
          threadIdRef.current = evt.data.thread_id;
          setState((s) => ({ ...s, threadId: evt.data.thread_id }));
          break;
        }
        case "step": {
          const entry: TimelineEntry = { node: evt.data.node, output: evt.data.output, ts: Date.now() };
          setState((s) => {
            const latestBrief =
              entry.node === "researcher" && Array.isArray(entry.output.research_findings)
                ? ((entry.output.research_findings as ResearchBrief[]).slice(-1)[0] ?? s.latestBrief)
                : s.latestBrief;
            return { ...s, timeline: [...s.timeline, entry], latestBrief };
          });
          break;
        }
        case "node_error": {
          setState((s) => ({ ...s, status: "error", errorMessage: `${evt.data.node}: ${evt.data.error}` }));
          break;
        }
        case "interrupt": {
          setState((s) => ({ ...s, status: "paused" }));
          break;
        }
        case "done": {
          setState((s) => ({ ...s, status: "completed", finalState: evt.data.final_state }));
          break;
        }
      }
    }
  }, []);

  const start = useCallback(
    async (input: StartResearchInput) => {
      setState({ ...initialState, status: "running" });
      threadIdRef.current = null;
      const res = await fetch("/api/research/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });
      await consume(res);
    },
    [consume]
  );

  const resume = useCallback(
    async (action: "approve" | "research", extra: { editedText?: string; query?: string } = {}) => {
      const threadId = threadIdRef.current;
      if (!threadId) return;
      setState((s) => ({ ...s, status: "running" }));
      const res = await fetch(`/api/research/${threadId}/resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, edited_text: extra.editedText, query: extra.query }),
      });
      await consume(res);
    },
    [consume]
  );

  const reset = useCallback(() => {
    threadIdRef.current = null;
    setState(initialState);
  }, []);

  return { ...state, start, resume, reset };
}
