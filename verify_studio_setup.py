#!/usr/bin/env python3
"""
ArcticCodex Studio - Deployment Verification

Checks that all components are ready for local or Fly deployment.
"""

import sys
import os
from pathlib import Path
import json

repo_root = Path(__file__).resolve().parent

def check_files():
    """Check required files exist."""
    print("\n[CHECK] Required Files")
    print("=" * 50)
    
    files = {
        "Dockerfile.fly-prod": "Production Docker image",
        "fly.toml": "Fly.io configuration",
        "packages/studio/src/studio_server_fly.py": "Studio server",
        "packages/studio/web/app.js": "Chat UI",
        "packages/vault/src/vault.py": "Vault implementation",
        "packages/core/src/agent.py": "Agent + LLM interface",
        "run_studio.py": "Studio launcher",
    }
    
    all_ok = True
    for file_path, description in files.items():
        full_path = repo_root / file_path
        exists = full_path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path:50} {description}")
        if not exists:
            all_ok = False
    
    return all_ok

def check_python_packages():
    """Check Python dependencies."""
    print("\n[CHECK] Python Packages")
    print("=" * 50)
    
    packages = [
        ("pathlib", "Standard library"),
        ("json", "Standard library"),
        ("http.server", "Standard library"),
    ]
    
    all_ok = True
    for package, description in packages:
        try:
            __import__(package)
            status = "✓"
        except ImportError:
            status = "✗"
            all_ok = False
        
        print(f"  {status} {package:30} {description}")
    
    print(f"  ⚠ sentence_transformers              Embeddings (installed via requirements.txt)")
    
    return all_ok

def check_directories():
    """Check directory structure."""
    print("\n[CHECK] Directory Structure")
    print("=" * 50)
    
    dirs = {
        "packages/studio": "Studio server + UI",
        "packages/vault": "Vault implementation",
        "packages/core": "Agent runtime",
        "docs": "Documentation (optional)",
        "KnowledgeTXT": "Knowledge base (optional)",
        "training_data": "Training data (optional)",
    }
    
    all_ok = True
    for dir_path, description in dirs.items():
        full_path = repo_root / dir_path
        exists = full_path.exists()
        status = "✓" if exists else "⚠" if "optional" in description else "✗"
        print(f"  {status} {dir_path:30} {description}")
        if not exists and "✗" == status:
            all_ok = False
    
    return all_ok

def check_vault():
    """Check vault status."""
    print("\n[CHECK] Vault Status")
    print("=" * 50)
    
    vault_path = repo_root / "vault"
    
    if not vault_path.exists():
        print(f"  ⚠ Vault not created yet at {vault_path}")
        print(f"    Run: python run_studio.py seed")
        return True  # Not an error, just not seeded
    
    # Count chunks
    chunks = 0
    try:
        from packages.vault.src.vault import Vault
        v = Vault(str(vault_path))
        stats = v.get_stats()
        chunks = stats.get("chunk_count", 0)
        docs = stats.get("doc_count", 0)
        
        print(f"  ✓ Vault found at {vault_path}")
        print(f"    Documents: {docs}")
        print(f"    Chunks: {chunks}")
        
        if chunks == 0:
            print(f"  ⚠ Vault is empty. Run: python run_studio.py seed")
        
        return True
    
    except Exception as e:
        print(f"  ✗ Error checking vault: {e}")
        return False

def check_config():
    """Check configuration files."""
    print("\n[CHECK] Configuration")
    print("=" * 50)
    
    # Check fly.toml
    fly_path = repo_root / "fly.toml"
    if fly_path.exists():
        with open(fly_path) as f:
            content = f.read()
        
        checks = {
            "arcticcodex-studio": "App name set",
            "Dockerfile.fly-prod": "Docker image configured",
            "16gb": "RAM allocation (16GB)",
            "vault_data": "Vault volume mount",
        }
        
        print("  fly.toml:")
        for key, desc in checks.items():
            has_key = key.lower() in content.lower()
            status = "✓" if has_key else "✗"
            print(f"    {status} {desc}")
    
    return True

def main():
    """Run all checks."""
    print("\n" + "=" * 50)
    print("ArcticCodex Studio - Deployment Verification")
    print("=" * 50)
    
    checks = [
        ("Files", check_files),
        ("Python Packages", check_python_packages),
        ("Directories", check_directories),
        ("Configuration", check_config),
        ("Vault", check_vault),
    ]
    
    results = []
    for name, check_fn in checks:
        try:
            result = check_fn()
            results.append((name, result))
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    all_ok = all(result for _, result in results)
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
    
    print("\n" + "=" * 50)
    
    if all_ok:
        print("\n✓ All checks passed! Ready to deploy.")
        print("\nNext steps:")
        print("  1. Seed vault:      python run_studio.py seed")
        print("  2. Run locally:     python run_studio.py local")
        print("  3. Deploy to Fly:   python run_studio.py fly")
        return 0
    else:
        print("\n✗ Some checks failed. Please review above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
