import os
from src import retriever as retr


def test_bm25_prefers_term_frequency(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    (root / "a.txt").write_text("alpha beta alpha", encoding="utf-8")
    (root / "b.txt").write_text("beta gamma", encoding="utf-8")

    idx = retr.build_index(str(root))
    results = retr.search(idx, "alpha", k=2)
    assert results[0]["path"].endswith("a.txt")


def test_attach_embeddings_and_cosine(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    (root / "a.txt").write_text("alpha beta", encoding="utf-8")
    idx = retr.build_index(str(root))
    emb_path = tmp_path / "emb.json"
    import json
    emb_data = [{"path": str(root / "a.txt"), "chunk_id": 0, "embedding": [1, 0]}]
    emb_path.write_text(json.dumps(emb_data), encoding="utf-8")
    idx = retr.attach_embeddings(idx, str(emb_path))
    results = retr.search(idx, "alpha", k=1, query_embedding=[1, 0], alpha=0.5)
    assert results and results[0]["score"] > 0