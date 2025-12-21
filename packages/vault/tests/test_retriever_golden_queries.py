"""Golden query regression: stable top chunk IDs."""
import json
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.vault import Vault

fixture_path = Path(__file__).parent.parent.parent / "testkit" / "src" / "fixtures" / "corpora" / "golden_queries.json"


def load_fixture():
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_golden_queries_top_chunk_stable():
    fixture = load_fixture()
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        for doc in fixture["docs"]:
            vault.import_text(doc["text"], title=doc["title"], source_path=doc["path"])

        for case in fixture["queries"]:
            results = vault.search(case["query"], limit=3)
            assert results, f"no results for {case['query']}"
            assert results[0]["doc_title"] == case["expect_top_title"]
