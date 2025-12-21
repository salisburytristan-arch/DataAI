import json
import math
from src import retriever as retr


def _norm(vec):
    return math.sqrt(sum(x * x for x in vec))


def test_build_hash_embeddings_shape_and_norm(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    (d / "one.txt").write_text("alpha beta gamma", encoding="utf-8")
    idx = retr.build_index(str(d), max_chars=50)
    emb = retr.build_hash_embeddings(idx, dim=16)
    assert len(emb) == len(idx["chunks"])
    for item in emb:
        vec = item["embedding"]
        assert len(vec) == 16
        n = _norm(vec)
        assert abs(n - 1.0) < 1e-6 or n == 0.0  # zero only if no tokens


def test_attach_embeddings_merges_sidecar(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    (d / "one.txt").write_text("alpha beta gamma", encoding="utf-8")
    idx = retr.build_index(str(d), max_chars=50)
    sidecar = []
    for ch in idx["chunks"]:
        sidecar.append({"path": ch["path"], "chunk_id": ch["chunk_id"], "embedding": [0.1, 0.2]})
    sc_path = tmp_path / "emb.json"
    sc_path.write_text(json.dumps(sidecar), encoding="utf-8")

    merged = retr.attach_embeddings(idx, str(sc_path))
    for ch in merged["chunks"]:
        assert "embedding" in ch
        assert ch["embedding"] == [0.1, 0.2]