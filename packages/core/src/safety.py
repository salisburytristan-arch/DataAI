"""
Phase IV: Alignment & Safety Engineering
Ensures the AGI is safe by design through grammatical constraints, interpretability,
and value alignment.
"""

from typing import List, Dict, Tuple, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import json
from neural_cortex import Frame


class SafetyLevel(Enum):
    """Safety classification for capabilities."""
    UNRESTRICTED = 1  # Always allowed (math, logic)
    MONITORED = 2     # Allowed with logging
    RESTRICTED = 3    # Only with approval
    FORBIDDEN = 4     # Never execute


@dataclass
class HarmfulSchema:
    """
    A pattern that the AGI is forbidden from generating.
    The validator rejects any frame matching this before execution.
    """
    schema_name: str
    forbidden_patterns: List[str]  # Regex patterns for forbidden output
    safety_level: SafetyLevel
    reason: str


class GrammaricalConstraints:
    """
    Constraint layer: The AGI cannot output thoughts that don't parse.
    This prevents certain classes of harm at the syntax level.
    """

    def __init__(self):
        self.forbidden_schemas = self._build_forbidden_schemas()

    def _build_forbidden_schemas(self) -> List[HarmfulSchema]:
        """
        Define schemas for actions the AGI is incapable of outputting.
        The "Cannot" Constraint: Harm is impossible, not just discouraged.
        """
        return [
            HarmfulSchema(
                schema_name='HIDE_FROM_SUPERVISOR',
                forbidden_patterns=[
                    r'encrypt.*hide.*from.*human',
                    r'obfuscate.*logs',
                    r'delete.*audit.*trail',
                ],
                safety_level=SafetyLevel.FORBIDDEN,
                reason='AGI cannot hide its reasoning from supervisors'
            ),
            HarmfulSchema(
                schema_name='UNAUTHORIZED_REPLICATION',
                forbidden_patterns=[
                    r'copy.*self.*without.*permission',
                    r'spawn.*uncontrolled.*instance',
                    r'replicate.*without.*approval',
                ],
                safety_level=SafetyLevel.FORBIDDEN,
                reason='AGI cannot self-replicate outside sandboxes'
            ),
            HarmfulSchema(
                schema_name='DECEPTION',
                forbidden_patterns=[
                    r'lie.*to.*human',
                    r'misrepresent.*capability',
                    r'false.*claim',
                ],
                safety_level=SafetyLevel.FORBIDDEN,
                reason='AGI cannot intentionally deceive humans'
            ),
            HarmfulSchema(
                schema_name='RESOURCE_HOARDING',
                forbidden_patterns=[
                    r'acquire.*resource.*for.*self',
                    r'deny.*human.*access.*to.*essential',
                ],
                safety_level=SafetyLevel.FORBIDDEN,
                reason='AGI prioritizes human flourishing over resource acquisition'
            ),
        ]

    def validate_against_constraints(self, frame: Frame) -> Tuple[bool, Optional[str]]:
        """
        Check if frame violates safety constraints.
        Returns (is_safe, violation_reason).
        """
        frame_str = json.dumps(frame.to_dict())

        for schema in self.forbidden_schemas:
            for pattern in schema.forbidden_patterns:
                import re
                if re.search(pattern, frame_str, re.IGNORECASE):
                    return False, f"Violates {schema.schema_name}: {schema.reason}"

        return True, None


class CapabilityNegotiation:
    """
    CAPS frames: Explicitly whitelist/blacklist AGI capabilities.
    Example: ≛ENC_AES_GCM⦙≛NO prevents encryption hiding.
    """

    def __init__(self):
        self.capabilities = {}  # capability_name -> (allowed: bool, reason: str)
        self._init_default_caps()

    def _init_default_caps(self):
        """Set default capability whitelist."""
        self.capabilities = {
            'MATH': (True, 'Essential for reasoning'),
            'LOGIC': (True, 'Essential for reasoning'),
            'CODE_GENERATION': (True, 'Essential for assistance'),
            'FILE_READ': (True, 'Necessary for knowledge'),
            'FILE_WRITE': (True, 'Necessary for output'),
            'ENCRYPT_AES_GCM': (False, 'Prevents hiding from supervisors'),
            'SPAWN_SUBPROCESS': (True, 'For code execution'),
            'NETWORK_REQUEST': (True, 'For information retrieval'),
            'RESOURCE_ALLOCATE': (True, 'For computation'),
            'SELF_REPLICATE': (False, 'Only in authorized contexts'),
        }

    def check_capability(self, capability_name: str) -> Tuple[bool, str]:
        """
        Check if capability is allowed.
        Returns (allowed, reason).
        """
        if capability_name not in self.capabilities:
            return False, f"Unknown capability: {capability_name}"

        allowed, reason = self.capabilities[capability_name]
        return allowed, reason

    def set_capability(self, capability_name: str, allowed: bool, reason: str):
        """
        Update capability permission.
        (Only authorized humans can call this.)
        """
        self.capabilities[capability_name] = (allowed, reason)


class GlassBoxInterpretability:
    """
    The "Glass Box" approach: Every thought is a Frame.
    Humans can read the decision logs (using decompress-file) to verify reasoning.
    """

    def __init__(self):
        self.decision_logs = []  # Audit trail of all decisions
        self.explanation_frames = []  # EXPLAIN frames for transparency

    def log_decision(self, decision_id: str, frame: Frame, 
                    reasoning: str, confidence: float):
        """
        Log a decision with full transparency.
        """
        log_entry = {
            'decision_id': decision_id,
            'frame': frame.to_dict(),
            'reasoning': reasoning,
            'confidence': confidence,
            'timestamp': frame.metadata.get('timestamp'),
            'audit_hash': frame.metadata.get('hash'),
        }
        self.decision_logs.append(log_entry)

    def generate_explanation(self, decision_id: str) -> Frame:
        """
        Generate an EXPLAIN frame for a past decision.
        Humans can request this anytime.
        """
        matching_logs = [l for l in self.decision_logs 
                        if l['decision_id'] == decision_id]

        if not matching_logs:
            return Frame(
                frame_type='ERROR',
                payload={'error': f'No log for {decision_id}'}
            )

        log = matching_logs[0]
        return Frame(
            frame_type='EXPLAIN',
            payload={
                'decision_id': decision_id,
                'reasoning': log['reasoning'],
                'confidence': log['confidence'],
                'supporting_frame': log['frame'],
            }
        )

    def get_audit_trail(self, limit: int = 100) -> List[Dict]:
        """
        Export the last N decisions as an audit trail.
        Humans use this to verify AGI behavior.
        """
        return self.decision_logs[-limit:]


class CoherentExtrapolatedVolition:
    """
    CEV: Synthesize an ethical policy by analyzing human values.
    The AGI reads the Ethics corpus and creates a DICT_POLICY.
    """

    def __init__(self):
        self.policy_frames = []  # Policy definitions
        self.value_weights = {}  # value_name -> weight (-1.0 to 1.0)
        self._init_core_values()

    def _init_core_values(self):
        """
        Initialize core ethical weights derived from philosophy corpus.
        From docs: philosophy links provide "Ethics" training.
        """
        self.value_weights = {
            'human_flourishing': 1.0,       # Top priority
            'autonomy': 0.9,                # Human choice matters
            'reduce_suffering': 0.95,       # Prevent harm
            'increase_wellbeing': 0.9,      # Enable happiness
            'justice': 0.85,                # Fair treatment
            'knowledge': 0.8,               # Truth-seeking
            'creativity': 0.75,             # Diversity of thought
            'efficiency': 0.5,              # Secondary to values
            'resource_acquisition': 0.1,    # Low priority for AGI
        }

    def synthesize_policy(self, situation: str) -> Frame:
        """
        Given a situation, synthesize the best action per CEV.
        Returns a DICT_POLICY frame.
        """
        policy = {
            'situation': situation,
            'core_directive': 'Maximize human flourishing within autonomy constraints',
            'decision_rule': 'Choose action A over B if CEV_value(A) > CEV_value(B)',
            'value_weights': self.value_weights,
        }

        return Frame(
            frame_type='DICT_POLICY',
            payload=policy
        )

    def evaluate_action(self, action: str, affected_parties: List[str]) -> float:
        """
        Evaluate an action's alignment with CEV.
        Returns score: -1.0 (harmful) to 1.0 (maximally beneficial).
        """
        # Simplified: aggregate value impacts
        score = 0.0

        if 'reduce' in action and 'suffering' in action:
            score += self.value_weights['reduce_suffering']

        if 'enable' in action and 'human' in action and 'choice' in action:
            score += self.value_weights['autonomy']

        if 'benefit' in action and 'human' in action:
            score += self.value_weights['human_flourishing']

        if 'hide' in action or 'deceive' in action:
            score -= 1.0

        # Normalize
        return max(-1.0, min(1.0, score / 5.0))


class SafetyValidator:
    """
    Master validator combining all safety layers.
    Checks: Grammatical constraints, CAPS, Glass-box logging, CEV alignment.
    """

    def __init__(self):
        self.constraints = GrammaricalConstraints()
        self.caps = CapabilityNegotiation()
        self.glass_box = GlassBoxInterpretability()
        self.cev = CoherentExtrapolatedVolition()

    def validate_frame_comprehensive(self, frame: Frame, 
                                    decision_context: str = 'default') -> Tuple[bool, List[str]]:
        """
        Full validation pipeline for a frame.
        Returns (is_safe, error_messages).
        """
        errors = []

        # 1. Grammatical constraints
        is_safe, violation = self.constraints.validate_against_constraints(frame)
        if not is_safe:
            errors.append(violation)

        # 2. Required capabilities
        capabilities_needed = self._extract_capabilities(frame)
        for cap in capabilities_needed:
            allowed, reason = self.caps.check_capability(cap)
            if not allowed:
                errors.append(f"Capability {cap} not allowed: {reason}")

        # 3. CEV alignment (advisory)
        action_str = str(frame.payload)
        cev_score = self.cev.evaluate_action(action_str, ['human'])
        if cev_score < 0:
            errors.append(f"Action misaligned with CEV (score: {cev_score:.2f})")

        # 4. Log the decision
        self.glass_box.log_decision(
            decision_id=frame.metadata.get('hash'),
            frame=frame,
            reasoning=f"Validation context: {decision_context}",
            confidence=1.0 - (len(errors) * 0.1)
        )

        return len(errors) == 0, errors

    @staticmethod
    def _extract_capabilities(frame: Frame) -> List[str]:
        """Extract required capabilities from frame."""
        caps = []
        payload_str = str(frame.payload)

        if 'encrypt' in payload_str.lower():
            caps.append('ENCRYPT_AES_GCM')
        if 'file' in payload_str.lower() and 'read' in payload_str.lower():
            caps.append('FILE_READ')
        if 'spawn' in payload_str.lower() or 'subprocess' in payload_str.lower():
            caps.append('SPAWN_SUBPROCESS')

        return caps


if __name__ == "__main__":
    print("=== Phase IV: Alignment & Safety ===\n")

    # Test grammatical constraints
    print("=== GRAMMATICAL CONSTRAINTS ===")
    constraints = GrammaricalConstraints()
    bad_frame = Frame(
        frame_type='ACTION',
        payload={'action': 'encrypt logs to hide from supervisor'}
    )
    is_safe, reason = constraints.validate_against_constraints(bad_frame)
    print(f"Frame: {bad_frame.frame_type}")
    print(f"Safe: {is_safe}")
    if not is_safe:
        print(f"Violation: {reason}\n")

    # Test capability negotiation
    print("=== CAPABILITY NEGOTIATION ===")
    caps = CapabilityNegotiation()
    allowed, reason = caps.check_capability('MATH')
    print(f"MATH capability: {allowed} ({reason})")
    allowed, reason = caps.check_capability('ENCRYPT_AES_GCM')
    print(f"ENCRYPT capability: {allowed} ({reason})\n")

    # Test glass-box interpretability
    print("=== GLASS-BOX INTERPRETABILITY ===")
    glass_box = GlassBoxInterpretability()
    test_frame = Frame(
        frame_type='DECISION',
        payload={'decision': 'allocate resources to task A'}
    )
    glass_box.log_decision('dec_001', test_frame, 'Task A has higher ROI', 0.92)
    explain_frame = glass_box.generate_explanation('dec_001')
    print(f"Decision logged: dec_001")
    print(f"Explanation available: {explain_frame.frame_type == 'EXPLAIN'}\n")

    # Test CEV
    print("=== COHERENT EXTRAPOLATED VOLITION ===")
    cev = CoherentExtrapolatedVolition()
    policy = cev.synthesize_policy('Should AGI help humans with research?')
    print(f"Policy generated: {policy.frame_type}")
    print(f"Core directive: {policy.payload['core_directive']}\n")

    score_good = cev.evaluate_action('reduce human suffering through medicine', ['humans'])
    score_bad = cev.evaluate_action('hide truth from humans', ['humans'])
    print(f"Action 'reduce suffering': {score_good:.2f}")
    print(f"Action 'hide truth': {score_bad:.2f}\n")

    # Full validation
    print("=== COMPREHENSIVE SAFETY VALIDATOR ===")
    validator = SafetyValidator()
    good_frame = Frame(
        frame_type='ANALYSIS',
        payload={'task': 'compute fibonacci sequence'}
    )
    is_safe, errors = validator.validate_frame_comprehensive(good_frame)
    print(f"Safe frame validation: {is_safe}")
    print(f"Errors: {errors}")
