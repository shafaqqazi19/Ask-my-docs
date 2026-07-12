"use client";

import { useState } from "react";
import { QueryForm } from "@/components/QueryForm";
import { AnswerCard } from "@/components/AnswerCard";
import { EvidenceDrawer } from "@/components/EvidenceDrawer";
import { DragDropUpload } from "@/components/DragDropUpload";
import { askQuestion, ApiError } from "@/lib/api";
import { evidenceDomId } from "@/lib/citations";
import type { QueryResponse } from "@/lib/types";

export default function HomePage() {
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);

  async function handleAsk(question: string) {
    setIsLoading(true);
    setError(null);
    setHighlightedId(null);
    try {
      const result = await askQuestion(question);
      setResponse(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
      setResponse(null);
    } finally {
      setIsLoading(false);
    }
  }

  function handleCitationClick(chunkId: string) {
    setHighlightedId(chunkId);
    const el = document.getElementById(evidenceDomId(chunkId));
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
    window.setTimeout(() => setHighlightedId((current) => (current === chunkId ? null : current)), 1500);
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-8 px-6 py-12">
      <header className="flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-1">
            <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">Ask My Docs</p>
            <h1 className="font-display text-3xl font-semibold text-ink">
              Every answer, traced to its source.
            </h1>
          </div>
          <button
            type="button"
            onClick={() => setShowUpload((v) => !v)}
            className="self-start rounded-card border border-rule bg-card px-3 py-1.5 font-mono text-xs text-ink-muted transition-colors hover:border-tab hover:text-ink"
          >
            {showUpload ? "Close upload" : "Upload docs"}
          </button>
        </div>
        <p className="max-w-2xl font-sans text-sm text-ink-muted">
          Answers are generated only from retrieved evidence. Each claim carries a
          citation tab — click one to jump to the exact chunk it came from.
        </p>
      </header>

      {showUpload && (
        <section className="rounded-card border border-rule bg-card p-6">
          <h2 className="mb-3 font-mono text-xs uppercase tracking-widest text-ink-muted">
            Add documents to the index
          </h2>
          <DragDropUpload />
        </section>
      )}

      <QueryForm onSubmit={handleAsk} isLoading={isLoading} />

      {error && (
        <div className="rounded-card border border-rejected/40 bg-rejected-soft px-4 py-3">
          <p className="font-mono text-xs uppercase tracking-widest text-rejected">Request failed</p>
          <p className="mt-1 font-sans text-sm text-ink">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <div>
          {isLoading && !response && (
            <div className="rounded-card border border-rule bg-card p-6">
              <div className="animate-pulse">
                <div className="h-3 w-24 rounded bg-rule" />
                <div className="mt-2 h-5 w-3/4 rounded bg-rule" />
                <div className="mt-6 h-3 w-16 rounded bg-rule" />
                <div className="mt-2 h-4 w-full rounded bg-rule" />
                <div className="mt-2 h-4 w-5/6 rounded bg-rule" />
              </div>
              <p className="mt-4 font-sans text-xs text-ink-muted">
                Loading models on first query may take up to a minute.
              </p>
            </div>
          )}

          {!isLoading && !response && !error && (
            <div className="rounded-card border border-dashed border-rule p-8 text-center">
              <p className="font-display text-lg text-ink">Nothing asked yet</p>
              <p className="mt-1 font-sans text-sm text-ink-muted">
                Try one of the example questions above, or ask your own.
              </p>
            </div>
          )}

          {response && (
            <AnswerCard
              question={response.question}
              answer={response.answer}
              isFullyGrounded={response.is_fully_grounded}
              wasRejected={response.was_rejected}
              latencyMs={response.latency_ms}
              onCitationClick={handleCitationClick}
            />
          )}
        </div>

        <EvidenceDrawer evidence={response?.evidence ?? []} highlightedId={highlightedId} />
      </div>
    </main>
  );
}
