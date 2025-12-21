import argparse
import os
import sys
from pathlib import Path

# Ensure workspace root on path for sibling package imports
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Add packages/core/src to path for phase imports
CORE_SRC = Path(__file__).resolve().parent
if str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))

from packages.vault.src.vault import Vault
from packages.core.src.agent import Agent
from packages.core.src.llm.llama_client import HttpLLM, MockLLM


def main() -> None:
    parser = argparse.ArgumentParser(prog="arctic-agent", description="ArcticCodex Agent CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    chat = sub.add_parser("chat", help="Interactive chat with Vault-backed agent")
    chat.add_argument("--vault", required=True, help="Path to vault directory")
    chat.add_argument("--endpoint", required=False, help="LLM HTTP endpoint (e.g., http://localhost:8000)")
    chat.add_argument("--persist", action="store_true", help="Persist responses as summaries in Vault")
    chat.add_argument("--convo", required=False, help="Conversation ID to group summaries")
    chat.add_argument("--embeddings", choices=["on","off"], required=False, help="Enable or disable embeddings for this run")
    chat.add_argument("--embedding-model", required=False, help="Override embeddings model (e.g., sentence-transformers/all-MiniLM-L6-v2)")

    exp = sub.add_parser("export", help="Export conversation summaries+facts to JSONL")
    exp.add_argument("--vault", required=True, help="Path to vault directory")
    exp.add_argument("--convo", required=True, help="Conversation ID to export")
    exp.add_argument("--out", required=True, help="Output JSONL path")

    exp_fn = sub.add_parser("export-fn", help="Export conversation to ForgeNumerics frames (.fn.jsonl)")
    exp_fn.add_argument("--vault", required=True, help="Path to vault directory")
    exp_fn.add_argument("--convo", required=True, help="Conversation ID to export")
    exp_fn.add_argument("--out", required=True, help="Output .fn.jsonl path")

    imp_fn = sub.add_parser("import-fn", help="Import ForgeNumerics frames into Vault")
    imp_fn.add_argument("--vault", required=True, help="Path to vault directory")
    imp_fn.add_argument("--file", required=True, help="Input .fn.jsonl file path")

    phase = sub.add_parser("phase", help="Run a Project Omega phase (26-40)")
    phase.add_argument("--num", type=int, required=True, help="Phase number (26-40)")
    phase.add_argument("--all", action="store_true", help="Run all phases sequentially")
    phase.add_argument("--export", required=False, help="Export all phase frames to file (JSONL)")

    args = parser.parse_args()

    if args.cmd == "chat":
        # Apply per-run embeddings configuration via env vars
        if getattr(args, "embeddings", None):
            os.environ["ACX_EMBEDDINGS"] = "1" if args.embeddings == "on" else "0"
        if getattr(args, "embedding_model", None):
            os.environ["ACX_EMBEDDINGS_MODEL"] = args.embedding_model
        vault = Vault(args.vault)
        llm = None
        endpoint = args.endpoint or os.environ.get("AC_LLM_ENDPOINT")
        if endpoint:
            try:
                llm = HttpLLM(endpoint)
                print(f"Using LLM endpoint: {endpoint}")
            except Exception:
                print("Failed to initialize HTTP LLM; falling back to MockLLM")
        agent = Agent(vault, llm=llm or MockLLM())
        print("Type your question. Type 'exit' to quit.")
        while True:
            try:
                q = input("> ").strip()
            except EOFError:
                break
            if not q:
                continue
            if q.lower() in {"exit", "quit"}:
                break
            res = agent.respond(q, evidence_limit=5, persist=bool(args.persist), convo_id=args.convo)
            print("\n" + res["text"]) 
            if res.get("citations"):
                print("\nCitations:")
                for c in res["citations"]:
                    print(f"- {c.get('doc_title','?')} chunk={c.get('chunk_id','?')} offset={c.get('offset','?')}")
            if res.get("persist"):
                p = res["persist"]
                print(f"\nSaved summary: {p.get('summary_id')} (convo {p.get('convo_id')})")
            print("")
        # Cleanup any env overrides to avoid leaking to parent environment
        if "ACX_EMBEDDINGS" in os.environ:
            del os.environ["ACX_EMBEDDINGS"]
        if "ACX_EMBEDDINGS_MODEL" in os.environ:
            del os.environ["ACX_EMBEDDINGS_MODEL"]
    elif args.cmd == "export":
        from packages.core.src.export import export_conversation
        vault = Vault(args.vault)
        stats = export_conversation(vault, args.convo, args.out)
        print(f"Exported {stats['summaries']} summaries and {stats['facts']} facts to {stats['path']}")
    elif args.cmd == "export-fn":
        from packages.core.src.fn_bridge import export_conversation_fn
        vault = Vault(args.vault)
        frames = export_conversation_fn(vault, args.convo)
        from pathlib import Path
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            for s in frames:
                f.write(s + "\n")
        print(f"Exported {len(frames)} ForgeNumerics frames to {out}")
    elif args.cmd == "import-fn":
        vault = Vault(args.vault)
        from pathlib import Path
        imported = 0
        with open(args.file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rec_id = vault.import_fn_frame(line)
                    imported += 1
        print(f"Imported {imported} frames into Vault")
    elif args.cmd == "phase":
        from phase_manager import PhaseManager
        manager = PhaseManager()
        if args.all:
            print("Running all phases (26-40)...")
            results = manager.run_all_phases()
            success_count = sum(1 for r in results.values() if r.get("status") == "COMPLETE")
            print(f"✓ Completed {success_count}/{len(results)} phases")
            if args.export:
                frames = manager.export_all_frames()
                Path(args.export).parent.mkdir(parents=True, exist_ok=True)
                with open(args.export, "w") as f:
                    for frame in frames:
                        f.write(frame + "\n")
                print(f"Exported {len(frames)} frames to {args.export}")
        else:
            phase_num = args.num
            print(f"Running phase {phase_num}...")
            result = manager.run_phase(phase_num)
            print(f"Status: {result.get('status')}")
            print(f"Frames: {len(result.get('frames', []))}")
            for frame in result.get("frames", []):
                print(frame)


if __name__ == "__main__":
    main()
