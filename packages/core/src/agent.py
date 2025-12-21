from typing import Any, Dict, List, Optional
import re
import json
import xml.etree.ElementTree as ET

# Tolerate CWD differences by adjusting sys.path for workspace root
try:
    from packages.vault.src.vault import Vault
except Exception:
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from packages.vault.src.vault import Vault

from .context import ContextBuilder
from .llm.llama_client import LLMClient, MockLLM, HttpLLM
from .config import get_llm_client
from .persistence import persist_response

# Import tool system
try:
    import importlib.util
    from pathlib import Path as PathlibPath
    tools_path = PathlibPath(__file__).parent / "tools.py"
    spec = importlib.util.spec_from_file_location("tools_module", tools_path)
    tools_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tools_module)
    ToolCall = tools_module.ToolCall
    get_registry = tools_module.get_registry
except Exception:
    # Fallback if tools module not available
    ToolCall = None
    get_registry = None


class Agent:
    def __init__(self, vault: Vault, llm: LLMClient | None = None) -> None:
        self.vault = vault
        self.llm = llm or get_llm_client() or MockLLM()
        self.ctx_builder = ContextBuilder()
        self.tool_registry = get_registry() if get_registry else None
        self.tool_call_history: List[Dict[str, Any]] = []
        self.max_tool_calls = 5  # Prevent infinite loops
    
    def _detect_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """Detect tool calls in LLM output.
        
        Looks for patterns like:
        <tool name="read_file" file_path="/path/to/file.txt" />
        or
        <tool name="calculate" expression="2 + 3 * 4"></tool>
        
        Args:
            text: LLM output text
        
        Returns:
            List of detected tool calls with name and parameters
        """
        tool_calls = []
        
        # Pattern 1: Self-closing tags
        pattern1 = r'<tool\s+name="([^"]+)"([^>]*)/>'
        # Pattern 2: Opening/closing tags
        pattern2 = r'<tool\s+name="([^"]+)"([^>]*)>.*?</tool>'
        
        for match in re.finditer(pattern1, text):
            name = match.group(1)
            attrs = match.group(2)
            params = self._parse_attributes(attrs)
            tool_calls.append({"name": name, "params": params, "raw": match.group(0)})
        
        for match in re.finditer(pattern2, text):
            name = match.group(1)
            attrs = match.group(2)
            params = self._parse_attributes(attrs)
            tool_calls.append({"name": name, "params": params, "raw": match.group(0)})
        
        return tool_calls
    
    def _parse_attributes(self, attr_string: str) -> Dict[str, Any]:
        """Parse XML-style attributes from a string.
        
        Args:
            attr_string: String like 'file_path="/path" max_lines="10"'
        
        Returns:
            Dictionary of {key: value} pairs
        """
        params = {}
        # Match key="value" or key='value'
        pattern = r'(\w+)=(["\'])([^"\']*)\2'
        for match in re.finditer(pattern, attr_string):
            key = match.group(1)
            value = match.group(3)
            # Try to parse as JSON for booleans/numbers/lists
            try:
                params[key] = json.loads(value)
            except (json.JSONDecodeError, ValueError):
                # Keep as string
                params[key] = value
        return params
    
    def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call.
        
        Args:
            tool_name: Name of tool to execute
            params: Tool parameters
        
        Returns:
            Tool result with success/result/error fields
        """
        if not self.tool_registry:
            return {
                "success": False,
                "error": "Tool registry not available",
                "tool_name": tool_name
            }
        
        try:
            # Create tool call
            call = ToolCall(tool_name=tool_name, parameters=params)
            # Execute
            result = self.tool_registry.execute(call)
            # Convert result to dict for serialization
            return {
                "success": result.success,
                "result": result.result if result.success else None,
                "error": result.error if not result.success else None,
                "tool_name": tool_name,
                "execution_time_ms": result.execution_time_ms
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name
            }
    
    def _format_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """Format tool results for inclusion in next LLM prompt.
        
        Args:
            tool_results: List of tool execution results
        
        Returns:
            Formatted string to include in next context
        """
        if not tool_results:
            return ""
        
        parts = ["[Tool Execution Results]"]
        for result in tool_results:
            tool_name = result.get("tool_name", "unknown")
            if result.get("success"):
                parts.append(f"✓ {tool_name}: {result.get('result')}")
            else:
                parts.append(f"✗ {tool_name}: {result.get('error')}")
        
        return "\n".join(parts)

    def respond(self, query: str, evidence_limit: int = 5, persist: bool = False, convo_id: str | None = None) -> Dict[str, Any]:
        """Generate a response, potentially using tools.
        
        Args:
            query: User query
            evidence_limit: Max evidence chunks to use
            persist: Whether to persist response
            convo_id: Conversation ID
        
        Returns:
            Response with text, citations, and tool usage info
        """
        ctx = self.ctx_builder.build(query, self.vault, limit=evidence_limit)
        
        # Initial response from LLM
        text = self.llm.generate(system=ctx.system, user=query, prompt=ctx.prompt, evidence=ctx.evidence)
        
        # Check for tool calls in response
        tool_calls = self._detect_tool_calls(text)
        tool_results = []
        
        # Execute tools (with limit to prevent loops)
        for i, tool_call in enumerate(tool_calls[:self.max_tool_calls]):
            result = self._execute_tool(tool_call["name"], tool_call["params"])
            tool_results.append(result)
            self.tool_call_history.append({
                "query": query,
                "tool": tool_call["name"],
                "params": tool_call["params"],
                "result": result
            })
        
        # If tools were used, make follow-up call to LLM to incorporate results
        if tool_results:
            formatted_results = self._format_tool_results(tool_results)
            follow_up_prompt = f"{ctx.prompt}\n\nPrevious Response:\n{text}\n\n{formatted_results}\n\nPlease provide a final answer incorporating the tool results."
            text = self.llm.generate(
                system=ctx.system,
                user=query,
                prompt=follow_up_prompt,
                evidence=ctx.evidence
            )
        
        result = {
            "text": text,
            "citations": ctx.citations,
            "used_chunks": [ch.get("chunk_id") for ch in ctx.evidence],
        }
        
        # Add tool usage info if applicable
        if tool_results:
            result["tool_calls"] = [
                {"tool": tc["name"], "params": tc["params"]} 
                for tc in tool_calls[:self.max_tool_calls]
            ]
            result["tool_results"] = tool_results
        
        if persist:
            written = persist_response(self.vault, convo_id, query, result)
            result.update({"persist": written})
        
        return result
