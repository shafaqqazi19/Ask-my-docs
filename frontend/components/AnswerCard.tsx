import { parseAnswerSegments } from "@/lib/citations";
import { StatusBadge } from "./StatusBadge";

interface AnswerCardProps {
  question: string;
  answer: string;
  isFullyGrounded: boolean;
  wasRejected: boolean;
  latencyMs: number;
  onCitationClick: (chunkId: string) => void;
}

export function AnswerCard({
  question,
  answer,
  isFullyGrounded,
  wasRejected,
  latencyMs,
  onCitationClick,
}: AnswerCardProps) {
  const segments = parseAnswerSegments(answer);

  return (
    <div className="rounded-card border border-rule bg-card p-6">
      <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">Question</p>
      <p className="mt-1 font-display text-lg text-ink">{question}</p>

      <div className="my-5 h-px bg-rule" />

      <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">Answer</p>
      <p className="mt-2 font-sans text-[15px] leading-relaxed text-ink">
        {segments.map((seg, i) =>
          seg.type === "text" ? (
            <span key={i}>{seg.content}</span>
          ) : (
            <button
              key={i}
              type="button"
              onClick={() => onCitationClick(seg.chunkId)}
              title={`Jump to evidence: ${seg.chunkId}`}
              className="mx-0.5 inline-flex -translate-y-0.5 items-center rounded-card border border-tab/50 bg-tab-soft px-1.5 py-0.5 align-middle font-mono text-[10px] font-medium text-tab hover:bg-tab hover:text-card"
            >
              {seg.chunkId}
            </button>
          )
        )}
      </p>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-rule pt-4">
        <StatusBadge isFullyGrounded={isFullyGrounded} wasRejected={wasRejected} />
        <span className="font-mono text-xs text-ink-muted">
          {latencyMs.toFixed(0)} ms
        </span>
      </div>
    </div>
  );
}
