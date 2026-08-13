"use client";

import { useEffect, useState } from "react";
import { ArrowRight, AlertTriangle } from "lucide-react";
import type { StartResearchInput } from "@/lib/schemas";

const GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"];
const OLLAMA_MODELS = ["llama3.1:latest", "llama3.1:8b", "qwen2.5:7b", "mistral:7b"];

interface HealthState {
  reachable: boolean;
  tavily_configured?: boolean;
  groq_configured?: boolean;
  ollama_reachable?: boolean;
}

export function TopicForm({ onStart }: { onStart: (input: StartResearchInput) => void }) {
  const [topic, setTopic] = useState("");
  const [provider, setProvider] = useState<"groq" | "ollama">("groq");
  const [model, setModel] = useState(GROQ_MODELS[0]);
  const [health, setHealth] = useState<HealthState | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth({ reachable: false }));
  }, []);

  function handleProviderChange(next: "groq" | "ollama") {
    setProvider(next);
    setModel(next === "groq" ? GROQ_MODELS[0] : OLLAMA_MODELS[0]);
  }

  const providerReady = provider === "groq" ? health?.groq_configured : health?.ollama_reachable;
  const canSubmit = topic.trim().length > 0 && health?.reachable && health?.tavily_configured && providerReady;

  return (
    <div className="space-y-4">
      {health && !health.reachable && (
        <Banner tone="danger">
          Can&rsquo;t reach the research backend. Confirm the FastAPI service is running and{" "}
          <code className="font-mono text-xs">BACKEND_URL</code> is set correctly.
        </Banner>
      )}
      {health?.reachable && !health.tavily_configured && (
        <Banner tone="danger">
          <code className="font-mono text-xs">TAVILY_API_KEY</code> is not configured on the backend — web search
          will fail. Add it to <code className="font-mono text-xs">backend/.env</code>.
        </Banner>
      )}
      {health?.reachable && health.tavily_configured && !providerReady && (
        <Banner tone="warning">
          {provider === "groq"
            ? "GROQ_API_KEY is not configured on the backend."
            : "Ollama isn't reachable at the configured host — pull a model and make sure it's running."}
        </Banner>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!canSubmit) return;
          onStart({ topic: topic.trim(), llm_provider: provider, llm_model: model });
        }}
        className="border border-rule bg-surface rounded-sm"
      >
        <div className="px-4 sm:px-5 py-3 border-b border-rule flex items-center justify-between">
          <span className="font-mono text-[11px] uppercase tracking-widest text-ink-muted">Research topic</span>
          <span className="font-mono text-[11px] text-ink-muted">{topic.length}/500</span>
        </div>

        <textarea
          id="topic"
          value={topic}
          onChange={(e) => setTopic(e.target.value.slice(0, 500))}
          placeholder="e.g. Impact of quantum computing on modern cryptography"
          rows={4}
          autoFocus
          className="w-full resize-none bg-transparent px-4 sm:px-5 py-4 text-[15px] placeholder:text-ink-muted/70 focus:outline-none"
        />

        <div className="px-4 sm:px-5 py-4 border-t border-rule grid grid-cols-2 gap-3 sm:gap-4">
          <Field label="Provider">
            <select
              value={provider}
              onChange={(e) => handleProviderChange(e.target.value as "groq" | "ollama")}
              className="select-plain w-full rounded-sm border border-rule bg-paper px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50"
            >
              <option value="groq">Groq (cloud)</option>
              <option value="ollama">Ollama (local)</option>
            </select>
          </Field>
          <Field label="Model">
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="select-plain w-full rounded-sm border border-rule bg-paper px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50"
            >
              {(provider === "groq" ? GROQ_MODELS : OLLAMA_MODELS).map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </Field>
        </div>

        <div className="px-4 sm:px-5 py-4 border-t border-rule">
          <button
            type="submit"
            disabled={!canSubmit}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-sm bg-accent px-5 py-2.5 text-sm font-medium text-accent-foreground transition-opacity hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Start research
            <ArrowRight className="size-4" />
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block font-mono text-[11px] uppercase tracking-widest text-ink-muted mb-1.5">{label}</span>
      {children}
    </label>
  );
}

function Banner({ tone, children }: { tone: "danger" | "warning"; children: React.ReactNode }) {
  return (
    <div
      className={`flex items-start gap-2.5 rounded-sm border px-3.5 py-3 text-sm ${
        tone === "danger" ? "border-danger/30 bg-danger-wash text-danger" : "border-accent/30 bg-accent-wash text-accent-strong"
      }`}
    >
      <AlertTriangle className="size-4 mt-0.5 shrink-0" />
      <p>{children}</p>
    </div>
  );
}
