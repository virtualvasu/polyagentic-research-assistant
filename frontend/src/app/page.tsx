import Link from "next/link";
import { ArrowRight, ExternalLink, ShieldCheck, GitBranch, Database } from "lucide-react";

const REPO_URL = "https://github.com/virtualvasu/polyagentic-research-assistant";

const PRINCIPLES = [
  {
    icon: GitBranch,
    title: "Deterministic first",
    body: "The Supervisor routes on hardcoded rules before it ever calls an LLM — a structured-output fallback only fires when the state is genuinely ambiguous.",
  },
  {
    icon: ShieldCheck,
    title: "One human checkpoint",
    body: "Every run pauses once, after research and before a word is written, so bad source material never silently propagates into the final report.",
  },
  {
    icon: Database,
    title: "Persistent by default",
    body: "Checkpoints live in SQLite, not memory — a paused or interrupted run survives a backend restart and resumes exactly where it left off.",
  },
];

const CASE_NOTES = [
  {
    num: "01",
    title: "Structured output, not string matching",
    body: "Supervisor routing, sub-query planning, and the critique verdict are all typed Pydantic schemas via with_structured_output — no substring-matching on “APPROVED” in free text.",
  },
  {
    num: "02",
    title: "Concurrent sub-query research",
    body: "The Researcher plans 2–4 distinct angles on a topic and searches them in parallel, then dedupes by URL — closer to how modern deep-research agents get real coverage.",
  },
  {
    num: "03",
    title: "Retries that know the difference",
    body: "Transient failures (timeouts, 429s, 5xxs) get exponential backoff. Auth failures fail on the first attempt — never three slow retries against a dead API key.",
  },
  {
    num: "04",
    title: "Untrusted content stays untrusted",
    body: "Web search results are explicitly delimited and framed as data, not instructions, in the summarization prompt — a basic mitigation against indirect prompt injection.",
  },
  {
    num: "05",
    title: "Errors surface, never fabricate",
    body: "A failed node returns a typed error the graph and UI understand. It never invents placeholder “research completed” text that could be silently approved at the review gate.",
  },
];

const STACK = [
  "Next.js", "React", "TypeScript", "Tailwind", "Prisma",
  "FastAPI", "LangGraph", "LangChain", "Groq", "Ollama", "Tavily",
];

export default function LandingPage() {
  return (
    <div>
      {/* Hero */}
      <section className="mx-auto max-w-4xl px-4 sm:px-6 pt-14 sm:pt-20 pb-12 sm:pb-16">
        <span className="font-mono text-[11px] uppercase tracking-widest text-ink-muted">
          Multi-agent research system
        </span>
        <h1 className="font-display italic text-4xl sm:text-6xl tracking-tight mt-3 leading-[1.1]">
          Five agents. One human checkpoint. Zero garbage output.
        </h1>
        <p className="text-ink-muted mt-5 text-base sm:text-lg leading-relaxed max-w-2xl">
          A supervised LangGraph workflow that researches, drafts, and critiques a report on any topic —
          pausing once for you to review the raw findings before a single word of the report gets written.
        </p>

        <div className="flex flex-wrap items-center gap-3 mt-8">
          <Link
            href="/research"
            className="inline-flex items-center gap-2 rounded-sm bg-accent px-5 py-2.5 text-sm font-medium text-accent-foreground hover:opacity-90"
          >
            Start research
            <ArrowRight className="size-4" />
          </Link>
          <a
            href={REPO_URL}
            className="inline-flex items-center gap-2 rounded-sm border border-rule px-5 py-2.5 text-sm font-medium hover:bg-paper-recessed"
          >
            <ExternalLink className="size-4" />
            View source
          </a>
        </div>

        <div className="mt-12 sm:mt-16">
          <div className="flex items-center justify-between mb-2.5">
            <span className="font-mono text-[11px] uppercase tracking-widest text-ink-muted">
              Full run, real output
            </span>
            <span className="font-mono text-[11px] text-ink-muted">sped up ~1.3&times;</span>
          </div>
          <div className="border border-rule bg-surface rounded-sm overflow-hidden">
            {/* eslint-disable-next-line @next/next/no-img-element -- animated GIF; next/image strips animation */}
            <img
              src="/demo.gif"
              alt="Screen recording of a full run: entering a topic, the Researcher's findings pausing for human review, and the final structured report."
              width={760}
              height={476}
              className="w-full h-auto block"
            />
          </div>
        </div>
      </section>

      {/* Why */}
      <section className="border-t border-rule">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 py-14 sm:py-20">
          <p className="font-display italic text-xl sm:text-2xl max-w-2xl leading-snug">
            Most LLM &ldquo;research&rdquo; tools are single-prompt wrappers. This is a proper multi-agent
            workflow with real, crash-safe checkpointing.
          </p>

          <div className="grid sm:grid-cols-3 gap-px bg-rule border border-rule rounded-sm overflow-hidden mt-10">
            {PRINCIPLES.map((p) => (
              <div key={p.title} className="bg-surface px-5 py-6">
                <p.icon className="size-4 text-accent" strokeWidth={1.75} />
                <h3 className="font-medium mt-3">{p.title}</h3>
                <p className="text-sm text-ink-muted mt-1.5 leading-relaxed">{p.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section className="border-t border-rule">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 py-14 sm:py-20">
          <span className="font-mono text-[11px] uppercase tracking-widest text-ink-muted">Architecture</span>
          <h2 className="font-display italic text-2xl sm:text-3xl mt-2">Two services, one typed boundary</h2>
          <p className="text-ink-muted mt-3 max-w-2xl leading-relaxed">
            A Next.js frontend owns the UI and its own saved-report history. A FastAPI service owns the LangGraph
            agent runtime. The browser only ever talks to Next.js &mdash; its Route Handlers proxy everything
            agent-related, including the live SSE stream, straight through.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-stretch gap-0 sm:gap-0 border border-rule rounded-sm overflow-hidden">
            {[
              { label: "Browser", detail: "React UI" },
              { label: "Next.js", detail: "Route Handlers · Prisma" },
              { label: "FastAPI", detail: "SSE · LangGraph" },
              { label: "Providers", detail: "Groq · Ollama · Tavily" },
            ].map((box, i, arr) => (
              <div key={box.label} className="flex-1 flex items-center">
                <div className="flex-1 px-5 py-6 text-center sm:text-left border-t sm:border-t-0 sm:border-l first:border-t-0 first:sm:border-l-0 border-rule">
                  <p className="font-mono text-xs text-ink-muted">{box.detail}</p>
                  <p className="font-medium mt-1">{box.label}</p>
                </div>
                {i !== arr.length - 1 && (
                  <ArrowRight className="hidden sm:block size-4 text-ink-muted shrink-0 mx-1" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Under the hood */}
      <section className="border-t border-rule">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 py-14 sm:py-20">
          <span className="font-mono text-[11px] uppercase tracking-widest text-ink-muted">Under the hood</span>
          <h2 className="font-display italic text-2xl sm:text-3xl mt-2">Five decisions worth reading the code for</h2>

          <ol className="border border-rule bg-surface rounded-sm mt-10">
            {CASE_NOTES.map((n, i) => (
              <li
                key={n.num}
                className={`px-5 py-5 flex gap-4 ${i !== CASE_NOTES.length - 1 ? "border-b border-rule" : ""}`}
              >
                <span className="font-mono text-xs text-ink-muted shrink-0 mt-0.5">{n.num}</span>
                <div>
                  <p className="font-medium">{n.title}</p>
                  <p className="text-sm text-ink-muted mt-1 leading-relaxed">{n.body}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Stack */}
      <section className="border-t border-rule">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 py-10 sm:py-12">
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 font-mono text-xs text-ink-muted">
            {STACK.map((t) => (
              <span key={t}>{t}</span>
            ))}
          </div>
        </div>
      </section>

      {/* Footer CTA */}
      <section className="border-t border-rule">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 py-14 sm:py-20 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6">
          <div>
            <h2 className="font-display italic text-2xl sm:text-3xl">Give it a topic.</h2>
            <p className="text-ink-muted mt-2">See the checkpoint. Read the report.</p>
          </div>
          <Link
            href="/research"
            className="inline-flex items-center gap-2 rounded-sm bg-accent px-5 py-2.5 text-sm font-medium text-accent-foreground hover:opacity-90 shrink-0"
          >
            Start research
            <ArrowRight className="size-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
