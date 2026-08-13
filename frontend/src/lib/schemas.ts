import { z } from "zod";

// Mirrors backend/app/schemas.py — kept in sync by hand since the two
// services are different languages (see README for why tRPC was dropped:
// it can't type-check across that boundary anyway).

export const startResearchSchema = z.object({
  topic: z.string().min(1).max(500),
  llm_provider: z.enum(["groq", "ollama"]).default("groq"),
  llm_model: z.string().optional(),
  ollama_url: z.string().optional(),
});
export type StartResearchInput = z.infer<typeof startResearchSchema>;

export const resumeActionSchema = z.object({
  action: z.enum(["approve", "research"]),
  edited_text: z.string().optional(),
  query: z.string().optional(),
});
export type ResumeActionInput = z.infer<typeof resumeActionSchema>;

export const sourceSchema = z.object({
  title: z.string(),
  url: z.string(),
});
export type Source = z.infer<typeof sourceSchema>;

export const researchBriefSchema = z.object({
  query: z.string(),
  sub_queries: z.array(z.string()),
  bullets: z.array(z.string()),
  sources: z.array(sourceSchema),
});
export type ResearchBrief = z.infer<typeof researchBriefSchema>;

export const researchStateSchema = z.object({
  main_task: z.string(),
  research_findings: z.array(researchBriefSchema),
  draft: z.string(),
  critique_notes: z.string(),
  critique_approved: z.boolean(),
  revision_number: z.number(),
  next_step: z.string(),
  current_sub_task: z.string(),
  llm_provider: z.string(),
  llm_model: z.string(),
  ollama_url: z.string(),
  hitl_approved: z.boolean(),
  hitl_edited_findings: z.string(),
  error: z.string().optional(),
});
export type ResearchState = z.infer<typeof researchStateSchema>;

export const saveReportSchema = z.object({
  threadId: z.string(),
  topic: z.string(),
  draft: z.string(),
  wordCount: z.number(),
  revisionCount: z.number(),
  sources: z.array(sourceSchema),
});
export type SaveReportInput = z.infer<typeof saveReportSchema>;

// ─── SSE event payloads (see backend/app/main.py _sse helper) ──────────────

export type SSEEvent =
  | { event: "thread"; data: { thread_id: string } }
  | { event: "step"; data: { node: string; output: Record<string, unknown> } }
  | { event: "node_error"; data: { node: string; error: string } }
  | { event: "interrupt"; data: { payload: { type: string; latest_finding: ResearchBrief | null } } }
  | { event: "done"; data: { final_state: ResearchState } };
