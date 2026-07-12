"""Run the RAG pipeline over a fixed QA test set and shape the results into the
column format Ragas expects: question, answer, contexts, ground_truth.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.pipeline import RagPipeline


def load_testset(path: str | Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_ragas_dataset(testset_path: str | Path, pipeline: RagPipeline | None = None) -> dict[str, list]:
    pipeline = pipeline or RagPipeline()
    testset = load_testset(testset_path)

    questions, answers, contexts, ground_truths = [], [], [], []

    for item in testset:
        result = pipeline.answer(item["question"])
        questions.append(item["question"])
        answers.append(result.answer)
        contexts.append([e.text for e in result.evidence])
        ground_truths.append(item["ground_truth"])

    return {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }
