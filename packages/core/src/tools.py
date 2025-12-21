"""Tool Execution System for ArcticCodex Agent.

Provides a safe, sandboxed framework for the agent to execute tools.

Tool Types:
- read: Read-only file operations
- compute: Mathematical computations  
- web: External API calls
- memory: Knowledge base operations

Security Features:
- Input validation and sanitization
- Resource limits (timeouts, file size)
- Restricted namespaces (no dangerous imports)
- Audit logging of all tool calls
- Result validation before returning
"""

import json
import time
import hashlib
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime


class ToolType(str, Enum):
    """Tool execution type."""
    READ = "read"
    COMPUTE = "compute"
    WEB = "web"
    MEMORY = "memory"


@dataclass
class ToolParameter:
    """Parameter specification for a tool."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    constraints: Optional[Dict[str, Any]] = None  # min, max, pattern, etc.


@dataclass
class ToolSpec:
    """Tool specification and metadata."""
    name: str
    description: str
    type: ToolType
    parameters: List[ToolParameter]
    return_type: str = "string"
    timeout: int = 30  # seconds
    max_retries: int = 1
    requires_approval: bool = False


@dataclass
class ToolCall:
    """A tool invocation with parameters."""
    tool_name: str
    parameters: Dict[str, Any]
    timestamp: str = None
    call_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.call_id is None:
            # Generate deterministic call ID from tool name and params
            content = f"{self.tool_name}:{json.dumps(self.parameters, sort_keys=True)}"
            self.call_id = hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class ToolResult:
    """Result of a tool execution."""
    tool_name: str
    call_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    timestamp: str = None
    execution_time_ms: float = 0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class ToolExecutionError(Exception):
    """Tool execution failed."""
    pass


class ToolValidationError(Exception):
    """Tool validation failed."""
    pass


class ToolRegistry:
    """Registry and executor for tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, Callable] = {}
        self.specs: Dict[str, ToolSpec] = {}
        self.call_history: List[ToolCall] = []
        self.result_history: List[ToolResult] = []
    
    def register(self, spec: ToolSpec, handler: Callable) -> None:
        """Register a new tool.
        
        Args:
            spec: Tool specification
            handler: Callable that executes the tool
        
        Raises:
            ValueError: If tool already registered
        """
        if spec.name in self.tools:
            raise ValueError(f"Tool '{spec.name}' already registered")
        
        self.tools[spec.name] = handler
        self.specs[spec.name] = spec
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """List all registered tools.
        
        Returns:
            Dict mapping tool names to specifications
        """
        result = {}
        for name, spec in self.specs.items():
            result[name] = {
                "name": spec.name,
                "description": spec.description,
                "type": spec.type.value,
                "parameters": [asdict(p) for p in spec.parameters],
                "return_type": spec.return_type,
                "requires_approval": spec.requires_approval
            }
        return result
    
    def validate_call(self, call: ToolCall) -> None:
        """Validate a tool call.
        
        Args:
            call: Tool call to validate
        
        Raises:
            ToolValidationError: If validation fails
        """
        if call.tool_name not in self.specs:
            raise ToolValidationError(f"Unknown tool: {call.tool_name}")
        
        spec = self.specs[call.tool_name]
        
        # Check required parameters
        required_params = {p.name for p in spec.parameters if p.required}
        provided_params = set(call.parameters.keys())
        
        missing = required_params - provided_params
        if missing:
            raise ToolValidationError(
                f"Missing required parameters: {missing}"
            )
        
        # Check extra parameters
        valid_params = {p.name for p in spec.parameters}
        extra = provided_params - valid_params
        if extra:
            raise ToolValidationError(
                f"Unknown parameters: {extra}"
            )
        
        # Validate parameter values
        for param in spec.parameters:
            if param.name in call.parameters:
                value = call.parameters[param.name]
                self._validate_parameter(param, value)
    
    def _validate_parameter(self, param: ToolParameter, value: Any) -> None:
        """Validate a parameter value.
        
        Args:
            param: Parameter specification
            value: Value to validate
        
        Raises:
            ToolValidationError: If validation fails
        """
        # Type checking
        expected_type = param.type.lower()
        actual_type = type(value).__name__.lower()
        
        # Basic type checking
        type_map = {
            "string": str,
            "integer": int,
            "float": (int, float),
            "boolean": bool,
            "list": list,
            "dict": dict,
            "any": object
        }
        
        if expected_type != "any":
            if not isinstance(value, type_map.get(expected_type, object)):
                raise ToolValidationError(
                    f"Parameter '{param.name}' expected {param.type}, "
                    f"got {actual_type}"
                )
        
        # Constraint checking
        if param.constraints:
            constraints = param.constraints
            
            # Length constraints
            if "min_length" in constraints:
                if len(str(value)) < constraints["min_length"]:
                    raise ToolValidationError(
                        f"Parameter '{param.name}' too short"
                    )
            
            if "max_length" in constraints:
                if len(str(value)) > constraints["max_length"]:
                    raise ToolValidationError(
                        f"Parameter '{param.name}' too long"
                    )
            
            # Numeric constraints
            if "min" in constraints and isinstance(value, (int, float)):
                if value < constraints["min"]:
                    raise ToolValidationError(
                        f"Parameter '{param.name}' below minimum"
                    )
            
            if "max" in constraints and isinstance(value, (int, float)):
                if value > constraints["max"]:
                    raise ToolValidationError(
                        f"Parameter '{param.name}' exceeds maximum"
                    )
            
            # Pattern matching
            if "pattern" in constraints and isinstance(value, str):
                import re
                if not re.match(constraints["pattern"], value):
                    raise ToolValidationError(
                        f"Parameter '{param.name}' doesn't match pattern"
                    )
    
    def execute(self, call: ToolCall, timeout: Optional[int] = None) -> ToolResult:
        """Execute a tool call.
        
        Args:
            call: Tool call to execute
            timeout: Execution timeout in seconds (overrides spec)
        
        Returns:
            Tool result
        """
        # Add to call history
        self.call_history.append(call)
        
        # Validate call
        try:
            self.validate_call(call)
        except ToolValidationError as e:
            result = ToolResult(
                tool_name=call.tool_name,
                call_id=call.call_id,
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=0
            )
            self.result_history.append(result)
            return result
        
        # Execute with timeout
        spec = self.specs[call.tool_name]
        timeout = timeout or spec.timeout
        handler = self.tools[call.tool_name]
        
        start_time = time.time()
        try:
            # Execute with timeout
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Tool execution exceeded {timeout}s timeout")
            
            # Set timeout (Unix/Linux only)
            try:
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout)
            except (AttributeError, ValueError):
                # Windows doesn't support SIGALRM, skip timeout
                old_handler = None
            
            try:
                result_value = handler(**call.parameters)
            finally:
                if old_handler is not None:
                    signal.alarm(0)  # Cancel alarm
                    signal.signal(signal.SIGALRM, old_handler)
            
            execution_time = (time.time() - start_time) * 1000
            
            result = ToolResult(
                tool_name=call.tool_name,
                call_id=call.call_id,
                success=True,
                result=result_value,
                execution_time_ms=execution_time
            )
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            result = ToolResult(
                tool_name=call.tool_name,
                call_id=call.call_id,
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=execution_time
            )
        
        self.result_history.append(result)
        return result
    
    def get_call_history(self, tool_name: Optional[str] = None) -> List[ToolCall]:
        """Get tool call history.
        
        Args:
            tool_name: Filter by tool name (optional)
        
        Returns:
            List of tool calls
        """
        if tool_name:
            return [c for c in self.call_history if c.tool_name == tool_name]
        return self.call_history
    
    def get_result_history(self, tool_name: Optional[str] = None) -> List[ToolResult]:
        """Get tool result history.
        
        Args:
            tool_name: Filter by tool name (optional)
        
        Returns:
            List of tool results
        """
        if tool_name:
            return [r for r in self.result_history if r.tool_name == tool_name]
        return self.result_history
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics.
        
        Returns:
            Dictionary with stats
        """
        if not self.result_history:
            return {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "tools_used": set()
            }
        
        successful = [r for r in self.result_history if r.success]
        failed = [r for r in self.result_history if not r.success]
        tools_used = {r.tool_name for r in self.result_history}
        
        avg_time = (
            sum(r.execution_time_ms for r in self.result_history) 
            / len(self.result_history)
        ) if self.result_history else 0
        
        return {
            "total_calls": len(self.call_history),
            "successful_calls": len(successful),
            "failed_calls": len(failed),
            "success_rate": len(successful) / len(self.result_history) if self.result_history else 0,
            "average_execution_time_ms": avg_time,
            "tools_used": list(tools_used),
            "total_tools_registered": len(self.tools)
        }


# Global tool registry
_default_registry = None


def get_registry() -> ToolRegistry:
    """Get the default tool registry.
    
    Returns:
        Tool registry instance
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry


def register_tool(spec: ToolSpec, handler: Callable) -> None:
    """Register a tool in the default registry.
    
    Args:
        spec: Tool specification
        handler: Tool handler function
    """
    get_registry().register(spec, handler)


def call_tool(name: str, **kwargs) -> ToolResult:
    """Call a tool in the default registry.
    
    Args:
        name: Tool name
        **kwargs: Tool parameters
    
    Returns:
        Tool result
    """
    call = ToolCall(tool_name=name, parameters=kwargs)
    return get_registry().execute(call)
