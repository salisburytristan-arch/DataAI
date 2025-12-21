"""
Tests for extension dictionary allocator (Part 14)
"""

import os
import tempfile
import shutil
from pathlib import Path
from src.extdict import ExtensionDictionary, DictionaryAllocator


def test_extension_dictionary_basic():
    """Test basic extension dictionary operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        extdict = ExtensionDictionary("TEST_0001", base_path=tmpdir)
        
        # Allocate a word
        success = extdict.allocate("megafauna", "Ωζ")
        assert success, "First allocation should succeed"
        
        # Verify lookup
        assert extdict.lookup_word("megafauna") == "Ωζ"
        assert extdict.lookup_combo("Ωζ") == "megafauna"
        
        # Try duplicate allocation
        success = extdict.allocate("megafauna", "Ψχ")
        assert not success, "Duplicate word should fail"
        
        # Try duplicate combo
        success = extdict.allocate("hypernode", "Ωζ")
        assert not success, "Duplicate combo should fail"
        
        # Allocate another word
        success = extdict.allocate("hypernode", "Ψχ")
        assert success, "Second allocation should succeed"
        
        # Verify entry count
        assert extdict.entry_count() == 2


def test_extension_dictionary_persistence():
    """Test that extension dictionaries persist to disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create and populate
        extdict1 = ExtensionDictionary("TEST_0002", base_path=tmpdir)
        extdict1.allocate("alpha", "α1")
        extdict1.allocate("beta", "β2")
        
        # Load again
        extdict2 = ExtensionDictionary("TEST_0002", base_path=tmpdir)
        assert extdict2.entry_count() == 2
        assert extdict2.lookup_word("alpha") == "α1"
        assert extdict2.lookup_word("beta") == "β2"


def test_extension_dictionary_case_normalization():
    """Test that words are normalized to lowercase."""
    with tempfile.TemporaryDirectory() as tmpdir:
        extdict = ExtensionDictionary("TEST_0003", base_path=tmpdir)
        
        extdict.allocate("MegaFauna", "Ωζ")
        
        # All case variations should work
        assert extdict.lookup_word("megafauna") == "Ωζ"
        assert extdict.lookup_word("MEGAFAUNA") == "Ωζ"
        assert extdict.lookup_word("MegaFauna") == "Ωζ"


def test_dictionary_allocator_free_combos():
    """Test that allocator correctly computes free combos."""
    allocator = DictionaryAllocator()
    
    # Should have many free combos
    free_count = allocator.get_free_combo_count()
    assert free_count > 100000, f"Expected >100k free combos, got {free_count}"
    
    # Get next free combo
    combo = allocator.get_next_free_combo()
    assert combo is not None
    assert len(combo) >= 1


def test_dictionary_allocator_word_allocation():
    """Test dynamic word allocation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch the extdict base path
        allocator = DictionaryAllocator()
        
        # Allocate a word (use temp extdict path)
        from src.extdict import ExtensionDictionary
        old_init = ExtensionDictionary.__init__
        
        def patched_init(self, extdict_id, base_path="extdict"):
            old_init(self, extdict_id, base_path=tmpdir)
        
        ExtensionDictionary.__init__ = patched_init
        
        try:
            combo = allocator.allocate_word("testword", "TEST_ALLOC_0001")
            assert combo is not None, "Allocation should succeed"
            
            # Verify it's in the allocator's tracking
            assert combo in allocator.allocated_combos
            
            # Try to allocate same word again
            combo2 = allocator.allocate_word("testword", "TEST_ALLOC_0001")
            assert combo2 == combo, "Re-allocating same word should return existing combo"
        finally:
            ExtensionDictionary.__init__ = old_init


def test_dictionary_allocator_base_word_conflict():
    """Test that words in base dictionary cannot be allocated."""
    allocator = DictionaryAllocator()
    
    # Get a word from base dictionary
    if allocator.base_words:
        base_word = allocator.base_words[0]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.extdict import ExtensionDictionary
            old_init = ExtensionDictionary.__init__
            
            def patched_init(self, extdict_id, base_path="extdict"):
                old_init(self, extdict_id, base_path=tmpdir)
            
            ExtensionDictionary.__init__ = patched_init
            
            try:
                result = allocator.allocate_word(base_word, "TEST_CONFLICT")
                assert result is None, "Should not allocate word that exists in base dict"
            finally:
                ExtensionDictionary.__init__ = old_init


def test_dict_update_frame():
    """Test DICT_UPDATE frame generation."""
    allocator = DictionaryAllocator()
    
    pairs = [
        ("megafauna", "Ωζ"),
        ("hypernode", "Ψχ"),
    ]
    
    frame = allocator.make_dict_update_frame("TEST_UPDATE", pairs)
    
    # Verify frame structure
    serialized = frame.serialize()
    assert "⧆" in serialized
    assert "⧈" in serialized
    assert "DICT_UPDATE" in serialized
    assert "TEST_UPDATE" in serialized
    assert "megafauna" in serialized or "⟦megafauna⟧" in serialized
    assert "hypernode" in serialized or "⟦hypernode⟧" in serialized


if __name__ == "__main__":
    # Run tests
    test_extension_dictionary_basic()
    print("✓ test_extension_dictionary_basic")
    
    test_extension_dictionary_persistence()
    print("✓ test_extension_dictionary_persistence")
    
    test_extension_dictionary_case_normalization()
    print("✓ test_extension_dictionary_case_normalization")
    
    test_dictionary_allocator_free_combos()
    print("✓ test_dictionary_allocator_free_combos")
    
    test_dictionary_allocator_word_allocation()
    print("✓ test_dictionary_allocator_word_allocation")
    
    test_dictionary_allocator_base_word_conflict()
    print("✓ test_dictionary_allocator_base_word_conflict")
    
    test_dict_update_frame()
    print("✓ test_dict_update_frame")
    
    print("\nAll extension dictionary tests passed!")
