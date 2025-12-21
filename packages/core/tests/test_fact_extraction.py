import unittest
from packages.core.src.fact_extraction import extract_svo_facts

class TestFactExtraction(unittest.TestCase):
    def test_simple_patterns(self):
        txt = "Fox is a canine. Cats are animals. Rust is fast."
        facts = extract_svo_facts(txt)
        # Expect multiple tuples
        self.assertTrue(any(f[0].lower().startswith("fox") and f[2].lower().startswith("canine") for f in facts))
        self.assertTrue(any(f[0].lower().startswith("cats") and f[2].lower().startswith("animals") for f in facts))

if __name__ == "__main__":
    unittest.main()
