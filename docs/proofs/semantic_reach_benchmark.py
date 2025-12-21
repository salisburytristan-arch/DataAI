import sys
from pathlib import Path
import tempfile

# Ensure 'packages' dir on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.vault.src.vault import Vault

def main():
    with tempfile.TemporaryDirectory() as tmp:
        v = Vault(tmp)
        v.import_text(
            "Our treasury policy emphasizes risk mitigation with diversified hedging strategies.",
            title="Risk Policy",
            source_path=str(Path(tmp)/"risk.txt"),
        )
        v.import_text(
            "Liquidity buffers are adjusted quarterly to ensure capital resilience.",
            title="Capital Resilience",
            source_path=str(Path(tmp)/"cap.txt"),
        )
        kw = v.retriever.search_keyword("financial safety", limit=5)
        print("TF-IDF results:", [r["doc_title"] for r in kw])
        hy = v.retriever.search_hybrid("financial safety", limit=5)
        print("Hybrid results:", [(r["doc_title"], r.get("hybrid_score")) for r in hy])
        if not any(r[0] == "Risk Policy" for r in [(r["doc_title"], r.get("hybrid_score")) for r in hy]):
            print("Note: Hybrid did not surface Risk Policy—ensure embeddings enabled and model installed.")

if __name__ == "__main__":
    main()
