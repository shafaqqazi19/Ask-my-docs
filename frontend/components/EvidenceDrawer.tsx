"use client";

import type { EvidenceItem } from "@/lib/types";
import { evidenceDomId } from "@/lib/citations";

interface EvidenceDrawerProps {
  evidence: EvidenceItem[];
  highlightedId: string | null;
}

export function EvidenceDrawer({ evidence, highlightedId }: EvidenceDrawerProps) {
  if (evidence.length === 0) {
    return (
      <div className="rounded-card border border-dashed border-rule p-6 text-center">
        <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">Evidence drawer</p>
        <p className="mt-2 font-sans text-sm text-ink-muted">
          Retrieved chunks will appear here once you ask a question.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">
        Evidence drawer — {evidence.length} chunk{evidence.length === 1 ? "" : "s"}
      </p>
      {evidence.map((item) => {
        const domId = evidenceDomId(item.chunk_id);
        const isHighlighted = highlightedId === item.chunk_id;
        return (
          <div
            id={domId}
            key={item.chunk_id}
            className={`rounded-card border p-4 transition-colors ${
              isHighlighted ? "border-tab bg-tab-soft animate-flash" : "border-rule bg-card"
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono text-[11px] font-medium text-tab">{item.chunk_id}</span>
              <span className="font-mono text-[11px] text-ink-muted">score {item.score.toFixed(3)}</span>
            </div>
            <p className="mt-2 font-sans text-sm leading-snug text-ink-muted line-clamp-4">
              {item.text}
            </p>
          </div>
        );
      })}
    </div>
  );
}
