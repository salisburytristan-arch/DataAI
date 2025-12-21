"""Tests for tool execution system."""

import sys
import unittest
import tempfile
from pathlib import Path
from dataclasses import asdict

# Direct import from tools.py file
import importlib.util

tools_path = Path(__file__).parent.parent / "src" / "tools.py"
spec = importlib.util.spec_from_file_location("tools_module", tools_path)
tools_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools_module)

ToolType = tools_module.ToolType
ToolParameter = tools_module.ToolParameter
ToolSpec = tools_module.ToolSpec
ToolCall = tools_module.ToolCall
ToolResult = tools_module.ToolResult
ToolRegistry = tools_module.ToolRegistry
ToolValidationError = tools_module.ToolValidationError
ToolExecutionError = tools_module.ToolExecutionError
get_registry = tools_module.get_registry
register_tool = tools_module.register_tool
call_tool = tools_module.call_tool

# Now import builtin tools
builtin_tools_path = Path(__file__).parent.parent / "src" / "builtin_tools.py"
spec2 = importlib.util.spec_from_file_location("builtin_tools_module", builtin_tools_path)
builtin_tools_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(builtin_tools_module)

register_builtin_tools = builtin_tools_module.register_builtin_tools

# Create an alias for easier use in tests
def register_builtin_tools_in_registry(registry):
    """Register builtin tools in a specific registry."""
    builtin_tools_module.register_builtin_tools(registry)


class TestToolType(unittest.TestCase):
    """Tests for ToolType enum."""
    
    def test_tool_types_exist(self):
        """Test all tool types defined."""
        self.assertEqual(ToolType.READ.value, "read")
        self.assertEqual(ToolType.COMPUTE.value, "compute")
        self.assertEqual(ToolType.WEB.value, "web")
        self.assertEqual(ToolType.MEMORY.value, "memory")


class TestToolParameter(unittest.TestCase):
    """Tests for ToolParameter."""
    
    def test_required_parameter(self):
        """Test required parameter."""
        param = ToolParameter("input", "string", "An input")
        self.assertEqual(param.name, "input")
        self.assertEqual(param.type, "string")
        self.assertTrue(param.required)
        self.assertIsNone(param.default)
    
    def test_optional_parameter(self):
        """Test optional parameter."""
        param = ToolParameter("output", "string", "Output", required=False, default="default.txt")
        self.assertFalse(param.required)
        self.assertEqual(param.default, "default.txt")
    
    def test_parameter_with_constraints(self):
        """Test parameter with constraints."""
        param = ToolParameter(
            "count", "integer", "Count",
            constraints={"min": 1, "max": 100}
        )
        self.assertEqual(param.constraints["min"], 1)
        self.assertEqual(param.constraints["max"], 100)


class TestToolSpec(unittest.TestCase):
    """Tests for ToolSpec."""
    
    def test_simple_spec(self):
        """Test creating a simple tool spec."""
        spec = ToolSpec(
            name="test_tool",
            description="A test tool",
            type=ToolType.COMPUTE,
            parameters=[
                ToolParameter("x", "integer", "First number"),
                ToolParameter("y", "integer", "Second number")
            ]
        )
        self.assertEqual(spec.name, "test_tool")
        self.assertEqual(spec.type, ToolType.COMPUTE)
        self.assertEqual(len(spec.parameters), 2)
    
    def test_spec_with_defaults(self):
        """Test spec with default timeout."""
        spec = ToolSpec(
            name="test",
            description="Test",
            type=ToolType.READ,
            parameters=[]
        )
        self.assertEqual(spec.timeout, 30)  # default
        self.assertEqual(spec.max_retries, 1)  # default


class TestToolCall(unittest.TestCase):
    """Tests for ToolCall."""
    
    def test_tool_call_creation(self):
        """Test creating a tool call."""
        call = ToolCall(
            tool_name="read_file",
            parameters={"path": "/tmp/test.txt"}
        )
        self.assertEqual(call.tool_name, "read_file")
        self.assertEqual(call.parameters["path"], "/tmp/test.txt")
    
    def test_tool_call_has_id(self):
        """Test that tool calls have deterministic IDs."""
        call1 = ToolCall("tool", {"x": 1})
        call2 = ToolCall("tool", {"x": 1})
        self.assertEqual(call1.call_id, call2.call_id)
    
    def test_tool_call_id_differs_on_params(self):
        """Test that call IDs differ with different parameters."""
        call1 = ToolCall("tool", {"x": 1})
        call2 = ToolCall("tool", {"x": 2})
        self.assertNotEqual(call1.call_id, call2.call_id)


class TestToolResult(unittest.TestCase):
    """Tests for ToolResult."""
    
    def test_successful_result(self):
        """Test a successful result."""
        result = ToolResult(
            tool_name="calculate",
            call_id="abc123",
            success=True,
            result=42
        )
        self.assertTrue(result.success)
        self.assertEqual(result.result, 42)
        self.assertIsNone(result.error)
    
    def test_failed_result(self):
        """Test a failed result."""
        result = ToolResult(
            tool_name="calculate",
            call_id="abc123",
            success=False,
            result=None,
            error="Invalid expression"
        )
        self.assertFalse(result.success)
        self.assertIsNone(result.result)
        self.assertEqual(result.error, "Invalid expression")


class TestToolRegistry(unittest.TestCase):
    """Tests for ToolRegistry."""
    
    def setUp(self):
        """Set up test registry."""
        self.registry = ToolRegistry()
    
    def test_register_tool(self):
        """Test registering a tool."""
        spec = ToolSpec(
            name="add",
            description="Add two numbers",
            type=ToolType.COMPUTE,
            parameters=[
                ToolParameter("a", "integer", "First"),
                ToolParameter("b", "integer", "Second")
            ]
        )
        
        def add_handler(a, b):
            return a + b
        
        self.registry.register(spec, add_handler)
        tools = self.registry.list_tools()
        self.assertIn("add", tools)
    
    def test_list_tools(self):
        """Test listing registered tools."""
        spec1 = ToolSpec("tool1", "First", ToolType.READ, [])
        spec2 = ToolSpec("tool2", "Second", ToolType.COMPUTE, [])
        
        self.registry.register(spec1, lambda: "result1")
        self.registry.register(spec2, lambda: "result2")
        
        tools = self.registry.list_tools()
        self.assertEqual(len(tools), 2)
        self.assertIn("tool1", tools)
        self.assertIn("tool2", tools)
    
    def test_register_duplicate_raises_error(self):
        """Test registering duplicate tool name raises error."""
        spec = ToolSpec("dup", "Duplicate", ToolType.COMPUTE, [])
        self.registry.register(spec, lambda: None)
        
        # Registering again should raise
        with self.assertRaises(ValueError):
            self.registry.register(spec, lambda: None)


class TestToolValidation(unittest.TestCase):
    """Tests for tool validation."""
    
    def setUp(self):
        """Set up test registry."""
        self.registry = ToolRegistry()
    
    def test_validate_required_parameter(self):
        """Test validation of required parameters."""
        spec = ToolSpec(
            "test",
            "Test",
            ToolType.COMPUTE,
            [ToolParameter("x", "integer", "Required")]
        )
        self.registry.register(spec, lambda x: x)
        
        # Missing required parameter
        call = ToolCall("test", {})
        with self.assertRaises(ToolValidationError):
            self.registry.validate_call(call)
    
    def test_validate_type_string(self):
        """Test string type validation."""
        spec = ToolSpec(
            "test",
            "Test",
            ToolType.COMPUTE,
            [ToolParameter("text", "string", "Text")]
        )
        self.registry.register(spec, lambda text: text)
        
        # Valid string
        call = ToolCall("test", {"text": "hello"})
        self.registry.validate_call(call)  # Should not raise
        
        # Invalid type
        call = ToolCall("test", {"text": 123})
        with self.assertRaises(ToolValidationError):
            self.registry.validate_call(call)
    
    def test_validate_type_integer(self):
        """Test integer type validation."""
        spec = ToolSpec(
            "test",
            "Test",
            ToolType.COMPUTE,
            [ToolParameter("count", "integer", "Count")]
        )
        self.registry.register(spec, lambda count: count)
        
        # Valid integer
        call = ToolCall("test", {"count": 42})
        self.registry.validate_call(call)
        
        # Invalid type
        call = ToolCall("test", {"count": "not an int"})
        with self.assertRaises(ToolValidationError):
            self.registry.validate_call(call)
    
    def test_validate_type_list(self):
        """Test list type validation."""
        spec = ToolSpec(
            "test",
            "Test",
            ToolType.COMPUTE,
            [ToolParameter("items", "list", "Items")]
        )
        self.registry.register(spec, lambda items: items)
        
        # Valid list
        call = ToolCall("test", {"items": [1, 2, 3]})
        self.registry.validate_call(call)
        
        # Invalid type
        call = ToolCall("test", {"items": "not a list"})
        with self.assertRaises(ToolValidationError):
            self.registry.validate_call(call)
    
    def test_validate_constraint_min_length(self):
        """Test min_length constraint."""
        spec = ToolSpec(
            "test",
            "Test",
            ToolType.COMPUTE,
            [ToolParameter("text", "string", "Text", 
                          constraints={"min_length": 5})]
        )
        self.registry.register(spec, lambda text: text)
        
        # Valid
        call = ToolCall("test", {"text": "hello world"})
        self.registry.validate_call(call)
        
        # Invalid
        call = ToolCall("test", {"text": "hi"})
        with self.assertRaises(ToolValidationError):
            self.registry.validate_call(call)
    
    def test_validate_constraint_max_length(self):
        """Test max_length constraint."""
        spec = ToolSpec(
            "test",
            "Test",
            ToolType.COMPUTE,
            [ToolParameter("text", "string", "Text",
                          constraints={"max_length": 10})]
        )
        self.registry.register(spec, lambda text: text)
        
        # Valid
        call = ToolCall("test", {"text": "hello"})
        self.registry.validate_call(call)
        
        # Invalid
        call = ToolCall("test", {"text": "this is too long"})
        with self.assertRaises(ToolValidationError):
            self.registry.validate_call(call)
    
    def test_validate_constraint_min_max(self):
        """Test min/max constraints for numbers."""
        spec = ToolSpec(
            "test",
            "Test",
            ToolType.COMPUTE,
            [ToolParameter("count", "integer", "Count",
                          constraints={"min": 1, "max": 10})]
        )
        self.registry.register(spec, lambda count: count)
        
        # Valid
        call = ToolCall("test", {"count": 5})
        self.registry.validate_call(call)
        
        # Too small
        call = ToolCall("test", {"count": 0})
        with self.assertRaises(ToolValidationError):
            self.registry.validate_call(call)
        
        # Too large
        call = ToolCall("test", {"count": 11})
        with self.assertRaises(ToolValidationError):
            self.registry.validate_call(call)
    
    def test_validate_pattern(self):
        """Test regex pattern validation."""
        spec = ToolSpec(
            "test",
            "Test",
            ToolType.COMPUTE,
            [ToolParameter("email", "string", "Email",
                          constraints={"pattern": r"^[a-z]+@[a-z]+$"})]
        )
        self.registry.register(spec, lambda email: email)
        
        # Valid
        call = ToolCall("test", {"email": "user@domain"})
        self.registry.validate_call(call)
        
        # Invalid
        call = ToolCall("test", {"email": "not-an-email"})
        with self.assertRaises(ToolValidationError):
            self.registry.validate_call(call)
    
    def test_validate_extra_parameters(self):
        """Test that extra parameters are detected."""
        spec = ToolSpec(
            "test",
            "Test",
            ToolType.COMPUTE,
            [ToolParameter("x", "integer", "X")]
        )
        self.registry.register(spec, lambda x: x)
        
        # Extra parameter
        call = ToolCall("test", {"x": 1, "y": 2})
        with self.assertRaises(ToolValidationError):
            self.registry.validate_call(call)


class TestToolExecution(unittest.TestCase):
    """Tests for tool execution."""
    
    def setUp(self):
        """Set up test registry."""
        self.registry = ToolRegistry()
    
    def test_execute_simple_tool(self):
        """Test executing a simple tool."""
        spec = ToolSpec(
            "add",
            "Add numbers",
            ToolType.COMPUTE,
            [
                ToolParameter("a", "integer", "First"),
                ToolParameter("b", "integer", "Second")
            ]
        )
        
        def add_handler(a, b):
            return a + b
        
        self.registry.register(spec, add_handler)
        
        call = ToolCall("add", {"a": 3, "b": 4})
        result = self.registry.execute(call)
        
        self.assertTrue(result.success)
        self.assertEqual(result.result, 7)
        self.assertIsNone(result.error)
    
    def test_execute_tool_with_exception(self):
        """Test tool that raises exception."""
        spec = ToolSpec(
            "divide",
            "Divide",
            ToolType.COMPUTE,
            [
                ToolParameter("a", "integer", "Numerator"),
                ToolParameter("b", "integer", "Denominator")
            ]
        )
        
        def divide_handler(a, b):
            return a / b
        
        self.registry.register(spec, divide_handler)
        
        call = ToolCall("divide", {"a": 10, "b": 0})
        result = self.registry.execute(call)
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)
    
    def test_execute_nonexistent_tool(self):
        """Test executing a tool that doesn't exist."""
        call = ToolCall("nonexistent", {})
        result = self.registry.execute(call)
        self.assertFalse(result.success)
        self.assertIn("Unknown tool", result.error)
    
    def test_execute_with_validation_error(self):
        """Test that execution returns failure on validation error."""
        spec = ToolSpec(
            "test",
            "Test",
            ToolType.COMPUTE,
            [ToolParameter("x", "integer", "X")]
        )
        
        def handler(x):
            return x * 2
        
        self.registry.register(spec, handler)
        
        call = ToolCall("test", {"x": "not an int"})
        result = self.registry.execute(call)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)
    
    def test_execution_tracking(self):
        """Test that executions are tracked."""
        spec = ToolSpec(
            "track",
            "Track",
            ToolType.COMPUTE,
            [ToolParameter("x", "integer", "X")]
        )
        
        def handler(x):
            return x
        
        self.registry.register(spec, handler)
        
        call1 = ToolCall("track", {"x": 1})
        call2 = ToolCall("track", {"x": 2})
        
        result1 = self.registry.execute(call1)
        result2 = self.registry.execute(call2)
        
        history = self.registry.get_result_history()
        self.assertEqual(len(history), 2)
    
    def test_execution_timing(self):
        """Test that execution time is tracked."""
        spec = ToolSpec(
            "sleep",
            "Sleep",
            ToolType.COMPUTE,
            [ToolParameter("seconds", "float", "Seconds")]
        )
        
        import time
        
        def handler(seconds):
            time.sleep(seconds)
            return "done"
        
        self.registry.register(spec, handler)
        
        call = ToolCall("sleep", {"seconds": 0.1})
        result = self.registry.execute(call)
        
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.execution_time_ms, 100)


class TestCallHistory(unittest.TestCase):
    """Tests for call history tracking."""
    
    def setUp(self):
        """Set up test registry."""
        self.registry = ToolRegistry()
    
    def test_call_history(self):
        """Test that calls are recorded."""
        spec = ToolSpec("test", "Test", ToolType.COMPUTE, [])
        self.registry.register(spec, lambda: "result")
        
        call = ToolCall("test", {})
        self.registry.execute(call)
        
        history = self.registry.get_call_history()
        self.assertEqual(len(history), 1)
    
    def test_call_history_filtered(self):
        """Test filtering call history by tool name."""
        spec1 = ToolSpec("tool1", "Tool1", ToolType.COMPUTE, [])
        spec2 = ToolSpec("tool2", "Tool2", ToolType.COMPUTE, [])
        
        self.registry.register(spec1, lambda: 1)
        self.registry.register(spec2, lambda: 2)
        
        self.registry.execute(ToolCall("tool1", {}))
        self.registry.execute(ToolCall("tool2", {}))
        self.registry.execute(ToolCall("tool1", {}))
        
        history = self.registry.get_call_history("tool1")
        self.assertEqual(len(history), 2)


class TestStatistics(unittest.TestCase):
    """Tests for execution statistics."""
    
    def setUp(self):
        """Set up test registry."""
        self.registry = ToolRegistry()
    
    def test_stats_empty(self):
        """Test stats for empty registry."""
        stats = self.registry.get_stats()
        self.assertEqual(stats["total_calls"], 0)
        self.assertEqual(stats["successful_calls"], 0)
        self.assertEqual(stats["failed_calls"], 0)
    
    def test_stats_success_rate(self):
        """Test success rate calculation."""
        spec = ToolSpec("test", "Test", ToolType.COMPUTE, [
            ToolParameter("fail", "boolean", "Fail?")
        ])
        
        def handler(fail):
            if fail:
                raise ValueError("Failed")
            return "ok"
        
        self.registry.register(spec, handler)
        
        self.registry.execute(ToolCall("test", {"fail": False}))
        self.registry.execute(ToolCall("test", {"fail": True}))
        
        stats = self.registry.get_stats()
        self.assertEqual(stats["total_calls"], 2)
        self.assertEqual(stats["successful_calls"], 1)
        self.assertEqual(stats["failed_calls"], 1)


class TestBuiltinTools(unittest.TestCase):
    """Tests for built-in tools."""
    
    def setUp(self):
        """Set up with built-in tools registered."""
        # Use a fresh registry for builtin tools
        self.registry = ToolRegistry()
        register_builtin_tools_in_registry(self.registry)
    
    def test_calculate_tool(self):
        """Test calculate tool."""
        call = ToolCall("calculate", {"expression": "2 + 3 * 4"})
        result = self.registry.execute(call)
        self.assertTrue(result.success)
        self.assertEqual(result.result, 14)
    
    def test_calculate_invalid_expression(self):
        """Test calculate with invalid expression."""
        call = ToolCall("calculate", {"expression": "__import__('os')"})
        result = self.registry.execute(call)
        self.assertFalse(result.success)
    
    def test_string_length_tool(self):
        """Test string_length tool."""
        call = ToolCall("string_length", {"text": "hello"})
        result = self.registry.execute(call)
        self.assertTrue(result.success)
        self.assertEqual(result.result, 5)
    
    def test_string_contains_tool(self):
        """Test string_contains tool."""
        call = ToolCall("string_contains", {
            "text": "Hello World",
            "substring": "world"
        })
        result = self.registry.execute(call)
        self.assertTrue(result.success)
        self.assertTrue(result.result)
    
    def test_string_replace_tool(self):
        """Test string_replace tool."""
        call = ToolCall("string_replace", {
            "text": "hello world",
            "old": "world",
            "new": "there"
        })
        result = self.registry.execute(call)
        self.assertTrue(result.success)
        self.assertEqual(result.result, "hello there")
    
    def test_statistics_mean_tool(self):
        """Test statistics_mean tool."""
        call = ToolCall("statistics_mean", {"values": [1, 2, 3, 4, 5]})
        result = self.registry.execute(call)
        self.assertTrue(result.success)
        self.assertEqual(result.result, 3)
    
    def test_parse_json_tool(self):
        """Test parse_json tool."""
        call = ToolCall("parse_json", {
            "json_string": '{"key": "value", "number": 42}'
        })
        result = self.registry.execute(call)
        self.assertTrue(result.success)
        self.assertEqual(result.result["key"], "value")
        self.assertEqual(result.result["number"], 42)
    
    def test_format_json_tool(self):
        """Test format_json tool."""
        call = ToolCall("format_json", {
            "data": {"name": "test", "value": 123}
        })
        result = self.registry.execute(call)
        self.assertTrue(result.success)
        self.assertIn('"name"', result.result)
        self.assertIn('"test"', result.result)
    
    def test_read_file_tool(self):
        """Test read_file tool."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            f.flush()
            temp_path = f.name
        
        try:
            call = ToolCall("read_file", {"file_path": temp_path})
            result = self.registry.execute(call)
            self.assertTrue(result.success)
            self.assertEqual(result.result, "test content")
        finally:
            Path(temp_path).unlink()
    
    def test_read_file_not_found(self):
        """Test read_file with non-existent file."""
        call = ToolCall("read_file", {"file_path": "/nonexistent/file.txt"})
        result = self.registry.execute(call)
        self.assertFalse(result.success)
    
    def test_list_directory_tool(self):
        """Test list_directory tool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "file1.txt").touch()
            Path(tmpdir, "file2.txt").touch()
            
            call = ToolCall("list_directory", {"directory_path": tmpdir})
            result = self.registry.execute(call)
            self.assertTrue(result.success)
            self.assertEqual(result.result["total"], 2)
    
    def test_count_lines_tool(self):
        """Test count_lines tool."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("line1\nline2\nline3")
            f.flush()
            temp_path = f.name
        
        try:
            call = ToolCall("count_lines", {"file_path": temp_path})
            result = self.registry.execute(call)
            self.assertTrue(result.success)
            self.assertEqual(result.result, 3)
        finally:
            Path(temp_path).unlink()
    
    def test_search_file_tool(self):
        """Test search_file tool."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("hello world\nhello there\ngoodbye")
            f.flush()
            temp_path = f.name
        
        try:
            call = ToolCall("search_file", {
                "file_path": temp_path,
                "pattern": "hello"
            })
            result = self.registry.execute(call)
            self.assertTrue(result.success)
            self.assertEqual(len(result.result["matches"]), 2)
        finally:
            Path(temp_path).unlink()


if __name__ == '__main__':
    unittest.main()
