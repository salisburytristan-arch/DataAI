import os
import shutil
from typing import Dict, Any


def vault_ingest(path: str) -> Dict[str, Any]:
    """Stub: Ingest files from a directory into the Vault.

    For now, counts files; real implementation would normalize/chunk/index.
    """
    count = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            count += 1
    return {"ingested_files": count, "source": os.path.abspath(path)}


def vault_reindex(store_path: str) -> Dict[str, Any]:
    """Stub: Rebuild indices for the Vault store."""
    return {"reindexed": True, "store": os.path.abspath(store_path)}


def vault_verify(store_path: str) -> Dict[str, Any]:
    """Stub: Verify integrity (hashes/manifests)."""
    return {"verified": True, "store": os.path.abspath(store_path)}


def vault_snapshot(store_path: str, out_dir: str) -> Dict[str, Any]:
    """Create a simple snapshot (directory copy)."""
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "vault_snapshot")
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(store_path, dest)
    return {"snapshot_path": os.path.abspath(dest)}


def vault_restore(snapshot_path: str, store_path: str) -> Dict[str, Any]:
    """Restore snapshot back to store path."""
    if os.path.exists(store_path):
        shutil.rmtree(store_path)
    shutil.copytree(snapshot_path, store_path)
    return {"restored": os.path.abspath(store_path)}
