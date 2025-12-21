from src import retriever as retr


def test_search_alpha_weighting_changes_order(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.txt").write_text("foo bar", encoding="utf-8")
    (d / "b.txt").write_text("foo baz", encoding="utf-8")
    idx = retr.build_index(str(d), max_chars=50)
    # attach embeddings to favor b
    sidecar = [
        {"path": str(d / "a.txt"), "chunk_id": 0, "embedding": [1.0, 0.0]},
        {"path": str(d / "b.txt"), "chunk_id": 0, "embedding": [0.0, 1.0]},
    ]
    idx = retr.attach_embeddings(idx, str((tmp_path / "emb.json").write_text("")))
    idx["chunks"][0]["embedding"] = [1.0, 0.0]
    idx["chunks"][1]["embedding"] = [0.0, 1.0]

    # alpha=0: BM25 order deterministic by path
    r0 = retr.search(idx, "foo", k=2, alpha=0.0)
    # alpha=0.9: cosine dominates; expect embedding with higher cosine ranks first
    r1 = retr.search(idx, "foo", k=2, query_embedding=[0.0, 1.0], alpha=0.9)

    paths0 = [r["path"] for r in r0]
    paths1 = [r["path"] for r in r1]
    assert paths0 != paths1