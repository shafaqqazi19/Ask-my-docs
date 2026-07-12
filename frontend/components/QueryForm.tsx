"use client";

import { FormEvent, useState } from "react";

const EXAMPLES = [
  "What monthly uptime does the SLA commit to?",
  "How many team members can I invite on the Pro plan?",
  "What is the API rate limit for the Enterprise plan?",
];

interface QueryFormProps {
  onSubmit: (question: string) => void;
  isLoading: boolean;
}

export function QueryForm({ onSubmit, isLoading }: QueryFormProps) {
  const [question, setQuestion] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isLoading) return;
    onSubmit(trimmed);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <label htmlFor="question" className="font-mono text-xs uppercase tracking-widest text-ink-muted">
        Ask the documents
      </label>
      <div className="flex flex-col gap-3 sm:flex-row">
        <textarea
          id="question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. What is the refund window for annual plans?"
          rows={2}
          className="flex-1 resize-none rounded-card border border-rule bg-card px-4 py-3 font-sans text-[15px] text-ink placeholder:text-ink-muted/70 focus-visible:border-tab"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <button
          type="submit"
          disabled={isLoading || !question.trim()}
          className="rounded-card bg-ink px-6 py-3 font-mono text-sm font-medium text-paper transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {isLoading ? "Searching…" : "Ask"}
        </button>
      </div>

      <div className="flex flex-wrap gap-2 pt-1">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            type="button"
            onClick={() => !isLoading && onSubmit(ex)}
            disabled={isLoading}
            className="rounded-card border border-rule bg-transparent px-3 py-1.5 font-sans text-xs text-ink-muted transition-colors hover:border-tab hover:text-ink disabled:opacity-40"
          >
            {ex}
          </button>
        ))}
      </div>
    </form>
  );
}
