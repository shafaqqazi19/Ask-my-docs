"""Split documents into overlapping chunks with stable, citeable chunk IDs."""
from __future__ import annotations

import re
from dataclasses import dataclass

from src.ingestion.loader import RawDocument


@dataclass
class Chunk:
    chunk_id: str          # e.g. "policy.md::chunk-0003" -- this is what gets cited
    doc_id: str
    text: str
    position: int


def _split_sentences(text: str) -> list[str]:
    # Lightweight sentence splitter; avoids an NLTK punkt download requirement.
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", text)
    return [p.strip() for p in parts if p.strip()]


_global_pos = 0


def chunk_document(doc: RawDocument, chunk_size: int = 800, chunk_overlap: int = 120) -> list[Chunk]:
    """Sentence-aware sliding window chunker.

    Packs sentences into windows of ~chunk_size characters, overlapping the last
    `chunk_overlap` characters' worth of sentences into the next chunk so context
    isn't lost at boundaries.
    """
    global _global_pos
    sentences = _split_sentences(doc.text)
    chunks: list[Chunk] = []

    current: list[str] = []
    current_len = 0
    position = 0

    def flush(carry_over: list[str] | None = None):
        nonlocal current, current_len, position
        global _global_pos
        if current:
            chunk_text = " ".join(current)
            chunk_id = f"s{_global_pos:04d}"
            chunks.append(Chunk(chunk_id=chunk_id, doc_id=doc.doc_id, text=chunk_text, position=position))
            _global_pos += 1
            position += 1
        current = carry_over or []
        current_len = sum(len(s) for s in current)

    for sentence in sentences:
        if current_len + len(sentence) > chunk_size and current:
            overlap: list[str] = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) > chunk_overlap:
                    break
                overlap.insert(0, s)
                overlap_len += len(s)
            flush(carry_over=overlap)

        current.append(sentence)
        current_len += len(sentence)

    flush()
    return chunks


def chunk_documents(docs: list[RawDocument], chunk_size: int = 800, chunk_overlap: int = 120) -> list[Chunk]:
    global _global_pos
    _global_pos = 0
    all_chunks: list[Chunk] = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc, chunk_size=chunk_size, chunk_overlap=chunk_overlap))
    return all_chunks
