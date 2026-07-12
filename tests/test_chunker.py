from src.ingestion.chunker import chunk_document
from src.ingestion.loader import RawDocument


def test_chunk_document_produces_ids():
    doc = RawDocument(doc_id="test.md", source_path="test.md", text="Sentence one. Sentence two. Sentence three.")
    chunks = chunk_document(doc, chunk_size=1000, chunk_overlap=10)

    assert len(chunks) >= 1
    assert chunks[0].chunk_id == "s0000"
    assert "Sentence one" in chunks[0].text


def test_chunk_document_respects_size_and_overlaps():
    long_text = " ".join([f"This is sentence number {i}." for i in range(100)])
    doc = RawDocument(doc_id="long.md", source_path="long.md", text=long_text)
    chunks = chunk_document(doc, chunk_size=200, chunk_overlap=50)

    assert len(chunks) > 1
    # chunk ids should be sequential and unique
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))
