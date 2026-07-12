from src.retrieval.hybrid_retriever import reciprocal_rank_fusion


def test_rrf_favors_docs_ranked_highly_in_both_lists():
    bm25_ranked = ["a", "b", "c"]
    vector_ranked = ["b", "a", "d"]

    fused = reciprocal_rank_fusion([bm25_ranked, vector_ranked])

    # "a" and "b" appear near the top of both lists, so they should outscore
    # "c" and "d", which each appear in only one list.
    assert fused["a"] > fused["c"]
    assert fused["b"] > fused["d"]


def test_rrf_handles_disjoint_lists():
    fused = reciprocal_rank_fusion([["a", "b"], ["c", "d"]])
    assert set(fused.keys()) == {"a", "b", "c", "d"}
    assert fused["a"] == fused["c"]  # both rank 0 in their own list
