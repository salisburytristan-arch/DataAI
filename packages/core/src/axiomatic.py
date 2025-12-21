"""
Phase XV: Axiomatic Restructuring (Logic Foundations)
Rebuild logical foundations, alternative axiom systems, redefining truth.

Implements:
- AXIOM_SYSTEM: Formal logical foundations
- CONSISTENCY_CHECKER: Detect contradictions
- ALTERNATIVE_LOGICS: Non-classical logic systems
- TRUTH_REDEFINITION: Redefine what "truth" means
"""

from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class LogicType(Enum):
    """Types of logical systems."""
    CLASSICAL = 'classical'               # True/False, excluded middle
    INTUITIONISTIC = 'intuitionistic'     # Constructive, no excluded middle
    PARACONSISTENT = 'paraconsistent'     # Tolerates contradictions
    FUZZY = 'fuzzy'                       # Degrees of truth [0,1]
    MODAL = 'modal'                       # Necessity/possibility
    QUANTUM = 'quantum'                   # Quantum superposition of truth
    MULTIVALUED = 'multivalued'           # More than 2 truth values


class TruthValue(Enum):
    """Extended truth values beyond True/False."""
    TRUE = 1.0
    FALSE = 0.0
    UNKNOWN = 0.5
    BOTH = 0.75          # Paraconsistent: both true and false
    NEITHER = 0.25       # Neither true nor false
    SUPERPOSITION = -1   # Quantum: superposed state


@dataclass
class Axiom:
    """Fundamental assumption in logical system."""
    axiom_id: str
    statement: str
    is_independent: bool  # Independent of other axioms
    is_consistent: bool  # Doesn't create contradictions
    
    def __hash__(self):
        return hash(self.axiom_id)
    
    def to_frame(self) -> Dict:
        return {
            'type': 'AXIOM',
            'id': self.axiom_id,
            'statement': self.statement,
            'independent': self.is_independent,
            'consistent': self.is_consistent
        }


@dataclass
class Theorem:
    """Derived statement from axioms."""
    theorem_id: str
    statement: str
    derived_from: List[str]  # Axiom IDs
    proof_steps: int
    
    def to_frame(self) -> Dict:
        return {
            'type': 'THEOREM',
            'id': self.theorem_id,
            'statement': self.statement,
            'axioms': self.derived_from,
            'proof_steps': self.proof_steps
        }


class AxiomSystem:
    """
    Formal logical system with axioms and inference rules.
    Can be consistent, complete, or neither (Gödel).
    """
    
    def __init__(self, name: str, logic_type: LogicType = LogicType.CLASSICAL):
        self.name = name
        self.logic_type = logic_type
        self.axioms: Dict[str, Axiom] = {}
        self.theorems: Dict[str, Theorem] = {}
        self.contradictions: List[Tuple[str, str]] = []
    
    def add_axiom(self, axiom: Axiom) -> bool:
        """
        Add axiom to system.
        Check if it maintains consistency.
        """
        # Add to system
        self.axioms[axiom.axiom_id] = axiom
        
        # Check consistency
        is_consistent = self.check_consistency()
        
        if not is_consistent:
            # Rollback if inconsistent (unless paraconsistent logic)
            if self.logic_type != LogicType.PARACONSISTENT:
                del self.axioms[axiom.axiom_id]
                return False
        
        return True
    
    def add_theorem(self, theorem: Theorem):
        """Add derived theorem."""
        self.theorems[theorem.theorem_id] = theorem
    
    def check_consistency(self) -> bool:
        """
        Check if axiom system is consistent.
        Look for contradictions.
        """
        # Simple check: look for direct negations
        statements = [a.statement for a in self.axioms.values()]
        
        for i, stmt1 in enumerate(statements):
            for stmt2 in statements[i+1:]:
                # Check if stmt2 is negation of stmt1
                if self._is_negation(stmt1, stmt2):
                    axiom1_id = list(self.axioms.keys())[i]
                    axiom2_id = list(self.axioms.keys())[statements.index(stmt2)]
                    self.contradictions.append((axiom1_id, axiom2_id))
                    
                    # Classical logic can't tolerate contradictions
                    if self.logic_type == LogicType.CLASSICAL:
                        return False
        
        # Paraconsistent logic tolerates contradictions
        if self.logic_type == LogicType.PARACONSISTENT:
            return True
        
        # No contradictions found
        return len(self.contradictions) == 0
    
    def _is_negation(self, stmt1: str, stmt2: str) -> bool:
        """Check if stmt2 is negation of stmt1."""
        # Simple heuristic
        if stmt1.startswith("NOT ") and stmt1[4:] == stmt2:
            return True
        if stmt2.startswith("NOT ") and stmt2[4:] == stmt1:
            return True
        return False
    
    def check_completeness(self) -> Dict:
        """
        Check if system is complete.
        Complete = every true statement is provable.
        (Gödel: sufficiently powerful systems are incomplete)
        """
        # Simplified check
        if len(self.axioms) < 5:
            return {
                'complete': False,
                'reason': 'Too few axioms to be complete',
                'godel_applies': False
            }
        
        # If system can express arithmetic, Gödel's theorem applies
        has_arithmetic = any('number' in a.statement.lower() or 
                           'successor' in a.statement.lower()
                           for a in self.axioms.values())
        
        if has_arithmetic:
            return {
                'complete': False,
                'reason': "Gödel's Incompleteness Theorem",
                'godel_applies': True,
                'undecidable_statements_exist': True
            }
        
        return {
            'complete': None,  # Unknown
            'reason': 'Completeness undetermined',
            'godel_applies': False
        }
    
    def derive_theorem(self, statement: str, axiom_ids: List[str]) -> Optional[Theorem]:
        """
        Derive new theorem from axioms.
        Simplified inference.
        """
        # Check all axioms exist
        if not all(aid in self.axioms for aid in axiom_ids):
            return None
        
        # Create theorem
        theorem = Theorem(
            theorem_id=f"thm_{len(self.theorems)}",
            statement=statement,
            derived_from=axiom_ids,
            proof_steps=len(axiom_ids)
        )
        
        self.add_theorem(theorem)
        return theorem


class AlternativeLogicSystem:
    """
    Non-classical logical systems.
    Explore alternative foundations for reasoning.
    """
    
    def __init__(self, logic_type: LogicType):
        self.logic_type = logic_type
    
    def evaluate(self, proposition: str, truth_value: float) -> Dict:
        """
        Evaluate proposition in this logic system.
        truth_value: 0.0 (false) to 1.0 (true)
        """
        if self.logic_type == LogicType.CLASSICAL:
            return self._classical_eval(truth_value)
        
        elif self.logic_type == LogicType.FUZZY:
            return self._fuzzy_eval(truth_value)
        
        elif self.logic_type == LogicType.INTUITIONISTIC:
            return self._intuitionistic_eval(truth_value)
        
        elif self.logic_type == LogicType.PARACONSISTENT:
            return self._paraconsistent_eval(truth_value)
        
        elif self.logic_type == LogicType.QUANTUM:
            return self._quantum_eval(truth_value)
        
        return {'value': truth_value, 'type': 'unknown'}
    
    def _classical_eval(self, truth_value: float) -> Dict:
        """Classical logic: crisp True/False."""
        return {
            'value': 1.0 if truth_value >= 0.5 else 0.0,
            'type': 'classical',
            'truth': truth_value >= 0.5
        }
    
    def _fuzzy_eval(self, truth_value: float) -> Dict:
        """Fuzzy logic: degrees of truth."""
        return {
            'value': max(0.0, min(1.0, truth_value)),
            'type': 'fuzzy',
            'degree': truth_value,
            'linguistic': self._fuzzy_linguistic(truth_value)
        }
    
    def _fuzzy_linguistic(self, value: float) -> str:
        """Convert numeric truth to linguistic term."""
        if value >= 0.9:
            return 'very_true'
        elif value >= 0.7:
            return 'mostly_true'
        elif value >= 0.5:
            return 'somewhat_true'
        elif value >= 0.3:
            return 'somewhat_false'
        elif value >= 0.1:
            return 'mostly_false'
        else:
            return 'very_false'
    
    def _intuitionistic_eval(self, truth_value: float) -> Dict:
        """
        Intuitionistic logic: constructive.
        No law of excluded middle (NOT (NOT P) ≠ P).
        """
        # Require explicit proof/construction
        if truth_value >= 0.8:
            return {
                'value': 1.0,
                'type': 'intuitionistic',
                'provable': True,
                'construction': 'explicit'
            }
        elif truth_value <= 0.2:
            return {
                'value': 0.0,
                'type': 'intuitionistic',
                'provable': True,
                'refutation': 'explicit'
            }
        else:
            return {
                'value': None,
                'type': 'intuitionistic',
                'provable': False,
                'status': 'undecided'
            }
    
    def _paraconsistent_eval(self, truth_value: float) -> Dict:
        """
        Paraconsistent logic: tolerates contradictions.
        Can be both true and false.
        """
        if truth_value > 0.7:
            return {
                'value': 1.0,
                'type': 'paraconsistent',
                'true': True,
                'false': False
            }
        elif truth_value < 0.3:
            return {
                'value': 0.0,
                'type': 'paraconsistent',
                'true': False,
                'false': True
            }
        else:
            # Contradiction region: both true and false
            return {
                'value': 0.5,
                'type': 'paraconsistent',
                'true': True,
                'false': True,
                'contradiction': True
            }
    
    def _quantum_eval(self, truth_value: float) -> Dict:
        """
        Quantum logic: superposition until measured.
        """
        import numpy as np
        
        # Superposition state
        alpha = np.sqrt(truth_value)  # Amplitude for |true>
        beta = np.sqrt(1 - truth_value)  # Amplitude for |false>
        
        return {
            'value': None,  # Undefined until measurement
            'type': 'quantum',
            'superposition': True,
            'amplitude_true': alpha,
            'amplitude_false': beta,
            'probability_true': truth_value,
            'probability_false': 1 - truth_value
        }
    
    def apply_operator(self, op: str, a: float, b: Optional[float] = None) -> float:
        """
        Apply logical operator in this logic system.
        op: 'NOT', 'AND', 'OR', 'IMPLIES'
        """
        if self.logic_type == LogicType.CLASSICAL:
            return self._classical_operator(op, a, b)
        
        elif self.logic_type == LogicType.FUZZY:
            return self._fuzzy_operator(op, a, b)
        
        return a
    
    def _classical_operator(self, op: str, a: float, b: Optional[float]) -> float:
        """Classical logic operators."""
        a = 1.0 if a >= 0.5 else 0.0
        if b is not None:
            b = 1.0 if b >= 0.5 else 0.0
        
        if op == 'NOT':
            return 1.0 - a
        elif op == 'AND' and b is not None:
            return min(a, b)
        elif op == 'OR' and b is not None:
            return max(a, b)
        elif op == 'IMPLIES' and b is not None:
            return 1.0 if (a == 0.0 or b == 1.0) else 0.0
        
        return a
    
    def _fuzzy_operator(self, op: str, a: float, b: Optional[float]) -> float:
        """Fuzzy logic operators (Łukasiewicz)."""
        if op == 'NOT':
            return 1.0 - a
        elif op == 'AND' and b is not None:
            return min(a, b)
        elif op == 'OR' and b is not None:
            return max(a, b)
        elif op == 'IMPLIES' and b is not None:
            return min(1.0, 1.0 - a + b)
        
        return a


class TruthRedefinition:
    """
    Redefine what "truth" means.
    Explore foundations of epistemology.
    """
    
    @dataclass
    class TruthTheory:
        """Theory of truth."""
        name: str
        description: str
        criteria: List[str]
    
    @staticmethod
    def correspondence_theory() -> 'TruthRedefinition.TruthTheory':
        """Truth = correspondence with reality."""
        return TruthRedefinition.TruthTheory(
            name='Correspondence',
            description='Statement is true if it corresponds to facts',
            criteria=['matches_reality', 'empirically_verifiable']
        )
    
    @staticmethod
    def coherence_theory() -> 'TruthRedefinition.TruthTheory':
        """Truth = coherence with other beliefs."""
        return TruthRedefinition.TruthTheory(
            name='Coherence',
            description='Statement is true if it coheres with belief system',
            criteria=['consistent_with_beliefs', 'no_contradictions']
        )
    
    @staticmethod
    def pragmatic_theory() -> 'TruthRedefinition.TruthTheory':
        """Truth = what works in practice."""
        return TruthRedefinition.TruthTheory(
            name='Pragmatic',
            description='Statement is true if it is useful',
            criteria=['practical_utility', 'predictive_power']
        )
    
    @staticmethod
    def consensus_theory() -> 'TruthRedefinition.TruthTheory':
        """Truth = what consensus agrees on."""
        return TruthRedefinition.TruthTheory(
            name='Consensus',
            description='Statement is true if consensus accepts it',
            criteria=['agreement', 'social_acceptance']
        )
    
    @staticmethod
    def deflationary_theory() -> 'TruthRedefinition.TruthTheory':
        """Truth is not a substantive property."""
        return TruthRedefinition.TruthTheory(
            name='Deflationary',
            description='"P is true" just means P',
            criteria=['no_truth_property', 'redundancy']
        )
    
    @staticmethod
    def evaluate_statement(statement: str, theory: 'TruthRedefinition.TruthTheory', 
                          context: Dict) -> Dict:
        """Evaluate truth of statement under given theory."""
        if theory.name == 'Correspondence':
            # Check if matches reality
            matches = context.get('matches_reality', False)
            return {
                'true': matches,
                'theory': theory.name,
                'justification': 'Corresponds to observed facts' if matches else 'No correspondence'
            }
        
        elif theory.name == 'Coherence':
            # Check coherence with beliefs
            coherent = context.get('coherent_with_system', True)
            return {
                'true': coherent,
                'theory': theory.name,
                'justification': 'Coherent with belief system' if coherent else 'Incoherent'
            }
        
        elif theory.name == 'Pragmatic':
            # Check utility
            useful = context.get('useful', False)
            return {
                'true': useful,
                'theory': theory.name,
                'justification': 'Pragmatically useful' if useful else 'Not useful'
            }
        
        elif theory.name == 'Consensus':
            # Check consensus
            agreement = context.get('consensus_ratio', 0.5)
            return {
                'true': agreement > 0.5,
                'theory': theory.name,
                'justification': f'{agreement:.0%} consensus'
            }
        
        elif theory.name == 'Deflationary':
            # Truth is redundant
            return {
                'true': None,
                'theory': theory.name,
                'justification': 'Truth predicate is redundant'
            }
        
        return {'true': None, 'theory': theory.name}


if __name__ == "__main__":
    print("=== Phase XV: Axiomatic Restructuring ===\n")
    
    # Classical axiom system
    print("=== Classical Axiom System ===")
    peano = AxiomSystem("Peano Arithmetic", LogicType.CLASSICAL)
    
    # Add Peano axioms
    peano.add_axiom(Axiom("PA1", "Zero is a number", True, True))
    peano.add_axiom(Axiom("PA2", "Every number has a successor", True, True))
    peano.add_axiom(Axiom("PA3", "Zero is not the successor of any number", True, True))
    peano.add_axiom(Axiom("PA4", "Different numbers have different successors", True, True))
    peano.add_axiom(Axiom("PA5", "Induction principle", True, True))
    
    print(f"Axioms: {len(peano.axioms)}")
    print(f"Consistent: {peano.check_consistency()}")
    
    completeness = peano.check_completeness()
    print(f"Complete: {completeness['complete']}")
    print(f"Reason: {completeness['reason']}")
    
    # Derive theorem
    theorem = peano.derive_theorem("One is a number", ["PA1", "PA2"])
    print(f"\nDerived theorem: {theorem.statement}")
    print(f"From axioms: {', '.join(theorem.derived_from)}")
    
    # Paraconsistent system (tolerates contradictions)
    print("\n=== Paraconsistent System ===")
    para = AxiomSystem("Paraconsistent Logic", LogicType.PARACONSISTENT)
    
    para.add_axiom(Axiom("P1", "The cat is alive", True, True))
    para.add_axiom(Axiom("P2", "NOT The cat is alive", True, True))  # Contradiction!
    
    print(f"Consistent: {para.check_consistency()}")
    print(f"Contradictions found: {len(para.contradictions)}")
    print(f"System remains valid: True (paraconsistent logic)")
    
    # Alternative logic systems
    print("\n=== Alternative Logic Systems ===")
    
    # Classical
    classical = AlternativeLogicSystem(LogicType.CLASSICAL)
    result = classical.evaluate("The sky is blue", 0.7)
    print(f"Classical: {result}")
    
    # Fuzzy
    fuzzy = AlternativeLogicSystem(LogicType.FUZZY)
    result = fuzzy.evaluate("The sky is blue", 0.7)
    print(f"Fuzzy: {result}")
    
    # Intuitionistic
    intuitionistic = AlternativeLogicSystem(LogicType.INTUITIONISTIC)
    result = intuitionistic.evaluate("P or NOT P", 0.5)  # Law of excluded middle
    print(f"Intuitionistic: {result}")
    
    # Quantum
    quantum = AlternativeLogicSystem(LogicType.QUANTUM)
    result = quantum.evaluate("Electron spin up", 0.7)
    print(f"Quantum: {result}")
    
    # Logical operators in fuzzy logic
    print("\n=== Fuzzy Logic Operators ===")
    a = 0.7  # Somewhat true
    b = 0.3  # Somewhat false
    
    print(f"A = {a}, B = {b}")
    print(f"NOT A = {fuzzy.apply_operator('NOT', a)}")
    print(f"A AND B = {fuzzy.apply_operator('AND', a, b)}")
    print(f"A OR B = {fuzzy.apply_operator('OR', a, b)}")
    print(f"A IMPLIES B = {fuzzy.apply_operator('IMPLIES', a, b)}")
    
    # Truth redefinition
    print("\n=== Theories of Truth ===")
    
    theories = [
        TruthRedefinition.correspondence_theory(),
        TruthRedefinition.coherence_theory(),
        TruthRedefinition.pragmatic_theory(),
        TruthRedefinition.consensus_theory(),
        TruthRedefinition.deflationary_theory()
    ]
    
    for theory in theories:
        print(f"\n{theory.name}: {theory.description}")
        print(f"Criteria: {', '.join(theory.criteria)}")
    
    # Evaluate same statement under different theories
    print("\n=== Statement: 'AGI is possible' ===")
    statement = "AGI is possible"
    
    contexts = [
        {'matches_reality': True},  # Correspondence
        {'coherent_with_system': True},  # Coherence
        {'useful': True},  # Pragmatic
        {'consensus_ratio': 0.8},  # Consensus
        {}  # Deflationary
    ]
    
    for theory, context in zip(theories, contexts):
        result = TruthRedefinition.evaluate_statement(statement, theory, context)
        print(f"{theory.name}: True={result['true']}, {result['justification']}")
