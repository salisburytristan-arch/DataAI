import sys
from pathlib import Path
import tempfile

# Ensure 'packages' dir on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.core.src.distillation_writer import DistillationDatasetWriter
from packages.vault.src.vault import Vault

def main():
    with tempfile.TemporaryDirectory() as tmp:
        v = Vault(tmp)
        writer = DistillationDatasetWriter(vault=v)
        # Add a sample training pair for demo
        writer.add_training_pair(
            instruction="Explain capital resilience.",
            completion="Capital resilience ensures buffers and quarterly adjustments.",
            evidence=["Liquidity buffers adjusted quarterly", "Diversified hedging strategies"],
            feedback="Solid baseline; include numeric metrics next time.",
            quality_score=0.85,
            signer_id="audit-verifier",
            source_convo_id="demo-convo-001",
        )
        # Generate frames and export
        writer.generate_frames()
        out = Path(tmp) / "distill.jsonl"
        stats = writer.export_dataset(str(out), quality_threshold=0.8, sign=False)
        print("Exported:", out)
        print("Stats:", stats)
        print("Next: run external training and capture pre/post metrics.")

if __name__ == "__main__":
    main()
