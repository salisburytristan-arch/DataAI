#!/usr/bin/env python3
"""
ArcticCodex Studio Launcher - Local & Fly.io Ready

Runs the full conversational chat system with:
- 230k+ chunks from vault
- Real-time streaming chat
- Citations and source attribution
- Conversation persistence
"""

import sys
import os
from pathlib import Path
import subprocess
import argparse

# Add workspace to path
repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

def run_studio_local(port=8000, vault_path=None, embeddings=True):
    """Run studio locally for development."""
    if vault_path is None:
        vault_path = repo_root / "vault"
    
    print(f"[*] Starting ArcticCodex Studio")
    print(f"    Vault: {vault_path}")
    print(f"    Port: {port}")
    print(f"    Embeddings: {'enabled' if embeddings else 'disabled'}")
    
    vault_path.mkdir(exist_ok=True)
    
    # Run studio server
    cmd = [
        sys.executable,
        "-m",
        "packages.studio.src.studio_server_fly",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--vault", str(vault_path),
    ]
    
    print(f"\n[*] Running: {' '.join(cmd)}\n")
    try:
        subprocess.run(cmd, cwd=str(repo_root))
    except KeyboardInterrupt:
        print("\n[*] Studio stopped")

def run_studio_fly():
    """Deploy to Fly.io."""
    print("[*] Deploying ArcticCodex to Fly.io")
    
    # Check if Fly CLI is installed
    try:
        subprocess.run(["fly", "version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[!] Fly CLI not found. Install from: https://fly.io/docs/hands-on/install-flyctl/")
        return 1
    
    # Check if app exists
    print("[*] Checking if Fly app exists...")
    result = subprocess.run(
        ["fly", "status"],
        cwd=str(repo_root),
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("[!] App does not exist. Creating it now...")
        print("\n[*] Run these commands to set up Fly app:\n")
        print("1. Create the app:")
        print("   fly apps create arcticcodex-studio --org personal\n")
        print("2. Create persistent volumes:")
        print("   fly volumes create vault_data --size 10 --region iad")
        print("   fly volumes create models_data --size 20 --region iad\n")
        print("3. Deploy:")
        print("   fly deploy --dockerfile Dockerfile.fly-prod\n")
        print("Or run these commands automatically? (y/n): ", end="")
        
        try:
            response = input().lower().strip()
        except (EOFError, KeyboardInterrupt):
            response = "n"
        
        if response == "y":
            # Create app
            print("\n[*] Creating app...")
            result = subprocess.run(
                ["fly", "apps", "create", "arcticcodex-studio"],
                cwd=str(repo_root)
            )
            if result.returncode != 0:
                print("[!] Failed to create app")
                return 1
            
            # Create volumes
            print("\n[*] Creating vault_data volume...")
            result = subprocess.run(
                ["fly", "volumes", "create", "vault_data", "--size", "10", "--region", "iad"],
                cwd=str(repo_root)
            )
            if result.returncode != 0:
                print("[!] Failed to create vault_data volume")
                return 1
            
            print("\n[*] Creating models_data volume...")
            result = subprocess.run(
                ["fly", "volumes", "create", "models_data", "--size", "20", "--region", "iad"],
                cwd=str(repo_root)
            )
            if result.returncode != 0:
                print("[!] Failed to create models_data volume")
                return 1
        else:
            print("\n[*] Please run the commands above manually, then try 'python run_studio.py fly' again.")
            return 1
    
    # Deploy
    cmd = [
        "fly",
        "deploy",
        "--dockerfile", "Dockerfile.fly-prod"
    ]
    
    print(f"\n[*] Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=str(repo_root))
    
    if result.returncode == 0:
        print("\n[✓] Deployment successful!")
        print("[*] Monitor logs with: fly logs")
        print("[*] View at: fly open")
    else:
        print("[!] Deployment failed")
        print("[*] Check logs with: fly logs")
    
    return result.returncode

def seed_vault_local(vault_path=None):
    """Seed local vault with documents."""
    if vault_path is None:
        vault_path = repo_root / "vault"
    
    print(f"[*] Seeding vault from docs...")
    
    try:
        from packages.vault.src.vault import Vault
        
        vault = Vault(str(vault_path))
        
        docs_dirs = [
            repo_root / "docs",
            repo_root / "KnowledgeTXT",
            repo_root / "training_data"
        ]
        
        count = 0
        for docs_dir in docs_dirs:
            if not docs_dir.exists():
                continue
            
            for file in docs_dir.glob("*"):
                if file.suffix not in [".md", ".txt", ".jsonl"]:
                    continue
                
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    doc_id = vault.import_text(
                        content,
                        title=file.name,
                        source_path=str(file.relative_to(repo_root))
                    )
                    
                    count += 1
                    print(f"  ✓ {file.name} ({doc_id[:8]}...)")
                
                except Exception as e:
                    print(f"  [!] {file.name}: {e}")
        
        print(f"\n[✓] Imported {count} documents")
        
        # Show stats
        try:
            stats = vault.get_stats()
            print(f"[*] Vault stats:")
            print(f"    Chunks: {stats.get('chunk_count', 0)}")
            print(f"    Docs: {stats.get('doc_count', 0)}")
        except:
            pass
        
    except Exception as e:
        print(f"[!] Failed to seed vault: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

def main():
    parser = argparse.ArgumentParser(
        description="ArcticCodex Studio Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run locally on port 8000
  python run_studio.py local
  
  # Deploy to Fly.io
  python run_studio.py fly
  
  # Seed vault first, then run
  python run_studio.py seed && python run_studio.py local
        """
    )
    
    parser.add_argument(
        "command",
        choices=["local", "fly", "seed"],
        help="Command to run"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for local server (default: 8000)"
    )
    
    parser.add_argument(
        "--vault",
        type=str,
        help="Path to vault directory"
    )
    
    parser.add_argument(
        "--no-embeddings",
        action="store_true",
        help="Disable embeddings"
    )
    
    args = parser.parse_args()
    
    if args.command == "local":
        return run_studio_local(
            port=args.port,
            vault_path=args.vault and Path(args.vault),
            embeddings=not args.no_embeddings
        )
    
    elif args.command == "fly":
        return run_studio_fly()
    
    elif args.command == "seed":
        return seed_vault_local(args.vault and Path(args.vault))

if __name__ == "__main__":
    sys.exit(main())
