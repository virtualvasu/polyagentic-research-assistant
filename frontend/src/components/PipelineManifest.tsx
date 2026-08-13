const STAGES = [
  { num: "01", label: "Supervisor", desc: "Routes the run — deterministic rules first, an LLM only when the state is ambiguous." },
  { num: "02", label: "Researcher", desc: "Plans 2–4 sub-queries, searches them concurrently, extracts sourced bullets." },
  { num: "03", label: "Review", desc: "Pauses for you. Approve, edit, or send it back for another search." },
  { num: "04", label: "Writer", desc: "Drafts Key Takeaway → Findings → Analysis → Bottom Line from the approved findings." },
  { num: "05", label: "Critiquer", desc: "Grades the draft; sends it back to the Writer up to 3 times, or approves it." },
];

export function PipelineManifest() {
  return (
    <div className="border border-rule bg-surface rounded-sm">
      <div className="px-4 sm:px-5 py-3 border-b border-rule">
        <span className="font-mono text-[11px] uppercase tracking-widest text-ink-muted">The pipeline</span>
      </div>
      <ol>
        {STAGES.map((s, i) => (
          <li
            key={s.num}
            className={`px-4 sm:px-5 py-3.5 flex gap-3.5 ${i !== STAGES.length - 1 ? "border-b border-rule" : ""} ${
              s.label === "Review" ? "bg-accent-wash" : ""
            }`}
          >
            <span
              className={`font-mono text-xs mt-0.5 shrink-0 ${s.label === "Review" ? "text-accent" : "text-ink-muted"}`}
            >
              {s.num}
            </span>
            <div className="min-w-0">
              <p className={`text-sm font-medium ${s.label === "Review" ? "text-accent-strong" : ""}`}>{s.label}</p>
              <p className="text-sm text-ink-muted mt-0.5 leading-snug">{s.desc}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
