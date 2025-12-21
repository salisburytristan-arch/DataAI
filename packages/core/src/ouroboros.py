"""
Phase XIV: Ouroboros Recursion (Self-Reference & Strange Loops)
Self-referential computation, Gödelian systems, tangled hierarchies.

Implements:
- STRANGE_LOOP: Self-referential systems (Hofstadter)
- GODEL_ENGINE: Incompleteness & self-reference
- QUINE_GENERATOR: Self-replicating code
- META_CIRCULAR_EVALUATOR: Interpreter that interprets itself
"""

from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import inspect


class LoopType(Enum):
    """Types of self-referential structures."""
    DIRECT = 'direct_recursion'           # f calls f
    MUTUAL = 'mutual_recursion'           # f calls g calls f
    META = 'meta_circular'                # Interpreter interprets itself
    GODEL = 'godelian'                    # Self-reference via encoding
    QUINE = 'quine'                       # Code that prints itself
    TANGLED_HIERARCHY = 'tangled_hierarchy'  # Levels fold back


@dataclass
class SelfReference:
    """A self-referential structure."""
    reference_id: str
    loop_type: LoopType
    depth: int  # Recursion depth
    is_productive: bool  # Does it terminate/produce value?
    
    def to_frame(self) -> Dict:
        return {
            'type': 'SELF_REFERENCE',
            'id': self.reference_id,
            'loop_type': self.loop_type.value,
            'depth': self.depth,
            'productive': self.is_productive
        }


class StrangeLoop:
    """
    Hofstadter's strange loop: hierarchical system where
    moving upward/downward through levels brings you back.
    
    Example: Self-awareness - consciousness observing itself.
    """
    
    @dataclass
    class Level:
        """Level in hierarchy."""
        level_id: int
        description: str
        next_level: Optional[int] = None  # Can loop back
        
    def __init__(self, name: str):
        self.name = name
        self.levels: List[StrangeLoop.Level] = []
        self.current_level: int = 0
    
    def add_level(self, description: str) -> int:
        """Add a level to hierarchy."""
        level_id = len(self.levels)
        level = StrangeLoop.Level(level_id, description)
        self.levels.append(level)
        return level_id
    
    def create_loop(self, from_level: int, to_level: int):
        """Create strange loop by connecting high level back to low level."""
        if from_level < len(self.levels):
            self.levels[from_level].next_level = to_level
    
    def traverse(self, steps: int) -> List[int]:
        """
        Traverse hierarchy. Will loop if strange loop exists.
        Returns path through levels.
        """
        path = [self.current_level]
        
        for _ in range(steps - 1):
            current = self.levels[self.current_level]
            
            if current.next_level is not None:
                # Explicit connection
                self.current_level = current.next_level
            elif self.current_level < len(self.levels) - 1:
                # Move up hierarchy
                self.current_level += 1
            else:
                # At top, loop back to bottom (strange loop)
                self.current_level = 0
            
            path.append(self.current_level)
        
        return path
    
    def detect_loop(self) -> Optional[Tuple[int, int]]:
        """
        Detect if strange loop exists.
        Returns (start, end) of loop, or None.
        """
        visited = set()
        current = 0
        
        for _ in range(len(self.levels) * 2):
            if current in visited:
                # Found loop
                return (current, current)
            
            visited.add(current)
            
            level = self.levels[current]
            if level.next_level is not None:
                current = level.next_level
            elif current < len(self.levels) - 1:
                current += 1
            else:
                current = 0
        
        return None
    
    def is_strange_loop(self) -> bool:
        """Check if this hierarchy contains a strange loop."""
        return self.detect_loop() is not None


class GodelEngine:
    """
    Implement Gödelian self-reference and incompleteness.
    System that can reason about itself.
    """
    
    def __init__(self):
        self.statements: Dict[int, str] = {}
        self.next_id = 1
    
    def encode_statement(self, statement: str) -> int:
        """
        Gödel numbering: encode statement as unique integer.
        Allows system to reference its own statements.
        """
        # Use hash as Gödel number
        godel_number = int(hashlib.sha256(statement.encode()).hexdigest(), 16) % (10**9)
        self.statements[godel_number] = statement
        return godel_number
    
    def decode_statement(self, godel_number: int) -> Optional[str]:
        """Decode Gödel number back to statement."""
        return self.statements.get(godel_number)
    
    def create_self_referential_statement(self) -> Tuple[int, str]:
        """
        Create statement that refers to itself.
        "This statement is unprovable."
        """
        # Template for self-reference
        template = "Statement #{godel_num} is unprovable in this system"
        
        # Encode template first
        temp_statement = template.format(godel_num=0)
        godel_num = self.encode_statement(temp_statement)
        
        # Update with actual Gödel number
        actual_statement = template.format(godel_num=godel_num)
        self.statements[godel_num] = actual_statement
        
        return godel_num, actual_statement
    
    def check_provability(self, godel_number: int) -> Dict:
        """
        Check if statement is provable.
        Self-referential statements create incompleteness.
        """
        statement = self.decode_statement(godel_number)
        
        if statement is None:
            return {'provable': None, 'reason': 'Unknown statement'}
        
        # Check if statement refers to itself
        if str(godel_number) in statement:
            # Self-referential!
            if "unprovable" in statement.lower():
                # Gödel's incompleteness: if provable, leads to contradiction
                return {
                    'provable': None,  # Undecidable
                    'reason': 'Self-referential undecidability (Gödel)',
                    'incomplete': True,
                    'godel_sentence': True
                }
        
        # Non-self-referential statements
        return {
            'provable': True,
            'reason': 'Not self-referential',
            'incomplete': False
        }
    
    def demonstrate_incompleteness(self) -> Dict:
        """
        Demonstrate Gödel's incompleteness theorem.
        Any sufficiently powerful system has unprovable truths.
        """
        godel_num, statement = self.create_self_referential_statement()
        provability = self.check_provability(godel_num)
        
        return {
            'godel_statement': statement,
            'godel_number': godel_num,
            'provability_status': provability,
            'theorem': 'First Incompleteness Theorem',
            'conclusion': 'System cannot prove all truths about itself'
        }


class QuineGenerator:
    """
    Generate quines: programs that output their own source code.
    Ultimate self-reference in computation.
    """
    
    @staticmethod
    def python_quine() -> str:
        """Generate a Python quine."""
        # Classic quine structure
        quine = 's=%r;print(s%%s)';s='s=%r;print(s%%s)';print(s%s)
        return quine
    
    @staticmethod
    def verify_quine(code: str) -> bool:
        """
        Verify if code is a valid quine.
        Execute it and check if output equals code.
        """
        try:
            # Capture output
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                exec(code)
            output = f.getvalue().strip()
            
            # Check if output equals original code
            return output == code.strip()
        
        except Exception as e:
            return False
    
    @staticmethod
    def create_frame_quine() -> Dict:
        """
        Create a quine in ForgeNumerics-S frame format.
        Frame that describes itself.
        """
        frame = {
            'type': 'QUINE_FRAME',
            'description': 'Frame that contains itself',
            'self': None  # Will be filled with frame itself
        }
        
        # Self-reference: frame contains itself
        frame['self'] = frame.copy()
        frame['self']['self'] = "... (recursive reference)"
        
        return frame


class MetaCircularEvaluator:
    """
    Interpreter that can interpret itself.
    Foundation of self-modifying AI.
    
    Simplified metacircular evaluator (based on LISP eval).
    """
    
    def __init__(self):
        self.environment: Dict[str, Any] = {
            # Built-in functions
            '+': lambda a, b: a + b,
            '-': lambda a, b: a - b,
            '*': lambda a, b: a * b,
            '/': lambda a, b: a / b,
            '=': lambda a, b: a == b,
            'if': None,  # Special form
            'lambda': None,  # Special form
            'eval': None,  # Will be set to self.eval
        }
        
        # Bootstrap: eval can eval itself
        self.environment['eval'] = self.eval
    
    def eval(self, expr, env: Optional[Dict] = None) -> Any:
        """
        Evaluate expression in environment.
        Can evaluate itself: eval(eval, env).
        """
        if env is None:
            env = self.environment
        
        # Atoms
        if isinstance(expr, (int, float)):
            return expr
        
        if isinstance(expr, str):
            # Variable lookup
            return env.get(expr, expr)
        
        if not isinstance(expr, (list, tuple)):
            return expr
        
        # Empty list
        if len(expr) == 0:
            return []
        
        # Special forms
        if expr[0] == 'if':
            # (if condition then else)
            _, condition, then_expr, else_expr = expr
            if self.eval(condition, env):
                return self.eval(then_expr, env)
            else:
                return self.eval(else_expr, env)
        
        if expr[0] == 'lambda':
            # (lambda (params) body)
            _, params, body = expr
            # Return closure
            return lambda *args: self.eval(body, {**env, **dict(zip(params, args))})
        
        if expr[0] == 'define':
            # (define name value)
            _, name, value = expr
            env[name] = self.eval(value, env)
            return None
        
        # Function application
        func = self.eval(expr[0], env)
        args = [self.eval(arg, env) for arg in expr[1:]]
        
        if callable(func):
            return func(*args)
        
        return None
    
    def eval_self(self) -> Any:
        """
        Metacircular evaluation: eval evaluates itself.
        The Ouroboros moment.
        """
        # Create expression that calls eval on itself
        expr = ['eval', ['lambda', ['x'], 'x'], 42]
        
        result = self.eval(expr)
        
        return {
            'expression': expr,
            'result': result,
            'metacircular': True,
            'self_interpreting': "Evaluator evaluated itself"
        }


class TangledHierarchy:
    """
    System where levels are not cleanly separated.
    Low-level can affect high-level and vice versa.
    
    Example: Brain (neurons) produces mind, mind controls neurons.
    """
    
    @dataclass
    class Entity:
        """Entity that exists at multiple levels."""
        entity_id: str
        level: int
        can_affect_levels: List[int]  # Which levels can it influence?
        
    def __init__(self):
        self.entities: List[TangledHierarchy.Entity] = []
    
    def add_entity(self, entity_id: str, level: int, affects: List[int]):
        """Add entity to hierarchy."""
        entity = TangledHierarchy.Entity(entity_id, level, affects)
        self.entities.append(entity)
    
    def is_tangled(self) -> bool:
        """
        Check if hierarchy is tangled.
        Tangled if low-level affects high-level or vice versa.
        """
        for entity in self.entities:
            for affected_level in entity.can_affect_levels:
                if affected_level != entity.level:
                    # Cross-level interaction = tangled
                    return True
        return False
    
    def find_causal_loops(self) -> List[List[str]]:
        """
        Find causal loops in tangled hierarchy.
        A affects B affects ... affects A.
        """
        loops = []
        
        def dfs(path: List[str], visited: set):
            current = path[-1]
            current_entity = next((e for e in self.entities if e.entity_id == current), None)
            
            if current_entity is None:
                return
            
            # Find entities this one affects
            for other in self.entities:
                if other.level in current_entity.can_affect_levels:
                    if other.entity_id in path:
                        # Found loop
                        loop_start = path.index(other.entity_id)
                        loop = path[loop_start:] + [other.entity_id]
                        if loop not in loops:
                            loops.append(loop)
                    elif other.entity_id not in visited:
                        dfs(path + [other.entity_id], visited | {other.entity_id})
        
        for entity in self.entities:
            dfs([entity.entity_id], {entity.entity_id})
        
        return loops


if __name__ == "__main__":
    print("=== Phase XIV: Ouroboros Recursion ===\n")
    
    # Strange loops
    print("=== Strange Loop: Consciousness ===")
    consciousness = StrangeLoop("Self-Awareness")
    
    # Build hierarchy
    consciousness.add_level("Neurons firing")
    consciousness.add_level("Neural patterns")
    consciousness.add_level("Thoughts emerge")
    consciousness.add_level("Self-awareness")
    consciousness.add_level("Observer observes itself")
    
    # Create strange loop: self-awareness loops back to neurons
    consciousness.create_loop(4, 0)
    
    print(f"Is strange loop: {consciousness.is_strange_loop()}")
    path = consciousness.traverse(10)
    print(f"Traversal path: {path}")
    print(f"Loop detected: {consciousness.detect_loop()}")
    
    # Gödel's incompleteness
    print("\n=== Gödel's Incompleteness ===")
    godel = GodelEngine()
    
    result = godel.demonstrate_incompleteness()
    print(f"Gödel statement: {result['godel_statement']}")
    print(f"Gödel number: {result['godel_number']}")
    print(f"Provability: {result['provability_status']['provable']}")
    print(f"Reason: {result['provability_status']['reason']}")
    print(f"Conclusion: {result['conclusion']}")
    
    # Quines
    print("\n=== Quine (Self-Replicating Code) ===")
    quine = QuineGenerator()
    
    python_quine = quine.python_quine()
    print(f"Python quine: {python_quine[:50]}...")
    print(f"Is valid quine: {quine.verify_quine(python_quine)}")
    
    frame_quine = quine.create_frame_quine()
    print(f"\nFrame quine type: {frame_quine['type']}")
    print(f"Self-reference depth: {1 if frame_quine['self'] else 0}")
    
    # Metacircular evaluator
    print("\n=== Metacircular Evaluator ===")
    evaluator = MetaCircularEvaluator()
    
    # Test basic evaluation
    result1 = evaluator.eval(['+', 2, 3])
    print(f"(+ 2 3) = {result1}")
    
    # Test lambda
    result2 = evaluator.eval([['lambda', ['x'], ['+', 'x', 1]], 5])
    print(f"((lambda (x) (+ x 1)) 5) = {result2}")
    
    # Test if
    result3 = evaluator.eval(['if', ['=', 1, 1], 'true', 'false'])
    print(f"(if (= 1 1) 'true' 'false') = {result3}")
    
    # Metacircular: eval evaluates itself
    print("\n=== Ouroboros Moment: Self-Interpretation ===")
    self_eval = evaluator.eval_self()
    print(f"Expression: {self_eval['expression']}")
    print(f"Result: {self_eval['result']}")
    print(f"Metacircular: {self_eval['metacircular']}")
    print(f"Status: {self_eval['self_interpreting']}")
    
    # Tangled hierarchy
    print("\n=== Tangled Hierarchy: Brain-Mind ===")
    brain_mind = TangledHierarchy()
    
    # Neurons (level 0) affect patterns (level 1)
    brain_mind.add_entity("neurons", level=0, affects=[1])
    
    # Patterns (level 1) create thoughts (level 2)
    brain_mind.add_entity("patterns", level=1, affects=[2])
    
    # Thoughts (level 2) affect neurons (level 0) via attention
    brain_mind.add_entity("thoughts", level=2, affects=[0, 1])
    
    print(f"Is tangled hierarchy: {brain_mind.is_tangled()}")
    
    loops = brain_mind.find_causal_loops()
    print(f"Causal loops found: {len(loops)}")
    for i, loop in enumerate(loops[:3], 1):
        print(f"  Loop {i}: {' -> '.join(loop)}")
