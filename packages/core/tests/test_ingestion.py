"""
Tests for ingestion.py - Document Ingestion System
"""

import unittest
import tempfile
import shutil
from pathlib import Path

from packages.core.src.ingestion import (
    DocumentIngestion, TextExtractor, Document
)


class TestIngestion(unittest.TestCase):
    
    def setUp(self):
        """Create temporary directory with test files"""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create test files
        (self.test_dir / "test.txt").write_text("This is a plain text file.")
        
        (self.test_dir / "test.md").write_text("""
# Header
This is **bold** and *italic* text.
[Link](http://example.com)
```python
print("code")
```
""")
        
        (self.test_dir / "test.html").write_text("""
<html>
<head><title>Test</title></head>
<body>
<script>alert('test');</script>
<p>This is HTML content.</p>
<a href="test">Link</a>
</body>
</html>
""")
        
        # Create subdirectory
        subdir = self.test_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("Nested file content.")
        
        # Create hidden file
        (self.test_dir / ".hidden.txt").write_text("Hidden file.")
        
        # Create large file
        (self.test_dir / "large.txt").write_text("x" * (11 * 1024 * 1024))  # 11MB
        
        self.ingestion = DocumentIngestion(max_file_size_mb=10)
    
    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.test_dir)
    
    def test_extract_txt(self):
        """Test plain text extraction"""
        content = TextExtractor.extract_txt(self.test_dir / "test.txt")
        self.assertEqual(content, "This is a plain text file.")
    
    def test_extract_markdown(self):
        """Test Markdown extraction"""
        content = TextExtractor.extract_markdown(self.test_dir / "test.md")
        
        # Should remove markdown syntax
        self.assertNotIn("**", content)
        self.assertNotIn("*", content)
        self.assertNotIn("#", content)
        self.assertNotIn("```", content)
        
        # Should keep text content
        self.assertIn("Header", content)
        self.assertIn("bold", content)
        self.assertIn("italic", content)
    
    def test_extract_html(self):
        """Test HTML extraction"""
        content = TextExtractor.extract_html(self.test_dir / "test.html")
        
        # Should remove HTML tags
        self.assertNotIn("<p>", content)
        self.assertNotIn("<a", content)
        
        # Should remove scripts
        self.assertNotIn("alert", content)
        
        # Should keep text content
        self.assertIn("HTML content", content)
    
    def test_scan_directory_non_recursive(self):
        """Test non-recursive directory scan"""
        files = self.ingestion.scan_directory(self.test_dir, recursive=False)
        
        # Should find files in root
        file_names = [f.name for f in files]
        self.assertIn("test.txt", file_names)
        self.assertIn("test.md", file_names)
        
        # Should not find nested files
        self.assertNotIn("nested.txt", file_names)
    
    def test_scan_directory_recursive(self):
        """Test recursive directory scan"""
        files = self.ingestion.scan_directory(self.test_dir, recursive=True)
        
        # Should find nested files
        file_names = [f.name for f in files]
        self.assertIn("nested.txt", file_names)
    
    def test_scan_directory_skip_hidden(self):
        """Test skipping hidden files"""
        files = self.ingestion.scan_directory(self.test_dir, recursive=False)
        
        file_names = [f.name for f in files]
        self.assertNotIn(".hidden.txt", file_names)
    
    def test_scan_directory_skip_large_files(self):
        """Test skipping files over size limit"""
        files = self.ingestion.scan_directory(self.test_dir, recursive=False)
        
        file_names = [f.name for f in files]
        self.assertNotIn("large.txt", file_names)
    
    def test_scan_directory_filter_extensions(self):
        """Test filtering by extension"""
        files = self.ingestion.scan_directory(
            self.test_dir,
            recursive=False,
            extensions={'.txt'}
        )
        
        # Should only find .txt files
        for f in files:
            self.assertEqual(f.suffix, '.txt')
    
    def test_ingest_file(self):
        """Test ingesting a single file"""
        doc = self.ingestion.ingest_file(self.test_dir / "test.txt")
        
        self.assertIsInstance(doc, Document)
        self.assertEqual(doc.content, "This is a plain text file.")
        self.assertIn("file_type", doc.metadata)
        self.assertEqual(doc.metadata["file_type"], "text")
        self.assertGreater(len(doc.doc_id), 0)
        self.assertGreater(len(doc.content_hash), 0)
    
    def test_ingest_file_size_limit(self):
        """Test file size limit enforcement"""
        with self.assertRaises(ValueError) as ctx:
            self.ingestion.ingest_file(self.test_dir / "large.txt")
        
        self.assertIn("exceeds size limit", str(ctx.exception))
    
    def test_ingest_file_unsupported_type(self):
        """Test unsupported file type"""
        (self.test_dir / "test.xyz").write_text("content")
        
        with self.assertRaises(ValueError) as ctx:
            self.ingestion.ingest_file(self.test_dir / "test.xyz")
        
        self.assertIn("Unsupported file type", str(ctx.exception))
    
    def test_ingest_file_nonexistent(self):
        """Test ingesting non-existent file"""
        with self.assertRaises(ValueError) as ctx:
            self.ingestion.ingest_file(self.test_dir / "nonexistent.txt")
        
        self.assertIn("does not exist", str(ctx.exception))
    
    def test_ingest_directory(self):
        """Test ingesting entire directory"""
        docs = self.ingestion.ingest_directory(self.test_dir, recursive=True)
        
        self.assertGreater(len(docs), 0)
        
        # Should have ingested supported files
        source_paths = [doc.source_path for doc in docs]
        self.assertTrue(any("test.txt" in path for path in source_paths))
        self.assertTrue(any("test.md" in path for path in source_paths))
        self.assertTrue(any("nested.txt" in path for path in source_paths))
    
    def test_ingest_batch(self):
        """Test batch ingestion"""
        files = [
            self.test_dir / "test.txt",
            self.test_dir / "test.md"
        ]
        
        docs = self.ingestion.ingest_batch(files)
        
        self.assertEqual(len(docs), 2)
        self.assertIsInstance(docs[0], Document)
        self.assertIsInstance(docs[1], Document)
    
    def test_document_content_hash(self):
        """Test document content hashing"""
        doc1 = self.ingestion.ingest_file(self.test_dir / "test.txt")
        doc2 = self.ingestion.ingest_file(self.test_dir / "test.txt")
        
        # Same content should have same hash
        self.assertEqual(doc1.content_hash, doc2.content_hash)
        
        # Different content should have different hash
        doc3 = self.ingestion.ingest_file(self.test_dir / "test.md")
        self.assertNotEqual(doc1.content_hash, doc3.content_hash)
    
    def test_document_metadata(self):
        """Test document metadata"""
        doc = self.ingestion.ingest_file(self.test_dir / "test.txt")
        
        self.assertIn("file_type", doc.metadata)
        self.assertIn("file_size_bytes", doc.metadata)
        self.assertIn("file_name", doc.metadata)
        self.assertIn("extension", doc.metadata)
        
        self.assertEqual(doc.metadata["file_name"], "test.txt")
        self.assertEqual(doc.metadata["extension"], ".txt")
    
    def test_scan_invalid_directory(self):
        """Test scanning non-existent directory"""
        with self.assertRaises(ValueError) as ctx:
            self.ingestion.scan_directory(Path("/nonexistent/directory"))
        
        self.assertIn("does not exist", str(ctx.exception))
    
    def test_scan_file_not_directory(self):
        """Test scanning a file instead of directory"""
        with self.assertRaises(ValueError) as ctx:
            self.ingestion.scan_directory(self.test_dir / "test.txt")
        
        self.assertIn("Not a directory", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
