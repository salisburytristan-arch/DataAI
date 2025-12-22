"""
Tests for arcticcodex_up.py - ArcticCodex Platform Launcher
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys

# Import from root-level arcticcodex_up module
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from arcticcodex_up import PlatformLauncher


class TestCLI(unittest.TestCase):
    
    def setUp(self):
        """Create temporary directory for tests"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.launcher = PlatformLauncher(
            vault_dir=str(self.test_dir / "vault"),
            api_port=18000  # Use different port for testing
        )
    
    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.test_dir)
    
    def test_check_python_version(self):
        """Test Python version check"""
        result = self.launcher.check_python_version()
        self.assertTrue(result)
    
    def test_check_vault_dir_create(self):
        """Test vault directory creation"""
        result = self.launcher.check_vault_dir()
        self.assertTrue(result)
        self.assertTrue(self.launcher.vault_dir.exists())
    
    def test_check_port_available(self):
        """Test port availability check"""
        result = self.launcher.check_port_available()
        self.assertIsInstance(result, bool)
    
    def test_check_core_imports(self):
        """Test core package imports"""
        result = self.launcher.check_core_imports()
        self.assertTrue(result)
    
    def test_init_vault(self):
        """Test vault initialization"""
        result = self.launcher.init_vault()
        self.assertTrue(result)
        self.assertTrue((self.launcher.vault_dir / ".vault_initialized").exists())
        self.assertTrue((self.launcher.vault_dir / "chunks").exists())
        self.assertTrue((self.launcher.vault_dir / "metadata").exists())
        self.assertTrue((self.launcher.vault_dir / "logs").exists())
    
    def test_validate_system(self):
        """Test full system validation"""
        result = self.launcher.validate()
        # Should pass most checks
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()
