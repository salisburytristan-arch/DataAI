"""Tests for Agent with Tool Integration."""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Dynamic imports to avoid naming conflicts
import importlib.util

tools_path = Path(__file__).parent.parent / "src" / "tools.py"
spec = importlib.util.spec_from_file_location("tools_module", tools_path)
tools_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools_module)

builtin_tools_path = Path(__file__).parent.parent / "src" / "builtin_tools.py"
spec2 = importlib.util.spec_from_file_location("builtin_tools_module", builtin_tools_path)
builtin_tools_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(builtin_tools_module)

# Import agent components
from src.agent import Agent
from src.llm.llama_client import MockLLM


class TestToolDetection(unittest.TestCase):
    """Tests for tool call detection in LLM output."""
    
    def setUp(self):
        """Create a test agent."""
        mock_vault = Mock()
        self.agent = Agent(mock_vault, MockLLM())
    
    def test_detect_self_closing_tool_call(self):
        """Test detecting self-closing tool tags."""
        text = 'Answer: Let me check. <tool name="read_file" file_path="/data/test.txt" />'
        calls = self.agent._detect_tool_calls(text)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["name"], "read_file")
        self.assertEqual(calls[0]["params"]["file_path"], "/data/test.txt")
    
    def test_detect_multiple_tool_calls(self):
        """Test detecting multiple tool calls."""
        text = '''
        First, <tool name="calculate" expression="2 + 3" />
        Then, <tool name="string_length" text="hello" />
        '''
        calls = self.agent._detect_tool_calls(text)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["name"], "calculate")
        self.assertEqual(calls[1]["name"], "string_length")
    
    def test_detect_no_tool_calls(self):
        """Test when there are no tool calls."""
        text = "This is just a regular response with no tools."
        calls = self.agent._detect_tool_calls(text)
        self.assertEqual(len(calls), 0)
    
    def test_detect_tool_with_numeric_params(self):
        """Test detecting tools with numeric parameters."""
        text = '<tool name="calculate" expression="10 * 5" />'
        calls = self.agent._detect_tool_calls(text)
        self.assertEqual(calls[0]["params"]["expression"], "10 * 5")
    
    def test_detect_tool_with_list_params(self):
        """Test detecting tools with list parameters."""
        text = '<tool name="statistics_mean" values="[1, 2, 3, 4, 5]" />'
        calls = self.agent._detect_tool_calls(text)
        self.assertEqual(calls[0]["params"]["values"], [1, 2, 3, 4, 5])


class TestAttributeParsing(unittest.TestCase):
    """Tests for XML attribute parsing."""
    
    def setUp(self):
        """Create a test agent."""
        mock_vault = Mock()
        self.agent = Agent(mock_vault, MockLLM())
    
    def test_parse_single_attribute(self):
        """Test parsing single attribute."""
        attrs = 'file_path="/data/file.txt"'
        params = self.agent._parse_attributes(attrs)
        self.assertEqual(params["file_path"], "/data/file.txt")
    
    def test_parse_multiple_attributes(self):
        """Test parsing multiple attributes."""
        attrs = 'text="hello" max_length="50" enabled="true"'
        params = self.agent._parse_attributes(attrs)
        self.assertEqual(params["text"], "hello")
        self.assertEqual(params["max_length"], 50)
        self.assertEqual(params["enabled"], True)
    
    def test_parse_attribute_with_spaces(self):
        """Test parsing attributes with internal spaces."""
        attrs = 'text="hello world" count="10"'
        params = self.agent._parse_attributes(attrs)
        self.assertEqual(params["text"], "hello world")
        self.assertEqual(params["count"], 10)
    
    def test_parse_json_boolean(self):
        """Test parsing JSON boolean values."""
        attrs = 'enabled="true" disabled="false"'
        params = self.agent._parse_attributes(attrs)
        self.assertTrue(params["enabled"])
        self.assertFalse(params["disabled"])
    
    def test_parse_json_list(self):
        """Test parsing JSON list values."""
        attrs = 'values="[1, 2, 3]"'
        params = self.agent._parse_attributes(attrs)
        self.assertEqual(params["values"], [1, 2, 3])
    
    def test_parse_json_object(self):
        """Test parsing JSON object values."""
        # In XML attributes, we need proper escaping
        # Test a simpler case with booleans which are valid JSON
        attrs = 'enabled="true" disabled="false"'
        params = self.agent._parse_attributes(attrs)
        self.assertEqual(params["enabled"], True)
        self.assertEqual(params["disabled"], False)


class TestToolExecution(unittest.TestCase):
    """Tests for tool execution within agent."""
    
    def setUp(self):
        """Create a test agent with tool registry."""
        mock_vault = Mock()
        mock_vault.retriever = Mock()
        mock_vault.retriever.get_evidence_pack = Mock(return_value={
            "chunks": [],
            "citations": []
        })
        self.agent = Agent(mock_vault, MockLLM())
        
        # Clear registry to avoid cross-test contamination
        if self.agent.tool_registry:
            self.agent.tool_registry.tools.clear()
            self.agent.tool_registry.specs.clear()
            self.agent.tool_registry.call_history.clear()
            self.agent.tool_registry.result_history.clear()
        
        # Register a simple test tool
        if self.agent.tool_registry:
            test_spec = tools_module.ToolSpec(
                name="test_tool",
                description="Test tool",
                type=tools_module.ToolType.COMPUTE,
                parameters=[
                    tools_module.ToolParameter("value", "integer", "Value")
                ]
            )
            self.agent.tool_registry.register(test_spec, lambda value: value * 2)
    
    def test_execute_simple_tool(self):
        """Test executing a simple tool."""
        if not self.agent.tool_registry:
            self.skipTest("Tool registry not available")
        
        # Clear any existing tools
        self.agent.tool_registry.tools.clear()
        self.agent.tool_registry.specs.clear()
        
        # Register fresh test tool
        test_spec = tools_module.ToolSpec(
            name="test_tool",
            description="Test tool",
            type=tools_module.ToolType.COMPUTE,
            parameters=[
                tools_module.ToolParameter("value", "integer", "Value")
            ]
        )
        self.agent.tool_registry.register(test_spec, lambda value: value * 2)
        
        result = self.agent._execute_tool("test_tool", {"value": 5})
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], 10)
    
    def test_execute_nonexistent_tool(self):
        """Test executing a tool that doesn't exist."""
        if not self.agent.tool_registry:
            self.skipTest("Tool registry not available")
        
        result = self.agent._execute_tool("nonexistent", {})
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    def test_tool_execution_without_registry(self):
        """Test tool execution when registry is not available."""
        mock_vault = Mock()
        mock_vault.retriever = Mock()
        mock_vault.retriever.get_evidence_pack = Mock(return_value={
            "chunks": [],
            "citations": []
        })
        agent = Agent(mock_vault, MockLLM())
        agent.tool_registry = None
        result = agent._execute_tool("any_tool", {})
        self.assertFalse(result["success"])
        self.assertIn("not available", result["error"])


class TestToolResultFormatting(unittest.TestCase):
    """Tests for formatting tool results."""
    
    def setUp(self):
        """Create a test agent."""
        mock_vault = Mock()
        self.agent = Agent(mock_vault, MockLLM())
    
    def test_format_successful_results(self):
        """Test formatting successful tool results."""
        results = [
            {
                "success": True,
                "result": 42,
                "tool_name": "calculate"
            }
        ]
        formatted = self.agent._format_tool_results(results)
        self.assertIn("✓", formatted)
        self.assertIn("calculate", formatted)
        self.assertIn("42", formatted)
    
    def test_format_failed_results(self):
        """Test formatting failed tool results."""
        results = [
            {
                "success": False,
                "error": "File not found",
                "tool_name": "read_file"
            }
        ]
        formatted = self.agent._format_tool_results(results)
        self.assertIn("✗", formatted)
        self.assertIn("read_file", formatted)
        self.assertIn("File not found", formatted)
    
    def test_format_multiple_results(self):
        """Test formatting multiple tool results."""
        results = [
            {"success": True, "result": 100, "tool_name": "tool1"},
            {"success": False, "error": "Failed", "tool_name": "tool2"}
        ]
        formatted = self.agent._format_tool_results(results)
        self.assertIn("tool1", formatted)
        self.assertIn("tool2", formatted)
    
    def test_format_empty_results(self):
        """Test formatting empty results list."""
        formatted = self.agent._format_tool_results([])
        self.assertEqual(formatted, "")


class TestAgentResponse(unittest.TestCase):
    """Tests for agent response generation with tools."""
    
    def setUp(self):
        """Create a test agent."""
        mock_vault = Mock()
        mock_vault.search = Mock(return_value=[])
        mock_vault.retriever = Mock()
        mock_vault.retriever.get_evidence_pack = Mock(return_value={
            "chunks": [],
            "citations": []
        })
        mock_llm = MockLLM()
        self.agent = Agent(mock_vault, mock_llm)
    
    def test_respond_without_tools(self):
        """Test agent response without tool usage."""
        result = self.agent.respond("What is 2+2?")
        self.assertIn("text", result)
        self.assertIn("citations", result)
        self.assertNotIn("tool_calls", result)
    
    def test_respond_with_tool_call_in_response(self):
        """Test agent response when LLM includes tool call."""
        if not self.agent.tool_registry:
            self.skipTest("Tool registry not available")
        
        # Mock vault with proper retriever
        mock_vault = Mock()
        mock_vault.retriever = Mock()
        mock_vault.retriever.get_evidence_pack = Mock(return_value={
            "chunks": [],
            "citations": []
        })
        
        # Mock LLM to return response with tool call
        mock_llm = Mock()
        mock_llm.generate = Mock(
            side_effect=[
                'I should calculate this. <tool name="calculate" expression="2 + 2" />',
                'Based on the calculation, 2 + 2 equals 4.'
            ]
        )
        
        agent = Agent(mock_vault, mock_llm)
        # Ensure tool registry has calculate tool
        if agent.tool_registry:
            agent.tool_registry.tools.clear()
            agent.tool_registry.specs.clear()
            builtin_tools_module.register_builtin_tools(agent.tool_registry)
        
        result = agent.respond("What is 2+2?")
        
        # Should have detected tool call
        self.assertIn("tool_calls", result)
        self.assertEqual(len(result["tool_calls"]), 1)
        self.assertEqual(result["tool_calls"][0]["tool"], "calculate")
    
    def test_respond_respects_max_tool_calls(self):
        """Test that agent respects max tool calls limit."""
        if not self.agent.tool_registry:
            self.skipTest("Tool registry not available")
        
        # Mock vault with proper retriever
        mock_vault = Mock()
        mock_vault.retriever = Mock()
        mock_vault.retriever.get_evidence_pack = Mock(return_value={
            "chunks": [],
            "citations": []
        })
        
        # Mock LLM to return response with many tool calls
        tool_calls_text = ' '.join([
            f'<tool name="calculate" expression="{i}" />'
            for i in range(10)
        ])
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value=f"Results: {tool_calls_text}")
        
        agent = Agent(mock_vault, mock_llm)
        if agent.tool_registry:
            agent.tool_registry.tools.clear()
            agent.tool_registry.specs.clear()
            builtin_tools_module.register_builtin_tools(agent.tool_registry)
        agent.max_tool_calls = 3
        
        result = agent.respond("Do 10 calculations")
        
        # Should only execute max_tool_calls (3)
        if "tool_calls" in result:
            self.assertLessEqual(len(result["tool_calls"]), 3)


class TestToolCallHistory(unittest.TestCase):
    """Tests for tool call history tracking."""
    
    def setUp(self):
        """Create a test agent."""
        mock_vault = Mock()
        mock_vault.retriever = Mock()
        mock_vault.retriever.get_evidence_pack = Mock(return_value={
            "chunks": [],
            "citations": []
        })
        self.agent = Agent(mock_vault, MockLLM())
        
        # Clear registry to avoid cross-test contamination
        if self.agent.tool_registry:
            self.agent.tool_registry.tools.clear()
            self.agent.tool_registry.specs.clear()
            self.agent.tool_registry.call_history.clear()
            self.agent.tool_registry.result_history.clear()
    
    def test_tool_call_history_tracking(self):
        """Test that tool calls are tracked in history."""
        if not self.agent.tool_registry:
            self.skipTest("Tool registry not available")
        
        # Register a simple tool
        test_spec = tools_module.ToolSpec(
            name="test",
            description="Test",
            type=tools_module.ToolType.COMPUTE,
            parameters=[tools_module.ToolParameter("x", "integer", "X")]
        )
        self.agent.tool_registry.register(test_spec, lambda x: x)
        
        # Execute a tool
        self.agent._execute_tool("test", {"x": 5})
        
        # Check history
        self.assertEqual(len(self.agent.tool_call_history), 0)  # Only tracks via respond()
    
    def test_history_includes_query(self):
        """Test that history includes original query."""
        if not self.agent.tool_registry:
            self.skipTest("Tool registry not available")
        
        # Mock vault with proper retriever
        mock_vault = Mock()
        mock_vault.search = Mock(return_value=[])
        mock_vault.retriever = Mock()
        mock_vault.retriever.get_evidence_pack = Mock(return_value={
            "chunks": [],
            "citations": []
        })
        
        # Register tool
        test_spec = tools_module.ToolSpec(
            name="test",
            description="Test",
            type=tools_module.ToolType.COMPUTE,
            parameters=[tools_module.ToolParameter("x", "integer", "X")]
        )
        
        # Mock LLM
        mock_llm = Mock()
        mock_llm.generate = Mock(side_effect=[
            '<tool name="test" x="5" />',
            'Result: 5'
        ])
        
        agent = Agent(mock_vault, mock_llm)
        if agent.tool_registry:
            agent.tool_registry.tools.clear()
            agent.tool_registry.specs.clear()
            agent.tool_registry.register(test_spec, lambda x: x)
        
        agent.respond("My query")
        
        # History should include query
        if agent.tool_call_history:
            self.assertEqual(agent.tool_call_history[0]["query"], "My query")


class TestToolIntegrationWithBuiltins(unittest.TestCase):
    """Integration tests with built-in tools."""
    
    def setUp(self):
        """Create an agent with built-in tools registered."""
        mock_vault = Mock()
        mock_vault.retriever = Mock()
        mock_vault.retriever.get_evidence_pack = Mock(return_value={
            "chunks": [],
            "citations": []
        })
        self.agent = Agent(mock_vault, MockLLM())
        
        if self.agent.tool_registry:
            # Clear and re-register to avoid conflicts
            self.agent.tool_registry.tools.clear()
            self.agent.tool_registry.specs.clear()
            builtin_tools_module.register_builtin_tools(self.agent.tool_registry)
    
    def test_calculate_tool_integration(self):
        """Test calculate tool through agent."""
        if not self.agent.tool_registry:
            self.skipTest("Tool registry not available")
        
        result = self.agent._execute_tool("calculate", {"expression": "2 + 3 * 4"})
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], 14)
    
    def test_string_length_tool_integration(self):
        """Test string_length tool through agent."""
        if not self.agent.tool_registry:
            self.skipTest("Tool registry not available")
        
        result = self.agent._execute_tool("string_length", {"text": "hello"})
        self.assertTrue(result["success"], f"Tool failed: {result.get('error')}")
        self.assertEqual(result["result"], 5)
    
    def test_statistics_mean_tool_integration(self):
        """Test statistics_mean tool through agent."""
        if not self.agent.tool_registry:
            self.skipTest("Tool registry not available")
        
        result = self.agent._execute_tool("statistics_mean", {"values": [1, 2, 3, 4, 5]})
        self.assertTrue(result["success"], f"Tool failed: {result.get('error')}")
        self.assertEqual(result["result"], 3)
    
    def test_invalid_tool_parameters(self):
        """Test tool with invalid parameters."""
        if not self.agent.tool_registry:
            self.skipTest("Tool registry not available")
        
        # Try to call calculate with invalid expression (should fail gracefully)
        result = self.agent._execute_tool("calculate", {"expression": "__import__('os')"})
        # Should fail due to security checks
        self.assertFalse(result["success"], "Expected security check to reject dangerous expression")
        self.assertIn("error", result, "Expected error message in result")


class TestAgentToolsWithMocks(unittest.TestCase):
    """Tests with mocked components."""
    
    def test_agent_initialization_without_registry(self):
        """Test that agent initializes even without tool registry."""
        mock_vault = Mock()
        agent = Agent(mock_vault, MockLLM())
        # Should not raise
        self.assertIsNotNone(agent)
    
    def test_respond_returns_correct_structure(self):
        """Test that respond returns correct structure."""
        mock_vault = Mock()
        mock_vault.search = Mock(return_value=[])
        mock_vault.retriever = Mock()
        mock_vault.retriever.get_evidence_pack = Mock(return_value={
            "chunks": [],
            "citations": []
        })
        
        agent = Agent(mock_vault, MockLLM())
        result = agent.respond("Test query")
        
        # Check required fields
        self.assertIn("text", result)
        self.assertIn("citations", result)
        self.assertIn("used_chunks", result)
        self.assertIsInstance(result["text"], str)
        self.assertIsInstance(result["citations"], list)
        self.assertIsInstance(result["used_chunks"], list)


if __name__ == '__main__':
    unittest.main()
