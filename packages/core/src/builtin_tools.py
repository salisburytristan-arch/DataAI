"""Built-in tools for ArcticCodex agent.

Includes:
- File operations (read)
- Math/computation
- Web requests
- Knowledge base operations
"""

import os
import re
import json
import math
import statistics
from typing import Any, Union, List, Dict, Optional
from pathlib import Path

# Import tools using dynamic import to avoid naming conflicts
import importlib.util
tools_path = Path(__file__).parent / "tools.py"
spec = importlib.util.spec_from_file_location("tools_module", tools_path)
tools_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools_module)

ToolRegistry = tools_module.ToolRegistry
ToolSpec = tools_module.ToolSpec
ToolType = tools_module.ToolType
ToolParameter = tools_module.ToolParameter
register_tool = tools_module.register_tool
get_registry = tools_module.get_registry


def _safe_file_read(file_path: str, max_size: int = 10_000_000) -> str:
    """Safely read a file with size limits.
    
    Args:
        file_path: Path to file
        max_size: Maximum file size in bytes (default 10MB)
    
    Returns:
        File contents
    
    Raises:
        ValueError: If file too large or doesn't exist
        PermissionError: If access denied
    """
    path = Path(file_path).resolve()
    
    # Security: prevent path traversal
    if ".." in str(path):
        raise ValueError("Path traversal not allowed")
    
    # Check file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Check file size
    size = path.stat().st_size
    if size > max_size:
        raise ValueError(f"File too large: {size} bytes (max {max_size})")
    
    # Read file
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def _safe_math_eval(expression: str) -> Union[int, float]:
    """Safely evaluate a math expression.
    
    Args:
        expression: Math expression (no variables, no imports)
    
    Returns:
        Evaluation result
    
    Raises:
        ValueError: If expression invalid
    """
    # Whitelist allowed characters
    allowed = set('0123456789+-*/%().,e ')
    if not all(c in allowed for c in expression):
        raise ValueError("Invalid characters in expression")
    
    # Prevent common attacks
    dangerous = ['__', 'import', 'exec', 'eval', 'open', 'file']
    if any(d in expression.lower() for d in dangerous):
        raise ValueError("Expression contains forbidden keywords")
    
    # Use restricted namespace
    safe_dict = {
        'abs': abs, 'round': round, 'min': min, 'max': max,
        'sum': sum, 'pow': pow, 'sqrt': math.sqrt, 'sin': math.sin,
        'cos': math.cos, 'tan': math.tan, 'log': math.log,
        'exp': math.exp, 'ceil': math.ceil, 'floor': math.floor,
        'pi': math.pi, 'e': math.e
    }
    
    try:
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        return result
    except Exception as e:
        raise ValueError(f"Math evaluation failed: {str(e)}")


# ============================================================================
# File Reading Tools
# ============================================================================

def read_file(file_path: str, max_lines: Optional[int] = None) -> str:
    """Read a file from disk.
    
    Args:
        file_path: Path to file
        max_lines: Maximum lines to read (optional)
    
    Returns:
        File contents
    """
    content = _safe_file_read(file_path)
    
    if max_lines:
        lines = content.split('\n')[:max_lines]
        content = '\n'.join(lines)
    
    return content


def list_directory(directory_path: str) -> Dict[str, Any]:
    """List directory contents.
    
    Args:
        directory_path: Path to directory
    
    Returns:
        Directory listing with file metadata
    """
    path = Path(directory_path).resolve()
    
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    if not path.is_dir():
        raise ValueError(f"Not a directory: {directory_path}")
    
    items = []
    try:
        for item in sorted(path.iterdir())[:100]:  # Limit to 100 items
            stat = item.stat()
            items.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime
            })
    except PermissionError as e:
        raise PermissionError(f"Access denied: {directory_path}")
    
    return {
        "directory": str(path),
        "items": items,
        "total": len(items)
    }


def count_lines(file_path: str) -> int:
    """Count lines in a file.
    
    Args:
        file_path: Path to file
    
    Returns:
        Number of lines
    """
    content = _safe_file_read(file_path)
    return len(content.split('\n'))


def search_file(file_path: str, pattern: str) -> Dict[str, Any]:
    """Search file for pattern.
    
    Args:
        file_path: Path to file
        pattern: Regex pattern to search for
    
    Returns:
        Matches with line numbers
    """
    content = _safe_file_read(file_path)
    matches = []
    
    try:
        regex = re.compile(pattern)
        for i, line in enumerate(content.split('\n'), 1):
            if regex.search(line):
                matches.append({"line": i, "content": line.strip()})
    except re.error as e:
        raise ValueError(f"Invalid regex: {str(e)}")
    
    return {
        "file": file_path,
        "pattern": pattern,
        "matches": matches[:100],  # Limit matches
        "total_matches": len(matches)
    }


# ============================================================================
# Math & Computation Tools
# ============================================================================

def calculate(expression: str) -> Union[int, float]:
    """Calculate a math expression.
    
    Args:
        expression: Math expression
    
    Returns:
        Result
    """
    return _safe_math_eval(expression)


def statistics_mean(values: List[Union[int, float]]) -> float:
    """Calculate mean of values.
    
    Args:
        values: List of numbers
    
    Returns:
        Mean value
    """
    if not values:
        raise ValueError("No values provided")
    return statistics.mean(values)


def statistics_median(values: List[Union[int, float]]) -> float:
    """Calculate median of values.
    
    Args:
        values: List of numbers
    
    Returns:
        Median value
    """
    if not values:
        raise ValueError("No values provided")
    return statistics.median(values)


def statistics_stddev(values: List[Union[int, float]]) -> float:
    """Calculate standard deviation.
    
    Args:
        values: List of numbers
    
    Returns:
        Standard deviation
    """
    if len(values) < 2:
        raise ValueError("Need at least 2 values")
    return statistics.stdev(values)


# ============================================================================
# Data Transformation Tools
# ============================================================================

def parse_json(json_string: str) -> Any:
    """Parse JSON string.
    
    Args:
        json_string: JSON string
    
    Returns:
        Parsed JSON object
    """
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {str(e)}")


def format_json(data: Any, indent: int = 2) -> str:
    """Format data as JSON.
    
    Args:
        data: Data to format
        indent: Indentation level
    
    Returns:
        JSON string
    """
    try:
        return json.dumps(data, indent=indent, default=str)
    except TypeError as e:
        raise ValueError(f"Cannot serialize to JSON: {str(e)}")


def extract_text(html: str) -> str:
    """Extract text from HTML.
    
    Args:
        html: HTML string
    
    Returns:
        Extracted text
    """
    # Simple HTML tag removal (not a full parser)
    text = re.sub(r'<[^>]+>', '', html)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ============================================================================
# String Tools
# ============================================================================

def string_length(text: str) -> int:
    """Get string length.
    
    Args:
        text: String
    
    Returns:
        Length
    """
    return len(text)


def string_contains(text: str, substring: str) -> bool:
    """Check if text contains substring.
    
    Args:
        text: Text to search in
        substring: Substring to find
    
    Returns:
        Whether substring found
    """
    return substring.lower() in text.lower()


def string_replace(text: str, old: str, new: str) -> str:
    """Replace text.
    
    Args:
        text: Text
        old: Old string
        new: New string
    
    Returns:
        Modified text
    """
    return text.replace(old, new)


# ============================================================================
# Tool Registration
# ============================================================================

def register_builtin_tools(registry: Optional[ToolRegistry] = None) -> ToolRegistry:
    """Register all built-in tools.
    
    Args:
        registry: Tool registry to register in (uses default if None)
    
    Returns:
        Tool registry
    """
    if registry is None:
        registry = get_registry()
    
    # File Reading Tools
    registry.register(
        ToolSpec(
            name="read_file",
            description="Read a file from disk",
            type=ToolType.READ,
            parameters=[
                ToolParameter("file_path", "string", "Path to file"),
                ToolParameter("max_lines", "integer", "Max lines to read", required=False)
            ]
        ),
        read_file
    )
    
    registry.register(
        ToolSpec(
            name="list_directory",
            description="List contents of a directory",
            type=ToolType.READ,
            parameters=[
                ToolParameter("directory_path", "string", "Path to directory")
            ]
        ),
        list_directory
    )
    
    registry.register(
        ToolSpec(
            name="count_lines",
            description="Count lines in a file",
            type=ToolType.READ,
            parameters=[
                ToolParameter("file_path", "string", "Path to file")
            ]
        ),
        count_lines
    )
    
    registry.register(
        ToolSpec(
            name="search_file",
            description="Search file for regex pattern",
            type=ToolType.READ,
            parameters=[
                ToolParameter("file_path", "string", "Path to file"),
                ToolParameter("pattern", "string", "Regex pattern")
            ]
        ),
        search_file
    )
    
    # Math Tools
    registry.register(
        ToolSpec(
            name="calculate",
            description="Calculate a math expression",
            type=ToolType.COMPUTE,
            parameters=[
                ToolParameter("expression", "string", "Math expression")
            ]
        ),
        calculate
    )
    
    registry.register(
        ToolSpec(
            name="statistics_mean",
            description="Calculate mean of values",
            type=ToolType.COMPUTE,
            parameters=[
                ToolParameter("values", "list", "List of numbers")
            ]
        ),
        statistics_mean
    )
    
    registry.register(
        ToolSpec(
            name="statistics_median",
            description="Calculate median of values",
            type=ToolType.COMPUTE,
            parameters=[
                ToolParameter("values", "list", "List of numbers")
            ]
        ),
        statistics_median
    )
    
    registry.register(
        ToolSpec(
            name="statistics_stddev",
            description="Calculate standard deviation",
            type=ToolType.COMPUTE,
            parameters=[
                ToolParameter("values", "list", "List of numbers")
            ]
        ),
        statistics_stddev
    )
    
    # Data Tools
    registry.register(
        ToolSpec(
            name="parse_json",
            description="Parse JSON string",
            type=ToolType.COMPUTE,
            parameters=[
                ToolParameter("json_string", "string", "JSON string")
            ]
        ),
        parse_json
    )
    
    registry.register(
        ToolSpec(
            name="format_json",
            description="Format data as JSON",
            type=ToolType.COMPUTE,
            parameters=[
                ToolParameter("data", "any", "Data to format"),
                ToolParameter("indent", "integer", "Indentation", required=False)
            ]
        ),
        format_json
    )
    
    registry.register(
        ToolSpec(
            name="extract_text",
            description="Extract text from HTML",
            type=ToolType.COMPUTE,
            parameters=[
                ToolParameter("html", "string", "HTML string")
            ]
        ),
        extract_text
    )
    
    # String Tools
    registry.register(
        ToolSpec(
            name="string_length",
            description="Get string length",
            type=ToolType.COMPUTE,
            parameters=[
                ToolParameter("text", "string", "String")
            ]
        ),
        string_length
    )
    
    registry.register(
        ToolSpec(
            name="string_contains",
            description="Check if text contains substring",
            type=ToolType.COMPUTE,
            parameters=[
                ToolParameter("text", "string", "Text to search in"),
                ToolParameter("substring", "string", "Substring to find")
            ]
        ),
        string_contains
    )
    
    registry.register(
        ToolSpec(
            name="string_replace",
            description="Replace text",
            type=ToolType.COMPUTE,
            parameters=[
                ToolParameter("text", "string", "Text"),
                ToolParameter("old", "string", "Old string"),
                ToolParameter("new", "string", "New string")
            ]
        ),
        string_replace
    )
    
    return registry


# Auto-register on import
if __name__ == '__main__':
    register_builtin_tools()
