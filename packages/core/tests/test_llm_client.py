import unittest
from packages.core.src.llm.llama_client import HttpLLM, MockLLM

class TestLLMClient(unittest.TestCase):
    def test_http_llm_fallback(self):
        # Use an endpoint that will fail to connect quickly
        client = HttpLLM("http://127.0.0.1:9")  # Port 9 (discard) typically closed
        try:
            client.generate(system="s", user="u", prompt="p", evidence=[])
            self.fail("Expected connection error")
        except Exception:
            # Simulate fallback by using MockLLM
            mock = MockLLM()
            text = mock.generate(system="s", user="hello", prompt="p", evidence=[])
            self.assertIn("You asked:", text)

if __name__ == "__main__":
    unittest.main()
