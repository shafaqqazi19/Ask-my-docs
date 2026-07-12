"""Extractive answer builder — constructs answers directly from retrieved evidence
without calling an LLM. Fast, always grounded, never hallucinates."""

from __future__ import annotations

import re

from src.retrieval.types import Evidence


def _fmt(text: str, max_chars: int = 500) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[-]{3,}", "", text)
    text = re.sub(r"\*+", "", text)
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    break_at = max(truncated.rfind(". "), truncated.rfind(".\n"), truncated.rfind("? "))
    if break_at > max_chars // 2:
        truncated = truncated[: break_at + 1]
    return truncated


class Generator:
    def __init__(self, max_chars: int = 500):
        self.max_chars = max_chars

    def generate_answer(self, question: str, evidence: list[Evidence]) -> str:
        if not evidence:
            return "I don't have enough information in the provided documents to answer this."

        parts: list[str] = []
        seen_keys: set[str] = set()

        for e in evidence:
            snippet = _fmt(e.text, max_chars=self.max_chars)
            key = snippet[:60]
            if key in seen_keys:
                continue
            seen_keys.add(key)
            parts.append(f"From {e.doc_id}:\n{snippet}  [{e.chunk_id}]")
            if len(parts) >= 3:
                break

        return "\n\n".join(parts)
