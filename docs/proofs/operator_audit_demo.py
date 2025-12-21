import sys
from pathlib import Path
import importlib.util
import tempfile

# Ensure 'packages' dir on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.core.src.agent import Agent
from packages.core.src.llm.llama_client import MockLLM
from packages.vault.src.vault import Vault

# Load builtin_tools dynamically
bt_path = REPO_ROOT / "packages/core/src/builtin_tools.py"
spec = importlib.util.spec_from_file_location("builtin_tools_module", bt_path)
builtin_tools_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builtin_tools_module)

class ToolLLM(MockLLM):
    def generate(self, system, user, prompt, evidence):
        return '<tool name="calculate" expression="2 + 2" />'

def main():
    with tempfile.TemporaryDirectory() as tmp:
        v = Vault(tmp)
        agent = Agent(v, llm=ToolLLM())
        if agent.tool_registry:
            builtin_tools_module.register_builtin_tools(agent.tool_registry)
        res = agent.respond("Compute test", evidence_limit=1)
        print("Tool calls:", res.get("tool_calls"))
        print("Tool results:", res.get("tool_results"))

        # Path traversal negative test
        bad = '<tool name="read_file" file_path="../secret.txt" />'
        calls = agent._detect_tool_calls(bad)
        out = agent._execute_tool(calls[0]["name"], calls[0]["params"])
        print("Traversal test:", out)
        if out.get("success", True):
            raise SystemExit("Traversal should be blocked")

if __name__ == "__main__":
    main()
