"""Citation enforcement: verify that every factual sentence in a generated answer
is (a) tagged with a citation, and (b) the cited chunk_id genuinely exists in the
retrieved evidence set. Optionally (strict mode) verify lexical/semantic overlap
between the sentence and its cited chunk as a lightweight entailment proxy.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.retrieval.types import Evidence

CITATION_TAG_RE = re.compile(r"\[([^\[\]]+?)\]")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")

# Sentences that are purely conversational / refusal boilerplate don't need citations.
NO_CITATION_NEEDED_PATTERNS = [
    r"^i don't have enough information",
    r"^i'm not sure",
    r"^sorry",
]


@dataclass
class SentenceVerdict:
    sentence: str
    cited_chunk_ids: list[str]
    supported: bool
    reason: str = ""


@dataclass
class VerificationResult:
    verdicts: list[SentenceVerdict] = field(default_factory=list)
    cleaned_answer: str = ""
    hallucinated_citations: list[str] = field(default_factory=list)
    is_fully_grounded: bool = True
    was_rejected: bool = False


def _split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return [s.strip() for s in SENTENCE_SPLIT_RE.split(text) if s.strip()]


def _extract_citations(sentence: str) -> list[str]:
    return CITATION_TAG_RE.findall(sentence)


def _strip_citations(sentence: str) -> str:
    return CITATION_TAG_RE.sub("", sentence).strip()


def _needs_no_citation(sentence: str) -> bool:
    lowered = sentence.lower()
    return any(re.match(p, lowered) for p in NO_CITATION_NEEDED_PATTERNS)


def _lexical_overlap_ok(sentence: str, chunk_text: str, min_overlap: float = 0.15) -> bool:
    """Cheap, dependency-free entailment proxy: fraction of sentence content-words
    that appear in the cited chunk. Used only in `strict` mode. For production,
    swap this for a proper NLI / entailment model.
    """
    sent_words = {w for w in re.findall(r"[a-z0-9]+", sentence.lower()) if len(w) > 3}
    if not sent_words:
        return True
    chunk_words = set(re.findall(r"[a-z0-9]+", chunk_text.lower()))
    overlap = len(sent_words & chunk_words) / len(sent_words)
    return overlap >= min_overlap


class CitationEnforcer:
    def __init__(self, policy: str = "strip", strict_entailment: bool = False):
        """
        policy: "strip"  -> remove unsupported sentences from the final answer.
                "reject" -> if ANY sentence is unsupported, reject the whole answer.
        strict_entailment: if True, also check lexical overlap between sentence and
                cited chunk (cheap proxy for "does the chunk actually support this?").
        """
        if policy not in ("strip", "reject"):
            raise ValueError(f"citation_policy must be 'strip' or 'reject', got {policy!r}")
        self.policy = policy
        self.strict_entailment = strict_entailment

    def verify(self, answer: str, evidence: list[Evidence], skip_sentence_check: bool = False) -> VerificationResult:
        valid_chunk_ids = {e.chunk_id for e in evidence}
        chunk_text_by_id = {e.chunk_id: e.text for e in evidence}

        result = VerificationResult()

        cited = _extract_citations(answer)
        hallucinated = [c for c in cited if c not in valid_chunk_ids]
        result.hallucinated_citations = hallucinated

        if skip_sentence_check:
            result.cleaned_answer = answer
            result.is_fully_grounded = len(hallucinated) == 0
            result.was_rejected = False
            return result

        kept_sentences: list[str] = []

        for sentence in _split_sentences(answer):
            if _needs_no_citation(sentence):
                result.verdicts.append(SentenceVerdict(sentence, [], True, "refusal/boilerplate"))
                kept_sentences.append(sentence)
                continue

            s_cited = _extract_citations(sentence)
            s_hallucinated = [c for c in s_cited if c not in valid_chunk_ids]
            result.hallucinated_citations.extend(s_hallucinated)

            s_valid_cited = [c for c in s_cited if c in valid_chunk_ids]

            if not s_cited:
                verdict = SentenceVerdict(sentence, [], False, "no citation present")
            elif not s_valid_cited:
                verdict = SentenceVerdict(sentence, [], False, "all citations hallucinated (not in evidence)")
            elif self.strict_entailment and not any(
                _lexical_overlap_ok(_strip_citations(sentence), chunk_text_by_id[c]) for c in s_valid_cited
            ):
                verdict = SentenceVerdict(sentence, s_valid_cited, False, "low overlap with cited chunk")
            else:
                verdict = SentenceVerdict(sentence, s_valid_cited, True)

            result.verdicts.append(verdict)
            if verdict.supported:
                kept_sentences.append(sentence)

        result.is_fully_grounded = all(v.supported for v in result.verdicts)

        if not result.is_fully_grounded and self.policy == "reject":
            result.was_rejected = True
            result.cleaned_answer = (
                "I don't have enough verifiably-grounded information in the provided "
                "documents to answer this confidently."
            )
        else:
            result.cleaned_answer = " ".join(kept_sentences).strip()
            if not result.cleaned_answer:
                result.cleaned_answer = (
                    "I don't have enough information in the provided documents to answer this."
                )

        return result
