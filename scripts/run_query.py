"""CLI: ask a single question against the built index.

Usage:
    python scripts/run_query.py "What is the refund policy for digital goods?"
"""
from __future__ import annotations

import argparse
import json

from src.pipeline import RagPipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question", help="Question to ask")
    parser.add_argument("--show-evidence", action="store_true", help="Print retrieved evidence chunks")
    args = parser.parse_args()

    pipeline = RagPipeline()
    result = pipeline.answer(args.question)

    print("\n=== ANSWER ===")
    print(result.answer)

    v = result.verification
    print("\n=== GROUNDING ===")
    print(json.dumps({
        "is_fully_grounded": v.is_fully_grounded,
        "was_rejected": v.was_rejected,
        "hallucinated_citations": v.hallucinated_citations,
    }, indent=2))

    if args.show_evidence:
        print("\n=== EVIDENCE ===")
        for e in result.evidence:
            print(f"[{e.chunk_id}] (score={e.score:.3f})\n{e.text}\n")


if __name__ == "__main__":
    main()
