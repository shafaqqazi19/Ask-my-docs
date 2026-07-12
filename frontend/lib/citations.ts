export type AnswerSegment =
  | { type: "text"; content: string }
  | { type: "citation"; chunkId: string };

const CITATION_RE = /\[([^\[\]]+?)\]/g;

/**
 * Splits generated answer text into alternating plain-text and citation
 * segments, e.g. "Refunds take 14 days [doc.md::chunk-1]." becomes
 * [{type:"text", content:"Refunds take 14 days "}, {type:"citation", chunkId:"doc.md::chunk-1"}, {type:"text", content:"."}]
 */
export function parseAnswerSegments(answer: string): AnswerSegment[] {
  const segments: AnswerSegment[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  CITATION_RE.lastIndex = 0;
  while ((match = CITATION_RE.exec(answer)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: "text", content: answer.slice(lastIndex, match.index) });
    }
    segments.push({ type: "citation", chunkId: match[1] });
    lastIndex = CITATION_RE.lastIndex;
  }

  if (lastIndex < answer.length) {
    segments.push({ type: "text", content: answer.slice(lastIndex) });
  }

  return segments;
}

/** DOM-safe id for scrolling/highlighting the evidence card matching a chunk_id. */
export function evidenceDomId(chunkId: string): string {
  return `evidence-${encodeURIComponent(chunkId)}`;
}
