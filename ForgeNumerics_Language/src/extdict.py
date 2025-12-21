"""
Extension Dictionary Allocator for ForgeNumerics-S (Part 14)

Manages dynamic allocation of unused symbol combinations (~750k free combos)
for extending the vocabulary beyond the base dictionary.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from src.data_loader import DataLoader
from src.frames import Frame


class ExtensionDictionary:
    """
    Manages a dynamic extension dictionary that allocates unused symbol combos
    to new words as they are encountered.
    """

    def __init__(self, extdict_id: str, base_path: str = "extdict"):
        """
        Initialize an extension dictionary.
        
        Args:
            extdict_id: Unique identifier (e.g., "EXTDICT_SITE_A_0001")
            base_path: Directory to store extension dictionary files
        """
        self.extdict_id = extdict_id
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Mapping: word -> symbol_combo
        self.word_to_combo: Dict[str, str] = {}
        # Reverse mapping: symbol_combo -> word
        self.combo_to_word: Dict[str, str] = {}
        
        # Load existing mappings if available
        self._load_from_disk()
    
    def _get_filepath(self) -> Path:
        """Get the JSON file path for this extension dictionary."""
        return self.base_path / f"{self.extdict_id}.json"
    
    def _load_from_disk(self):
        """Load existing extension dictionary from disk if it exists."""
        filepath = self._get_filepath()
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.word_to_combo = data.get('word_to_combo', {})
                self.combo_to_word = data.get('combo_to_word', {})
    
    def _save_to_disk(self):
        """Persist the extension dictionary to disk."""
        filepath = self._get_filepath()
        data = {
            'extdict_id': self.extdict_id,
            'word_to_combo': self.word_to_combo,
            'combo_to_word': self.combo_to_word,
            'entry_count': len(self.word_to_combo)
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def lookup_word(self, word: str) -> Optional[str]:
        """Look up a word's symbol combo in this extension dictionary."""
        word_canonical = word.lower().strip()
        return self.word_to_combo.get(word_canonical)
    
    def lookup_combo(self, combo: str) -> Optional[str]:
        """Look up a symbol combo's word in this extension dictionary."""
        return self.combo_to_word.get(combo)
    
    def allocate(self, word: str, combo: str) -> bool:
        """
        Allocate a new mapping from word to combo.
        
        Args:
            word: The word to map
            combo: The symbol combo to assign
            
        Returns:
            True if allocation succeeded, False if word or combo already in use
        """
        # Normalize word (lowercase, strip)
        word_canonical = word.lower().strip()
        
        # Check for conflicts
        if word_canonical in self.word_to_combo:
            return False  # Word already allocated
        if combo in self.combo_to_word:
            return False  # Combo already allocated
        
        # Allocate
        self.word_to_combo[word_canonical] = combo
        self.combo_to_word[combo] = word_canonical
        
        # Persist
        self._save_to_disk()
        return True
    
    def get_entries(self) -> List[Tuple[str, str]]:
        """Get all (word, combo) pairs in this extension dictionary."""
        return [(w, c) for w, c in self.word_to_combo.items()]
    
    def entry_count(self) -> int:
        """Return the number of entries in this extension dictionary."""
        return len(self.word_to_combo)


class DictionaryAllocator:
    """
    Central allocator that manages free symbol combos and assigns them
    to extension dictionaries based on policy.
    """

    def __init__(self, config_path: str = "config.yml"):
        """Initialize the allocator with base dictionary and free combos."""
        # Load config and data via DataLoader
        self.dl = DataLoader()
        
        # Load base dictionary info
        self.base_words = self.dl.load_words()
        self.base_mapping = self.dl.load_word_to_combo()
        
        # Compute free combos (all combos minus used combos)
        all_combos = set(self.dl.load_combos())
        used_combos = set(self.base_mapping.values())
        self.free_combos = list(all_combos - used_combos)
        
        # Sort free combos for deterministic allocation order
        # Prefer shorter combos first, then lexicographic
        self.free_combos_sorted = sorted(
            self.free_combos,
            key=lambda c: (len(c), c)
        )
        
        # Track which combos have been allocated
        self.allocated_combos: Set[str] = set()
        
        # Track loaded extension dictionaries
        self.extdicts: Dict[str, ExtensionDictionary] = {}
    
    def get_free_combo_count(self) -> int:
        """Return the number of available free combos."""
        return len(self.free_combos_sorted) - len(self.allocated_combos)
    
    def get_next_free_combo(self) -> Optional[str]:
        """
        Get the next unused symbol combo from the free list.
        
        Returns:
            A free symbol combo, or None if exhausted
        """
        for combo in self.free_combos_sorted:
            if combo not in self.allocated_combos:
                return combo
        return None
    
    def load_extdict(self, extdict_id: str) -> ExtensionDictionary:
        """Load or create an extension dictionary."""
        if extdict_id not in self.extdicts:
            extdict = ExtensionDictionary(extdict_id)
            self.extdicts[extdict_id] = extdict
            
            # Mark its combos as allocated
            for _, combo in extdict.get_entries():
                self.allocated_combos.add(combo)
        
        return self.extdicts[extdict_id]
    
    def allocate_word(
        self,
        word: str,
        extdict_id: str,
        force_combo: Optional[str] = None
    ) -> Optional[str]:
        """
        Allocate a new word to an extension dictionary.
        
        Args:
            word: The word to allocate
            extdict_id: Which extension dictionary to use
            force_combo: Optionally force a specific combo (for testing)
            
        Returns:
            The allocated symbol combo, or None if allocation failed
        """
        # Load the extension dictionary
        extdict = self.load_extdict(extdict_id)
        
        # Check if word already exists (in base or any extension)
        if word.lower().strip() in self.base_mapping:
            return None  # Already in base dictionary
        
        existing = extdict.lookup_word(word)
        if existing:
            return existing  # Already allocated in this extdict
        
        # Get a free combo
        if force_combo:
            combo = force_combo
            if combo in self.allocated_combos or combo not in self.free_combos:
                return None  # Combo not available
        else:
            combo = self.get_next_free_combo()
            if not combo:
                return None  # Exhausted
        
        # Allocate
        if extdict.allocate(word, combo):
            self.allocated_combos.add(combo)
            return combo
        
        return None
    
    def lookup_word_all(self, word: str) -> Optional[Tuple[str, str]]:
        """
        Look up a word in base + all loaded extension dictionaries.
        
        Returns:
            (symbol_combo, source) where source is "BASE" or extdict_id
        """
        word_canonical = word.lower().strip()
        
        # Check base first
        if word_canonical in self.base_mapping:
            return (self.base_mapping[word_canonical], "BASE")
        
        # Check extensions
        for extdict_id, extdict in self.extdicts.items():
            combo = extdict.lookup_word(word_canonical)
            if combo:
                return (combo, extdict_id)
        
        return None
    
    def make_dict_update_frame(
        self,
        extdict_id: str,
        word_combo_pairs: List[Tuple[str, str]]
    ) -> Frame:
        """
        Create a DICT_UPDATE frame documenting new allocations.
        
        Args:
            extdict_id: The extension dictionary ID
            word_combo_pairs: List of (word, combo) tuples to document
            
        Returns:
            A Frame with TYPE=DICT_UPDATE
        """
        dict_version = self.dl.defaults().get('DICT', 'DICT_v2025_11')
        
        # Build header
        header_fields = [
            ("TYPE", "DICT_UPDATE"),
            ("EXTDICT", extdict_id),
            ("DICT", dict_version),
            ("COUNT", str(len(word_combo_pairs)))
        ]
        
        # Build payload as list of tokens
        payload = []
        for word, combo in word_combo_pairs:
            # Use literals for words (since they may not be in dict yet)
            word_literal = f"≛⟦{word}⟧"
            combo_token = f"≛{combo}"
            payload.extend(["≛WORD", word_literal, "≛CODE", combo_token])
        
        return Frame(header_fields, payload)


def enumerate_free_combos(config_path: str = "config.yml", limit: int = 100) -> List[str]:
    """
    Enumerate free symbol combos (for CLI display).
    
    Args:
        config_path: Path to config file
        limit: Maximum number to return
        
    Returns:
        List of free combos (sorted, shortest first)
    """
    allocator = DictionaryAllocator()
    free = [c for c in allocator.free_combos_sorted if c not in allocator.allocated_combos]
    return free[:limit]
