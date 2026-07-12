interface StatusBadgeProps {
  isFullyGrounded: boolean;
  wasRejected: boolean;
}

export function StatusBadge({ isFullyGrounded, wasRejected }: StatusBadgeProps) {
  if (wasRejected) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-card border border-rejected/40 bg-rejected-soft px-2.5 py-1 text-xs font-medium uppercase tracking-wide text-rejected">
        <span className="h-1.5 w-1.5 rounded-full bg-rejected" aria-hidden />
        Insufficient evidence
      </span>
    );
  }

  if (isFullyGrounded) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-card border border-grounded/40 bg-grounded-soft px-2.5 py-1 text-xs font-medium uppercase tracking-wide text-grounded">
        <span className="h-1.5 w-1.5 rounded-full bg-grounded" aria-hidden />
        Fully grounded
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 rounded-card border border-tab/40 bg-tab-soft px-2.5 py-1 text-xs font-medium uppercase tracking-wide text-tab">
      <span className="h-1.5 w-1.5 rounded-full bg-tab" aria-hidden />
      Partially grounded
    </span>
  );
}
