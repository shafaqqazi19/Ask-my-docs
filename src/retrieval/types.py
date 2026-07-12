"""Lightweight shared dataclasses used across retrieval/generation, kept dependency-free
so modules like the citation enforcer can be imported/tested without pulling in
faiss / sentence-transformers.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Evidence:
    chunk_id: str
    doc_id: str
    text: str
    score: float
