#!/usr/bin/env python
"""Quick launcher for ArcticCodex Studio.

Usage:
    python launch_studio.py [--port 8080] [--vault ./vault] [--open]

Opens Studio at http://localhost:8080 with your vault loaded.
"""

import sys
import os
import argparse
import webbrowser
import time
from pathlib import Path

# Add packages to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

from packages.studio.src.studio_server import start_studio
from packages.vault.src.vault import Vault


def main():
    parser = argparse.ArgumentParser(
        description="Launch ArcticCodex Studio web interface"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to run Studio on (default: 8080)"
    )
    parser.add_argument(
        "--vault",
        default="./vault",
        help="Path to vault directory (default: ./vault)"
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open browser automatically"
    )
    parser.add_argument(
        "--convo",
        default="studio-session",
        help="Conversation ID to track facts (default: studio-session)"
    )
    
    args = parser.parse_args()
    
    # Load vault
    vault_path = Path(args.vault)
    if not vault_path.exists():
        print(f"ERROR: Vault not found at {vault_path}")
        print(f"Please ensure vault directory exists or use --vault option")
        sys.exit(1)
    
    print(f"Loading vault from: {vault_path}")
    vault = Vault(data_dir=str(vault_path))
    
    print(f"\n{'='*60}")
    print(f"ArcticCodex Studio MVP")
    print(f"{'='*60}")
    print(f"Vault location: {vault_path.resolve()}")
    print(f"Server starting on: http://localhost:{args.port}")
    print(f"Conversation ID: {args.convo}")
    print(f"\nPress Ctrl+C to stop the server")
    print(f"{'='*60}\n")
    
    # Start server in threaded mode
    server_thread = start_studio(
        vault=vault,
        agent=None,  # Optional: can pass agent instance here
        convo_id=args.convo,
        port=args.port,
        threaded=True
    )
    
    # Give server time to start
    time.sleep(1)
    
    # Open browser if requested
    if args.open:
        url = f"http://localhost:{args.port}"
        print(f"Opening {url} in browser...")
        webbrowser.open(url)
    
    # Keep server running
    try:
        if server_thread:
            server_thread.join()
        else:
            # If not threaded, this won't return
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down Studio...")
        sys.exit(0)


if __name__ == "__main__":
    main()
