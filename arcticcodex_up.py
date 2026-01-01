"""
ArcticCodex Platform Launcher - One-Command Startup

Usage:
    python arcticcodex_up.py        # Start platform
    python arcticcodex_up.py --validate-only  # Just validate, don't start
"""

import sys
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict
import json
import os
import socket


class PlatformLauncher:
    """One-command platform startup with validation"""
    
    def __init__(self, vault_dir: str = "./vault_data", api_port: int = 8000):
        self.vault_dir = Path(vault_dir)
        self.api_port = api_port
        self.checks_passed = []
        self.checks_failed = []
    
    def check_python_version(self) -> bool:
        """Check Python >= 3.10"""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 10:
            self.checks_passed.append(f"Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.checks_failed.append(f"Python 3.10+ required (found {version.major}.{version.minor})")
            return False
    
    def check_vault_dir(self) -> bool:
        """Check vault directory exists or can be created"""
        try:
            self.vault_dir.mkdir(parents=True, exist_ok=True)
            self.checks_passed.append(f"Vault directory: {self.vault_dir}")
            return True
        except Exception as e:
            self.checks_failed.append(f"Cannot create vault directory: {e}")
            return False
    
    def check_port_available(self) -> bool:
        """Check if API port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', self.api_port))
            self.checks_passed.append(f"Port {self.api_port} available")
            return True
        except OSError:
            self.checks_failed.append(f"Port {self.api_port} already in use")
            return False
    
    def check_core_imports(self) -> bool:
        """Check core packages can be imported"""
        try:
            from packages.core.src import auth, tool_policies, uncertainty, audit_stream
            from packages.vault.src.vault import Vault
            self.checks_passed.append("Core packages importable")
            return True
        except ImportError as e:
            self.checks_failed.append(f"Import error: {e}")
            return False
    
    def init_vault(self) -> bool:
        """Initialize vault structure"""
        try:
            # Create vault subdirectories
            (self.vault_dir / "chunks").mkdir(parents=True, exist_ok=True)
            (self.vault_dir / "metadata").mkdir(parents=True, exist_ok=True)
            (self.vault_dir / "logs").mkdir(parents=True, exist_ok=True)
            (self.vault_dir / "auth_data").mkdir(parents=True, exist_ok=True)
            
            # Create marker
            marker = self.vault_dir / ".vault_initialized"
            if not marker.exists():
                marker.write_text(json.dumps({
                    "initialized_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "version": "1.0"
                }))
            
            self.checks_passed.append("Vault initialized")
            return True
        except Exception as e:
            self.checks_failed.append(f"Vault init failed: {e}")
            return False
    
    def validate(self) -> bool:
        """Run all validation checks"""
        print("🔍 Validating ArcticCodex Platform...\n")
        
        checks = [
            self.check_python_version(),
            self.check_vault_dir(),
            self.check_port_available(),
            self.check_core_imports(),
            self.init_vault()
        ]
        
        print("\n✅ Passed:")
        for check in self.checks_passed:
            print(f"   • {check}")
        
        if self.checks_failed:
            print("\n❌ Failed:")
            for check in self.checks_failed:
                print(f"   • {check}")
        
        return all(checks)
    
    def up(self) -> int:
        """
        Start the platform.
        Returns exit code (0=success).
        """
        print("=" * 70)
        print("  🚀 ArcticCodex Platform Launcher")
        print("  Version 1.0 - Enterprise AI with Φ-State Reasoning")
        print("=" * 70)
        print()
        
        # Validate
        if not self.validate():
            print("\n❌ Validation failed. Cannot start platform.")
            return 1
        
        # In production, would start FastAPI + Studio
        print("\n" + "=" * 70)
        print("  ✅ ArcticCodex Platform Ready")
        print("=" * 70)
        print(f"\n  📦 Vault:  {self.vault_dir}")
        print(f"  🔌 API:    http://localhost:{self.api_port} (ready to start)")
        print(f"  🎨 Studio: http://localhost:3000 (ready to start)")
        print("\n  💡 Next steps:")
        print("     • Run: uvicorn packages.core.src.api:app --port 8000")
        print("     • Run: cd arctic-site && npm run dev")
        print("     • Optional: LLM server → python packages/core/src/llm_server.py (port 8001)")
        print("       Set: AC_LLM_ENDPOINT=http://localhost:8001 and AC_GGUF_MODEL=path/to/model.gguf")
        print("     • Or use Docker: docker-compose up")
        print()
        
        return 0


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="ArcticCodex Platform Launcher"
    )
    parser.add_argument(
        '--vault-dir',
        default='./vault_data',
        help='Vault directory path'
    )
    parser.add_argument(
        '--api-port',
        type=int,
        default=8000,
        help='API server port'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only run validation, do not start'
    )
    
    args = parser.parse_args()
    
    launcher = PlatformLauncher(
        vault_dir=args.vault_dir,
        api_port=args.api_port
    )
    
    if args.validate_only:
        if launcher.validate():
            print("\n✅ All checks passed")
            return 0
        else:
            print("\n❌ Validation failed")
            return 1
    else:
        return launcher.up()


if __name__ == "__main__":
    sys.exit(main())
