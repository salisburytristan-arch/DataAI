import os
from src import retriever as retr


def test_search_deterministic_order(tmp_path):
    # Prepare temp docs
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.txt").write_text("alpha beta gamma", encoding="utf-8")
    (d / "b.txt").write_text("alpha beta delta", encoding="utf-8")

    os.environ["ACX_TEST_MODE"] = "1"
    os.environ["ACX_SEED"] = "42"

    idx = retr.build_index(str(d), max_chars=100)
    results = retr.search(idx, "alpha", k=5)
    paths = [r["path"] for r in results]
    # Deterministic tie-break should order by path when scores tie
    assert paths == sorted(paths)
