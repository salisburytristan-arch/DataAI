import os
import json
from src import retriever as retr


def _hash_index(idx: dict) -> str:
    return json.dumps(idx, sort_keys=True, ensure_ascii=False)


def test_build_index_deterministic(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    (d / "one.txt").write_text("alpha beta gamma", encoding="utf-8")
    (d / "two.txt").write_text("alpha beta delta", encoding="utf-8")

    os.environ["ACX_TEST_MODE"] = "1"
    os.environ["ACX_SEED"] = "123"

    idx1 = retr.build_index(str(d), max_chars=50)
    idx2 = retr.build_index(str(d), max_chars=50)

    assert _hash_index(idx1) == _hash_index(idx2)


def test_search_repeated_consistent(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    (d / "one.txt").write_text("alpha beta gamma", encoding="utf-8")
    (d / "two.txt").write_text("alpha beta delta", encoding="utf-8")

    os.environ["ACX_TEST_MODE"] = "1"
    os.environ["ACX_SEED"] = "321"

    idx = retr.build_index(str(d), max_chars=50)
    first = retr.search(idx, "alpha", k=4)
    second = retr.search(idx, "alpha", k=4)

    assert first == second
