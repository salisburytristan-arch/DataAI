import os
import unittest

from src.data_loader import DataLoader, FILES

class TestDataLoader(unittest.TestCase):
    def test_paths_exist_or_empty(self):
        dl = DataLoader()
        # All loaders should return lists/dicts even if files are missing
        self.assertIsInstance(dl.load_words(), list)
        self.assertIsInstance(dl.load_symbols(), list)
        self.assertIsInstance(dl.load_combos(), list)
        self.assertIsInstance(dl.load_word_to_combo(), dict)
        self.assertIsInstance(dl.free_combos(), list)

if __name__ == "__main__":
    unittest.main()
