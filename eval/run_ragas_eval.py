"""CI-gated evaluation: runs Ragas metrics against a fixed regression test set and
exits with a non-zero status code (failing the CI job) if any score drops below
its configured threshold.

Usage:
    python eval/run_ragas_eval.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from eval.dataset import build_ragas_dataset

TESTSET_PATH = Path(__file__).parent / "testset" / "sample_qa.json"

# Tune these to your domain. Faithfulness is the most important gate for citation
# enforcement: it measures whether the answer's claims are actually backed by the
# retrieved contexts.
THRESHOLDS = {
    "faithfulness": 0.85,
    "answer_relevancy": 0.80,
    "context_precision": 0.75,
    "context_recall": 0.75,
}


def main() -> int:
    print(f"Loading test set from {TESTSET_PATH} ...")
    data = build_ragas_dataset(TESTSET_PATH)
    dataset = Dataset.from_dict(data)

    print("Running Ragas evaluation (faithfulness, answer_relevancy, context_precision, context_recall) ...")
    results = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )

    scores = results.to_pandas().mean(numeric_only=True).to_dict()

    print("\n=== RAGAS SCORES ===")
    failed = []
    for metric, threshold in THRESHOLDS.items():
        score = scores.get(metric)
        if score is None:
            print(f"  {metric:20s}: MISSING from results")
            failed.append(metric)
            continue

        status = "PASS" if score >= threshold else "FAIL"
        print(f"  {metric:20s}: {score:.3f}  (threshold {threshold:.2f})  [{status}]")
        if score < threshold:
            failed.append(metric)

    if failed:
        print(f"\nCI GATE FAILED: metrics below threshold -> {failed}")
        return 1

    print("\nCI GATE PASSED: all metrics meet threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
