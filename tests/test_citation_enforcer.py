from src.generation.citation_enforcer import CitationEnforcer
from src.retrieval.types import Evidence


def make_evidence():
    return [
        Evidence(chunk_id="doc.md::chunk-0001", doc_id="doc.md", text="Refunds are issued within 14 days.", score=1.0),
        Evidence(chunk_id="doc.md::chunk-0002", doc_id="doc.md", text="Digital goods are non-refundable after download.", score=0.9),
    ]


def test_fully_cited_answer_is_kept_and_grounded():
    enforcer = CitationEnforcer(policy="strip")
    answer = "Refunds are issued within 14 days [doc.md::chunk-0001]."
    result = enforcer.verify(answer, make_evidence())

    assert result.is_fully_grounded
    assert "14 days" in result.cleaned_answer
    assert not result.hallucinated_citations


def test_uncited_sentence_is_stripped_in_strip_mode():
    enforcer = CitationEnforcer(policy="strip")
    answer = (
        "Refunds are issued within 14 days [doc.md::chunk-0001]. "
        "The company was founded in 1999."  # no citation -> unsupported
    )
    result = enforcer.verify(answer, make_evidence())

    assert not result.is_fully_grounded
    assert "1999" not in result.cleaned_answer
    assert "14 days" in result.cleaned_answer


def test_hallucinated_citation_is_detected():
    enforcer = CitationEnforcer(policy="strip")
    answer = "Refunds take 30 days [doc.md::chunk-9999]."
    result = enforcer.verify(answer, make_evidence())

    assert not result.is_fully_grounded
    assert "doc.md::chunk-9999" in result.hallucinated_citations
    assert result.cleaned_answer == "I don't have enough information in the provided documents to answer this."


def test_reject_policy_rejects_whole_answer_on_any_unsupported_sentence():
    enforcer = CitationEnforcer(policy="reject")
    answer = (
        "Refunds are issued within 14 days [doc.md::chunk-0001]. "
        "Unsupported claim with no citation."
    )
    result = enforcer.verify(answer, make_evidence())

    assert result.was_rejected
    assert "insufficient" in result.cleaned_answer.lower() or "grounded" in result.cleaned_answer.lower()


def test_refusal_sentence_needs_no_citation():
    enforcer = CitationEnforcer(policy="reject")
    answer = "I don't have enough information in the provided documents to answer this."
    result = enforcer.verify(answer, make_evidence())

    assert result.is_fully_grounded
    assert not result.was_rejected
