"""Tests for distillation dataset writer."""

import unittest
import json
import os
import tempfile
from unittest.mock import MagicMock, patch
from packages.core.src.distillation_writer import (
    TrainingPair,
    DistillationDatasetWriter,
)


class TestTrainingPair(unittest.TestCase):
    """Test TrainingPair dataclass."""
    
    def test_pair_creation(self):
        """Test creating a training pair."""
        pair = TrainingPair(
            pair_id="train-001",
            instruction="What is AI?",
            completion="AI is artificial intelligence...",
            evidence_chunks=["chunk1"],
            teacher_feedback="Good explanation",
            quality_score=0.9,
            signer_id="verifier-01",
            source_convo_id="conv-001",
            created_at="2025-12-20T12:00:00",
            verified=True
        )
        
        self.assertEqual(pair.pair_id, "train-001")
        self.assertEqual(pair.quality_score, 0.9)
        self.assertTrue(pair.verified)


class TestDistillationDatasetWriter(unittest.TestCase):
    """Test distillation dataset writer."""
    
    def setUp(self):
        """Initialize test fixtures."""
        self.mock_vault = MagicMock()
        self.writer = DistillationDatasetWriter(vault=self.mock_vault)
    
    def test_writer_initialization(self):
        """Test writer initialization."""
        self.assertIsNotNone(self.writer.vault)
        self.assertEqual(len(self.writer.pairs), 0)
        self.assertEqual(self.writer.quality_threshold, 0.75)
    
    def test_add_training_pair(self):
        """Test adding a training pair."""
        pair = self.writer.add_training_pair(
            instruction="Test instruction",
            completion="Test completion",
            evidence=["chunk1", "chunk2"],
            feedback="Good",
            quality_score=0.9,
            signer_id="test-signer"
        )
        
        self.assertEqual(len(self.writer.pairs), 1)
        self.assertEqual(pair.instruction, "Test instruction")
        self.assertEqual(pair.quality_score, 0.9)
        self.assertTrue(pair.verified)
    
    def test_add_training_pair_below_threshold(self):
        """Test adding pair below quality threshold."""
        pair = self.writer.add_training_pair(
            instruction="Test",
            completion="Test",
            quality_score=0.5  # Below 0.75 threshold
        )
        
        self.assertFalse(pair.verified)
    
    def test_filter_by_quality(self):
        """Test filtering pairs by quality."""
        self.writer.add_training_pair("Q1", "C1", quality_score=0.95)
        self.writer.add_training_pair("Q2", "C2", quality_score=0.80)
        self.writer.add_training_pair("Q3", "C3", quality_score=0.60)
        
        filtered = self.writer.filter_by_quality(0.80)
        
        self.assertEqual(len(filtered), 2)
        self.assertTrue(all(p.quality_score >= 0.80 for p in filtered))
    
    def test_generate_frames(self):
        """Test generating ForgeNumerics frames."""
        self.writer.add_training_pair(
            instruction="Test instruction",
            completion="Test completion",
            quality_score=0.9,
            source_convo_id="conv-001"
        )
        
        # Mock the frame generation
        with patch("packages.core.src.distillation_writer.to_fn_train_pair") as mock_to_fn:
            mock_to_fn.return_value = "≛TRAIN_PAIR≛...≛frame_data≛⧈"
            
            self.writer.generate_frames()
            
            # Verify frame was generated
            self.assertIsNotNone(self.writer.pairs[0].frame_str)
            self.assertEqual(self.writer.pairs[0].frame_str, "≛TRAIN_PAIR≛...≛frame_data≛⧈")
    
    def test_export_dataset_to_jsonl(self):
        """Test exporting dataset to JSONL file."""
        self.writer.add_training_pair(
            instruction="Q1",
            completion="C1",
            quality_score=0.95,
            signer_id="verifier-01"
        )
        self.writer.add_training_pair(
            instruction="Q2",
            completion="C2",
            quality_score=0.80,
            signer_id="verifier-02"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            temp_file = f.name
        
        try:
            with patch("packages.core.src.distillation_writer.to_fn_train_pair") as mock_to_fn:
                mock_to_fn.return_value = "≛FRAME≛"
                
                stats = self.writer.export_dataset(temp_file)
            
            # Verify file was created
            self.assertTrue(os.path.exists(temp_file))
            
            # Verify content
            with open(temp_file, 'r') as f:
                lines = f.readlines()
                self.assertEqual(len(lines), 2)
                
                # Parse first line
                first = json.loads(lines[0])
                self.assertEqual(first["instruction"], "Q1")
                self.assertEqual(first["quality_score"], 0.95)
            
            # Check stats
            self.assertEqual(stats["total_pairs"], 2)
            self.assertEqual(stats["verified_pairs"], 2)
            
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_export_dataset_with_quality_filter(self):
        """Test exporting with quality filter."""
        self.writer.add_training_pair("Q1", "C1", quality_score=0.95)
        self.writer.add_training_pair("Q2", "C2", quality_score=0.70)
        self.writer.add_training_pair("Q3", "C3", quality_score=0.85)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            temp_file = f.name
        
        try:
            with patch("packages.core.src.distillation_writer.to_fn_train_pair") as mock_to_fn:
                mock_to_fn.return_value = "≛FRAME≛"
                
                stats = self.writer.export_dataset(temp_file, quality_threshold=0.80)
            
            # Only 2 pairs above 0.80 threshold
            with open(temp_file, 'r') as f:
                lines = f.readlines()
                self.assertEqual(len(lines), 2)
            
            self.assertEqual(stats["total_pairs"], 2)
            
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_export_with_signatures(self):
        """Test exporting with signatures."""
        mock_verifier = MagicMock()
        writer = DistillationDatasetWriter(vault=self.mock_vault, verifier=mock_verifier)
        
        writer.add_training_pair("Q1", "C1", quality_score=0.95)
        mock_verifier.sign_frame.return_value = "[SIG|abc123|verifier-01|timestamp]"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            temp_file = f.name
        
        try:
            with patch("packages.core.src.distillation_writer.to_fn_train_pair") as mock_to_fn:
                mock_to_fn.return_value = "≛FRAME≛"
                
                writer.export_dataset(temp_file, sign=True)
            
            # Verify signature was included
            with open(temp_file, 'r') as f:
                first_line = json.loads(f.readline())
                self.assertIn("signature", first_line)
                self.assertEqual(first_line["signature"], "[SIG|abc123|verifier-01|timestamp]")
            
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_statistics(self):
        """Test getting dataset statistics."""
        self.writer.add_training_pair("Q1", "C1", quality_score=0.95, signer_id="v1")
        self.writer.add_training_pair("Q2", "C2", quality_score=0.88, signer_id="v2")
        self.writer.add_training_pair("Q3", "C3", quality_score=0.72, signer_id="v1")
        
        stats = self.writer.statistics()
        
        self.assertEqual(stats["total_pairs"], 3)
        self.assertEqual(stats["verified_pairs"], 2)
        self.assertEqual(stats["unverified_pairs"], 1)
        self.assertAlmostEqual(stats["average_quality"], 0.85, places=1)
        self.assertEqual(stats["min_quality"], 0.72)
        self.assertEqual(stats["max_quality"], 0.95)
        self.assertIn("v1", stats["signers"])
        self.assertIn("v2", stats["signers"])
    
    def test_statistics_empty(self):
        """Test statistics with empty dataset."""
        stats = self.writer.statistics()
        
        self.assertEqual(stats["total_pairs"], 0)
        self.assertEqual(stats["verified_pairs"], 0)
        self.assertEqual(stats["average_quality"], 0.0)
    
    def test_quality_distribution(self):
        """Test quality score distribution."""
        self.writer.add_training_pair("Q1", "C1", quality_score=0.98)  # Excellent
        self.writer.add_training_pair("Q2", "C2", quality_score=0.90)  # Good
        self.writer.add_training_pair("Q3", "C3", quality_score=0.80)  # Acceptable
        self.writer.add_training_pair("Q4", "C4", quality_score=0.60)  # Poor
        
        stats = self.writer.statistics()
        dist = stats["quality_distribution"]
        
        self.assertEqual(dist["excellent (0.95+)"], 1)
        self.assertEqual(dist["good (0.85-0.95)"], 1)
        self.assertEqual(dist["acceptable (0.75-0.85)"], 1)
        self.assertEqual(dist["poor (<0.75)"], 1)


class TestImportFromConversation(unittest.TestCase):
    """Test importing training pairs from conversations."""
    
    def setUp(self):
        """Initialize test fixtures."""
        self.mock_vault = MagicMock()
        self.writer = DistillationDatasetWriter(vault=self.mock_vault)
    
    def test_import_from_conversation(self):
        """Test importing pairs from conversation."""
        # Mock vault returns
        self.mock_vault.list_summaries.return_value = [
            {"summary_text": "Summary of discussion about Python"},
        ]
        self.mock_vault.list_facts.return_value = [
            {
                "subject": "Python",
                "predicate": "is_a",
                "object": "programming_language"
            },
        ]
        
        count = self.writer.import_from_conversation("conv-001")
        
        self.assertEqual(count, 1)
        self.assertEqual(len(self.writer.pairs), 1)
        self.assertEqual(self.writer.pairs[0].source_convo_id, "conv-001")
    
    def test_import_multiple_summaries(self):
        """Test importing multiple summaries."""
        self.mock_vault.list_summaries.return_value = [
            {"summary_text": "Summary 1"},
            {"summary_text": "Summary 2"},
            {"summary_text": "Summary 3"},
        ]
        self.mock_vault.list_facts.return_value = []
        
        count = self.writer.import_from_conversation("conv-001")
        
        self.assertEqual(count, 3)
        self.assertEqual(len(self.writer.pairs), 3)


if __name__ == "__main__":
    unittest.main()
