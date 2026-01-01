"""Tests for Vault storage and retrieval."""
import tempfile
import shutil
import sys
import unittest
from pathlib import Path

# Import vault package
vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from packages.vault.src.vault import Vault


class TestVaultLegacy(unittest.TestCase):
    """Legacy Vault tests converted to unittest."""
    
    def test_vault_import_and_retrieve(self):
        """Test basic import and retrieval workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create vault
            vault = Vault(tmpdir)
            
            # Import a document
            text = """
            The quick brown fox jumps over the lazy dog.
            This is a test document for the Vault system.
            It contains multiple sentences and paragraphs.
            
            Here is another paragraph with different content.
            The Vault stores chunks and allows retrieval.
            """
            
            doc_id = vault.import_text(text, title="Test Doc", source_path="/tmp/test.txt")
            
            # Verify document was stored
            doc = vault.get_doc(doc_id)
            self.assertIsNotNone(doc, "Document should be stored")
            self.assertEqual(doc.title, "Test Doc")
            self.assertGreater(doc.chunk_count, 0, "Document should have chunks")
            
            # Verify chunks were created
            chunks = vault.get_chunks_for_doc(doc_id)
            self.assertGreater(len(chunks), 0, "Should have chunks")
            
            # Verify chunk content
            chunk = chunks[0]
            self.assertGreater(len(chunk.content), 0, "Chunk should have content")

    def test_vault_search(self):
        """Test keyword search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Vault(tmpdir)
            
            # Import documents
            vault.import_text(
                "The quick brown fox jumps over the lazy dog.",
                title="Fox Doc",
                source_path="/tmp/fox.txt"
            )
            vault.import_text(
                "Dogs are loyal animals and make great companions.",
                title="Dogs Doc",
                source_path="/tmp/dogs.txt"
            )
            
            # Search for "dog"
            results = vault.search("dog", limit=5)
            self.assertGreater(len(results), 0, "Should find results for 'dog'")
            self.assertIsNotNone(results[0]["content"], "Result should have content")

    def test_vault_facts(self):
        """Test fact storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Vault(tmpdir)
            
            # Store facts
            fact_id1 = vault.put_fact("Alice", "knows", "Bob", confidence=0.9)
            fact_id2 = vault.put_fact("Bob", "works_at", "Acme Corp", confidence=0.8)
            
            # Retrieve facts
            facts = vault.list_facts()
            self.assertEqual(len(facts), 2, "Should have 2 facts")
            self.assertIn(facts[0].subject, ["Alice", "Bob"], "Fact should have correct subject")

    def test_vault_forget(self):
        """Test soft deletion with tombstones."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Vault(tmpdir)
            
            # Import and then forget
            doc_id = vault.import_text("Test content", title="Test", source_path="/tmp/test.txt")
            self.assertIsNotNone(vault.get_doc(doc_id))
            
            # Soft delete
            ts_id = vault.forget(doc_id, reason="Test deletion")
            self.assertIsNotNone(ts_id, "Should return tombstone ID")
            
            # Document should still be in index but marked deleted
            self.assertTrue(vault.index.is_deleted(doc_id))
            self.assertIsNone(vault.get_doc(doc_id), "Deleted doc should not be retrievable")

    def test_vault_stats(self):
        """Test vault statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Vault(tmpdir)
            
            # Import document
            vault.import_text("Test content", title="Test", source_path="/tmp/test.txt")
            
            # Get stats
            stats = vault.stats()
            self.assertEqual(stats["doc_count"], 1)
            self.assertGreater(stats["chunk_count"], 0)


if __name__ == "__main__":
    unittest.main()

