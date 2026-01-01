#!/usr/bin/env python3
"""
Quick vault seeder - populate with 230k chunks from your documents.
"""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

def main():
    from packages.vault.src.vault import Vault
    
    vault_path = repo_root / "vault"
    vault_path.mkdir(exist_ok=True)
    
    print(f"[*] Creating vault at {vault_path}")
    vault = Vault(str(vault_path))
    
    print(f"[*] Seeding from:")
    
    docs_dirs = [
        ("docs", "Documentation"),
        ("KnowledgeTXT", "Knowledge base"),
        ("training_data", "Training data"),
    ]
    
    total_count = 0
    
    for dir_name, label in docs_dirs:
        docs_dir = repo_root / dir_name
        if not docs_dir.exists():
            print(f"  - {label} ({dir_name}): Not found, skipping")
            continue
        
        count = 0
        files = list(docs_dir.glob("*.md")) + list(docs_dir.glob("*.txt")) + list(docs_dir.glob("*.jsonl"))
        
        print(f"  - {label} ({dir_name}): Found {len(files)} files")
        
        for file in files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if len(content) < 10:
                    continue
                
                doc_id = vault.import_text(
                    content,
                    title=file.name,
                    source_path=str(file.relative_to(repo_root))
                )
                count += 1
                total_count += 1
                
                if count % 10 == 0:
                    print(f"    ✓ {count} documents imported from {label}")
            
            except Exception as e:
                print(f"    [!] {file.name}: {e}")
        
        if count > 0:
            print(f"    ✓ Total: {count} documents from {label}")
    
    print(f"\n[✓] Seeding complete: {total_count} total documents imported")
    
    # Show vault stats
    try:
        stats = vault.get_stats()
        print(f"\n[*] Vault stats:")
        print(f"    Chunks: {stats.get('chunk_count', 0)}")
        print(f"    Docs: {stats.get('doc_count', 0)}")
        print(f"    Total size: {stats.get('total_bytes', 0) / 1024 / 1024:.1f}MB")
    except Exception as e:
        print(f"[!] Could not get stats: {e}")

if __name__ == "__main__":
    main()
