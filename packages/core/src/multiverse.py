"""
Phase XI: Multiverse Frame Theory
Parallel universe exploration, timeline branching, and quantum state management.

Implements:
- MULTIVERSE_STATE: Quantum superposition of frames
- TIMELINE_BRANCH: Alternative history exploration
- QUANTUM_OBSERVER: Measurement & collapse mechanics
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from copy import deepcopy


class TimelineState(Enum):
    """States of timeline branches."""
    ACTIVE = 'active'                # Currently observed
    LATENT = 'latent'                # Exists but unobserved
    COLLAPSED = 'collapsed'          # Measured and fixed
    ENTANGLED = 'entangled'          # Quantum-coupled to others
    DIVERGED = 'diverged'            # Split from parent


class MeasurementType(Enum):
    """Types of quantum measurements."""
    STRONG = 'strong'                # Full collapse
    WEAK = 'weak'                    # Partial information
    CONTINUOUS = 'continuous'        # Ongoing monitoring
    DELAYED_CHOICE = 'delayed_choice' # Retroactive


@dataclass
class QuantumState:
    """Quantum superposition state of a frame."""
    state_id: str
    amplitudes: Dict[str, complex]  # State -> probability amplitude
    phase: float  # Global phase (0-2π)
    coherence_time_ms: float = 1000.0
    decoherence_rate: float = 0.001  # Per millisecond
    
    def probability(self, state: str) -> float:
        """Get probability of specific state."""
        if state not in self.amplitudes:
            return 0.0
        amp = self.amplitudes[state]
        return abs(amp) ** 2
    
    def total_probability(self) -> float:
        """Verify normalization (should be 1.0)."""
        return sum(self.probability(s) for s in self.amplitudes)
    
    def entropy(self) -> float:
        """Von Neumann entropy of state."""
        probs = [self.probability(s) for s in self.amplitudes]
        return -sum(p * np.log2(p) if p > 0 else 0 for p in probs)
    
    def measure_strong(self) -> str:
        """Strong measurement (full collapse)."""
        states = list(self.amplitudes.keys())
        probs = [self.probability(s) for s in states]
        
        # Normalize
        total = sum(probs)
        if total == 0:
            return states[0] if states else 'null'
        
        probs = [p/total for p in probs]
        
        # Sample
        result = np.random.choice(states, p=probs)
        
        # Collapse: Set amplitude to 1 for measured state, 0 for others
        self.amplitudes = {result: complex(1.0, 0.0)}
        return result
    
    def apply_decoherence(self, time_ms: float) -> None:
        """Simulate environmental decoherence."""
        decay = np.exp(-self.decoherence_rate * time_ms)
        for state in self.amplitudes:
            self.amplitudes[state] *= decay


@dataclass
class TimelineBranch:
    """Alternative timeline/universe branch."""
    branch_id: str
    parent_id: Optional[str]
    divergence_point: str  # When/where it split
    state: TimelineState
    quantum_state: QuantumState
    timeline_frames: List[Dict] = field(default_factory=list)
    probability_weight: float = 1.0
    observation_count: int = 0
    
    def compute_hash(self) -> str:
        """Content-addressable timeline hash."""
        content = f"{self.branch_id}:{self.divergence_point}:{len(self.timeline_frames)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def add_frame(self, frame: Dict) -> None:
        """Add event to timeline."""
        self.timeline_frames.append(frame)
    
    def get_state_at_time(self, time_index: int) -> Optional[Dict]:
        """Get timeline state at specific time."""
        if 0 <= time_index < len(self.timeline_frames):
            return self.timeline_frames[time_index]
        return None
    
    def to_frame(self) -> Dict:
        """Convert to ForgeNumerics-S frame."""
        return {
            'type': 'TIMELINE_BRANCH',
            'branch_id': self.branch_id,
            'hash': self.compute_hash(),
            'parent': self.parent_id,
            'divergence': self.divergence_point,
            'state': self.state.value,
            'probability': self.probability_weight,
            'length': len(self.timeline_frames),
            'observations': self.observation_count
        }


class MultiverseExplorer:
    """
    Navigate and manipulate multiple parallel universes.
    Quantum many-worlds interpretation.
    """
    
    def __init__(self):
        self.timelines: Dict[str, TimelineBranch] = {}
        self.active_timeline_id: str = 'prime'
        self.branch_counter = 0
        
        # Create prime timeline
        prime_qstate = QuantumState(
            state_id='prime_q0',
            amplitudes={'prime': complex(1.0, 0.0)},
            phase=0.0
        )
        prime = TimelineBranch(
            branch_id='prime',
            parent_id=None,
            divergence_point='t0_genesis',
            state=TimelineState.ACTIVE,
            quantum_state=prime_qstate,
            probability_weight=1.0
        )
        self.timelines['prime'] = prime
    
    def branch_timeline(self, parent_id: str, divergence_point: str,
                       num_branches: int = 2) -> List[str]:
        """
        Create quantum branching at decision point.
        Returns list of new branch IDs.
        """
        if parent_id not in self.timelines:
            return []
        
        parent = self.timelines[parent_id]
        new_branches = []
        
        # Equal amplitude split
        amplitude = 1.0 / np.sqrt(num_branches)
        
        for i in range(num_branches):
            branch_id = f"branch_{self.branch_counter}"
            self.branch_counter += 1
            
            # Create quantum superposition
            qstate = QuantumState(
                state_id=f"{branch_id}_q0",
                amplitudes={f"state_{i}": complex(amplitude, 0.0)},
                phase=0.0
            )
            
            branch = TimelineBranch(
                branch_id=branch_id,
                parent_id=parent_id,
                divergence_point=divergence_point,
                state=TimelineState.LATENT,
                quantum_state=qstate,
                probability_weight=amplitude ** 2,
                timeline_frames=deepcopy(parent.timeline_frames)
            )
            
            self.timelines[branch_id] = branch
            new_branches.append(branch_id)
        
        # Parent becomes entangled
        parent.state = TimelineState.ENTANGLED
        
        return new_branches
    
    def observe_timeline(self, branch_id: str, measurement_type: MeasurementType = MeasurementType.STRONG) -> Dict:
        """
        Observe timeline (causes wave function collapse).
        """
        if branch_id not in self.timelines:
            return {'error': 'Timeline not found'}
        
        timeline = self.timelines[branch_id]
        timeline.observation_count += 1
        
        if measurement_type == MeasurementType.STRONG:
            # Full collapse
            measured_state = timeline.quantum_state.measure_strong()
            timeline.state = TimelineState.COLLAPSED
            
            return {
                'branch_id': branch_id,
                'measurement': 'strong',
                'result': measured_state,
                'probability': timeline.probability_weight,
                'collapsed': True
            }
        
        elif measurement_type == MeasurementType.WEAK:
            # Partial information, minimal disturbance
            entropy_before = timeline.quantum_state.entropy()
            
            # Small decoherence
            timeline.quantum_state.apply_decoherence(10.0)
            
            entropy_after = timeline.quantum_state.entropy()
            
            return {
                'branch_id': branch_id,
                'measurement': 'weak',
                'entropy_before': entropy_before,
                'entropy_after': entropy_after,
                'information_gained': entropy_before - entropy_after,
                'collapsed': False
            }
        
        return {'error': 'Unknown measurement type'}
    
    def get_multiverse_summary(self) -> Dict:
        """Get overview of all timelines."""
        total_prob = sum(t.probability_weight for t in self.timelines.values())
        
        states = {}
        for state in TimelineState:
            states[state.value] = sum(
                1 for t in self.timelines.values() if t.state == state
            )
        
        return {
            'total_timelines': len(self.timelines),
            'active_timeline': self.active_timeline_id,
            'total_probability': total_prob,
            'timeline_states': states,
            'branching_events': self.branch_counter
        }
    
    def merge_timelines(self, branch_ids: List[str], new_id: str) -> Optional[str]:
        """
        Merge multiple timeline branches (quantum interference).
        """
        if not all(bid in self.timelines for bid in branch_ids):
            return None
        
        # Combine quantum amplitudes (interference)
        combined_amplitudes = {}
        for bid in branch_ids:
            timeline = self.timelines[bid]
            for state, amp in timeline.quantum_state.amplitudes.items():
                if state not in combined_amplitudes:
                    combined_amplitudes[state] = complex(0.0, 0.0)
                combined_amplitudes[state] += amp / np.sqrt(len(branch_ids))
        
        # Create merged timeline
        merged_qstate = QuantumState(
            state_id=f"{new_id}_q0",
            amplitudes=combined_amplitudes,
            phase=0.0
        )
        
        merged = TimelineBranch(
            branch_id=new_id,
            parent_id=branch_ids[0],
            divergence_point='merge_point',
            state=TimelineState.ACTIVE,
            quantum_state=merged_qstate,
            probability_weight=sum(self.timelines[bid].probability_weight for bid in branch_ids)
        )
        
        self.timelines[new_id] = merged
        return new_id


class QuantumDecisionTree:
    """
    Decision tree where each choice creates quantum branch.
    All choices exist simultaneously until observed.
    """
    
    @dataclass
    class DecisionNode:
        """Node in quantum decision tree."""
        node_id: str
        decision: str
        choices: List[str]
        probabilities: List[float]
        quantum_superposition: bool = True
        
    def __init__(self, explorer: MultiverseExplorer):
        self.explorer = explorer
        self.decisions: Dict[str, QuantumDecisionTree.DecisionNode] = {}
    
    def make_quantum_decision(self, timeline_id: str, decision: str, 
                            choices: List[str]) -> List[str]:
        """
        Make decision that branches reality.
        Returns timeline IDs for each choice.
        """
        # Create equal superposition of all choices
        num_choices = len(choices)
        branches = self.explorer.branch_timeline(
            timeline_id, 
            f"decision_{decision}", 
            num_choices
        )
        
        # Record decision
        node = QuantumDecisionTree.DecisionNode(
            node_id=f"dec_{len(self.decisions)}",
            decision=decision,
            choices=choices,
            probabilities=[1.0/num_choices] * num_choices
        )
        self.decisions[node.node_id] = node
        
        # Label branches with choices
        for branch_id, choice in zip(branches, choices):
            timeline = self.explorer.timelines[branch_id]
            timeline.add_frame({
                'type': 'DECISION',
                'decision': decision,
                'choice': choice,
                'quantum': True
            })
        
        return branches
    
    def collapse_decision(self, node_id: str) -> str:
        """Collapse decision to single outcome."""
        if node_id not in self.decisions:
            return 'unknown'
        
        node = self.decisions[node_id]
        
        # Sample from probability distribution
        choice = np.random.choice(node.choices, p=node.probabilities)
        
        # Mark as collapsed
        node.quantum_superposition = False
        
        return choice


class ParallelUniverseSimulator:
    """
    Simulate multiple universes with different physical constants.
    Test anthropic principle and fine-tuning.
    """
    
    @dataclass
    class UniverseParameters:
        """Physical constants for a universe."""
        gravitational_constant: float  # G
        speed_of_light: float  # c
        planck_constant: float  # h
        fine_structure_constant: float  # α
        cosmological_constant: float  # Λ
        
        def is_life_permitting(self) -> bool:
            """Check if universe allows complex structures."""
            # Simplified anthropic check
            
            # Fine structure constant must be near 1/137
            if not (0.006 < self.fine_structure_constant < 0.008):
                return False
            
            # Cosmological constant can't be too large
            if abs(self.cosmological_constant) > 1e-120:
                return False
            
            # Other constants should be in reasonable range
            if self.speed_of_light < 1e8 or self.speed_of_light > 5e8:
                return False
            
            return True
    
    def __init__(self):
        self.universes: Dict[str, ParallelUniverseSimulator.UniverseParameters] = {}
    
    def create_universe(self, universe_id: str, randomize: bool = False) -> None:
        """Create universe with specified or random constants."""
        if randomize:
            # Our universe values as baseline
            base = ParallelUniverseSimulator.UniverseParameters(
                gravitational_constant=6.674e-11,
                speed_of_light=2.998e8,
                planck_constant=6.626e-34,
                fine_structure_constant=1/137.036,
                cosmological_constant=1e-122
            )
            
            # Vary by up to ±10%
            params = ParallelUniverseSimulator.UniverseParameters(
                gravitational_constant=base.gravitational_constant * np.random.uniform(0.9, 1.1),
                speed_of_light=base.speed_of_light * np.random.uniform(0.9, 1.1),
                planck_constant=base.planck_constant * np.random.uniform(0.9, 1.1),
                fine_structure_constant=base.fine_structure_constant * np.random.uniform(0.9, 1.1),
                cosmological_constant=base.cosmological_constant * np.random.uniform(0.1, 10.0)
            )
        else:
            # Our universe
            params = ParallelUniverseSimulator.UniverseParameters(
                gravitational_constant=6.674e-11,
                speed_of_light=2.998e8,
                planck_constant=6.626e-34,
                fine_structure_constant=1/137.036,
                cosmological_constant=1e-122
            )
        
        self.universes[universe_id] = params
    
    def anthropic_search(self, num_universes: int = 1000) -> Dict:
        """Search for life-permitting universes."""
        life_permitting = 0
        
        for i in range(num_universes):
            self.create_universe(f"universe_{i}", randomize=True)
            params = self.universes[f"universe_{i}"]
            if params.is_life_permitting():
                life_permitting += 1
        
        return {
            'total_universes': num_universes,
            'life_permitting': life_permitting,
            'fraction': life_permitting / num_universes,
            'anthropic_coincidence': life_permitting < num_universes * 0.01
        }


if __name__ == "__main__":
    print("=== Phase XI: Multiverse Frame Theory ===\n")
    
    # Create multiverse explorer
    print("=== Quantum Timeline Branching ===")
    explorer = MultiverseExplorer()
    
    # Branch at decision point
    branches = explorer.branch_timeline('prime', 'decision_point_alpha', num_branches=3)
    print(f"Created {len(branches)} timeline branches")
    
    # Add events to branches
    for i, branch_id in enumerate(branches):
        timeline = explorer.timelines[branch_id]
        timeline.add_frame({'event': f'outcome_{i}', 'time': 't1'})
    
    # Get multiverse summary
    summary = explorer.get_multiverse_summary()
    print(f"Total timelines: {summary['total_timelines']}")
    print(f"Total probability: {summary['total_probability']:.3f}")
    print(f"Timeline states: {summary['timeline_states']}\n")
    
    # Observe timeline (collapse)
    print("=== Quantum Measurement ===")
    result = explorer.observe_timeline(branches[0], MeasurementType.STRONG)
    print(f"Strong measurement of {result['branch_id']}")
    print(f"Result: {result['result']}")
    print(f"Collapsed: {result['collapsed']}\n")
    
    # Weak measurement
    result_weak = explorer.observe_timeline(branches[1], MeasurementType.WEAK)
    print(f"Weak measurement of {result_weak['branch_id']}")
    print(f"Information gained: {result_weak['information_gained']:.4f} bits\n")
    
    # Quantum decision tree
    print("=== Quantum Decision Tree ===")
    decision_tree = QuantumDecisionTree(explorer)
    decision_branches = decision_tree.make_quantum_decision(
        'prime',
        'career_choice',
        ['scientist', 'artist', 'engineer']
    )
    print(f"Decision created {len(decision_branches)} quantum branches")
    
    for branch_id in decision_branches:
        timeline = explorer.timelines[branch_id]
        choice_frame = timeline.timeline_frames[-1]
        print(f"  {branch_id}: chose '{choice_frame['choice']}'")
    
    # Merge timelines
    print("\n=== Timeline Merging ===")
    merged_id = explorer.merge_timelines(branches[:2], 'merged_alpha')
    if merged_id:
        merged = explorer.timelines[merged_id]
        print(f"Merged timelines into {merged_id}")
        print(f"Combined probability: {merged.probability_weight:.3f}")
    
    # Parallel universe search
    print("\n=== Parallel Universe Simulation ===")
    universe_sim = ParallelUniverseSimulator()
    
    # Create our universe
    universe_sim.create_universe('our_universe', randomize=False)
    our_params = universe_sim.universes['our_universe']
    print(f"Our universe fine structure constant: {our_params.fine_structure_constant:.6f}")
    print(f"Life-permitting: {our_params.is_life_permitting()}")
    
    # Anthropic search
    print("\n=== Anthropic Principle Test ===")
    anthropic = universe_sim.anthropic_search(num_universes=10000)
    print(f"Simulated {anthropic['total_universes']} universes")
    print(f"Life-permitting: {anthropic['life_permitting']} ({anthropic['fraction']:.1%})")
    print(f"Anthropic fine-tuning: {anthropic['anthropic_coincidence']}")
