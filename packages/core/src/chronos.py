"""
Phase XII: Chronos Interface (Time Manipulation)
Temporal navigation, causality management, and retrocausality protocols.

Implements:
- CHRONOS_FRAME: Time-aware computation frame
- CAUSAL_GRAPH: Event causality tracking
- TIME_LOOP: Closed timelike curves
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from datetime import datetime, timedelta


class TemporalDirection(Enum):
    """Direction of temporal flow."""
    FORWARD = 'forward'              # Normal time
    BACKWARD = 'backward'            # Retrocausality
    STATIONARY = 'stationary'        # Frozen time
    ORTHOGONAL = 'orthogonal'        # Perpendicular to time


class CausalityType(Enum):
    """Types of causal relationships."""
    CAUSES = 'causes'                # A → B
    PREVENTS = 'prevents'            # A ⊥ B
    ENABLES = 'enables'              # A allows B
    REQUIRES = 'requires'            # B needs A
    LOOP = 'loop'                    # A ↔ B (paradox)


@dataclass
class ChronosFrame:
    """
    Time-aware computational frame.
    Tracks temporal position and causal relationships.
    """
    frame_id: str
    timestamp: float  # Seconds since epoch
    temporal_direction: TemporalDirection
    causal_parent: Optional[str]  # What caused this frame
    causal_children: Set[str] = field(default_factory=set)
    data: Dict = field(default_factory=dict)
    time_coordinate: float = 0.0  # Position in abstract time
    
    def compute_hash(self) -> str:
        """Content-addressable hash including temporal data."""
        content = f"{self.frame_id}:{self.timestamp}:{self.temporal_direction.value}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_frame(self) -> Dict:
        """Convert to ForgeNumerics-S frame."""
        return {
            'type': 'CHRONOS_FRAME',
            'frame_id': self.frame_id,
            'hash': self.compute_hash(),
            'timestamp': self.timestamp,
            'direction': self.temporal_direction.value,
            'parent': self.causal_parent,
            'children': list(self.causal_children),
            'time_coord': self.time_coordinate
        }


@dataclass
class CausalEdge:
    """Edge in causal graph."""
    source_event: str
    target_event: str
    causality_type: CausalityType
    strength: float  # 0-1, how strong the causal link
    time_delta: float  # Seconds between events
    
    def is_timelike(self) -> bool:
        """Check if edge respects causality (time_delta > 0)."""
        return self.time_delta > 0
    
    def is_spacelike(self) -> bool:
        """Check if events are causally disconnected."""
        return self.time_delta == 0
    
    def is_paradoxical(self) -> bool:
        """Check if edge creates temporal paradox."""
        return self.time_delta < 0 or self.causality_type == CausalityType.LOOP


class CausalGraph:
    """
    Directed acyclic graph (DAG) of causal relationships.
    Detects temporal paradoxes and causal loops.
    """
    
    def __init__(self):
        self.events: Dict[str, ChronosFrame] = {}
        self.edges: List[CausalEdge] = []
        self.paradoxes: List[CausalEdge] = []
    
    def add_event(self, frame: ChronosFrame) -> None:
        """Add event to causal graph."""
        self.events[frame.frame_id] = frame
    
    def add_causal_link(self, source_id: str, target_id: str,
                       causality: CausalityType, strength: float = 1.0) -> bool:
        """
        Add causal edge between events.
        Returns False if creates paradox.
        """
        if source_id not in self.events or target_id not in self.events:
            return False
        
        source = self.events[source_id]
        target = self.events[target_id]
        
        time_delta = target.timestamp - source.timestamp
        
        edge = CausalEdge(
            source_event=source_id,
            target_event=target_id,
            causality_type=causality,
            strength=strength,
            time_delta=time_delta
        )
        
        # Check for paradox
        if edge.is_paradoxical():
            self.paradoxes.append(edge)
            return False
        
        self.edges.append(edge)
        source.causal_children.add(target_id)
        target.causal_parent = source_id
        
        return True
    
    def find_cycles(self) -> List[List[str]]:
        """Detect causal loops (cycles in graph)."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str, path: List[str]):
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            if node_id in self.events:
                for child_id in self.events[node_id].causal_children:
                    if child_id not in visited:
                        dfs(child_id, path[:])
                    elif child_id in rec_stack:
                        # Found cycle
                        cycle_start = path.index(child_id)
                        cycles.append(path[cycle_start:])
            
            rec_stack.remove(node_id)
        
        for event_id in self.events:
            if event_id not in visited:
                dfs(event_id, [])
        
        return cycles
    
    def topological_sort(self) -> Optional[List[str]]:
        """
        Compute topological ordering of events.
        Returns None if cycles exist.
        """
        if self.find_cycles():
            return None  # Can't sort with cycles
        
        in_degree = {eid: 0 for eid in self.events}
        
        for edge in self.edges:
            in_degree[edge.target_event] += 1
        
        queue = [eid for eid in self.events if in_degree[eid] == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            if node_id in self.events:
                for child_id in self.events[node_id].causal_children:
                    in_degree[child_id] -= 1
                    if in_degree[child_id] == 0:
                        queue.append(child_id)
        
        return result if len(result) == len(self.events) else None
    
    def get_causal_cone(self, event_id: str, direction: str = 'future') -> Set[str]:
        """
        Get all events in future or past light cone of event.
        direction: 'future' or 'past'
        """
        if event_id not in self.events:
            return set()
        
        cone = set()
        
        def traverse(node_id: str):
            if node_id in cone:
                return
            cone.add(node_id)
            
            if node_id in self.events:
                if direction == 'future':
                    for child_id in self.events[node_id].causal_children:
                        traverse(child_id)
                elif direction == 'past':
                    parent_id = self.events[node_id].causal_parent
                    if parent_id:
                        traverse(parent_id)
        
        traverse(event_id)
        return cone


class TimeLoop:
    """
    Closed timelike curve (CTC): path through spacetime that returns to starting point.
    Bootstrap paradox and consistency checking.
    """
    
    @dataclass
    class LoopIteration:
        """Single iteration through time loop."""
        iteration_number: int
        events: List[ChronosFrame]
        consistency_score: float  # 0-1, how consistent with previous
        
    def __init__(self, loop_id: str, duration_seconds: float):
        self.loop_id = loop_id
        self.duration = duration_seconds
        self.iterations: List[TimeLoop.LoopIteration] = []
        self.converged = False
    
    def run_iteration(self, initial_state: Dict) -> Dict:
        """
        Run one loop iteration.
        Checks for consistency with previous iterations.
        """
        iteration_num = len(self.iterations)
        events = []
        
        # Simulate events in loop
        current_time = 0.0
        state = initial_state.copy()
        
        while current_time < self.duration:
            frame = ChronosFrame(
                frame_id=f"loop_{self.loop_id}_iter{iteration_num}_t{current_time:.1f}",
                timestamp=current_time,
                temporal_direction=TemporalDirection.FORWARD,
                causal_parent=None,
                data=state.copy(),
                time_coordinate=current_time
            )
            events.append(frame)
            
            # Update state (simplified evolution)
            for key in state:
                if isinstance(state[key], (int, float)):
                    state[key] = state[key] * 0.99 + 0.01 * iteration_num
            
            current_time += 1.0
        
        # Check consistency with previous iteration
        consistency = 1.0
        if self.iterations:
            prev_events = self.iterations[-1].events
            if len(prev_events) == len(events):
                differences = []
                for prev, curr in zip(prev_events, events):
                    # Compare states
                    diff = sum(abs(prev.data.get(k, 0) - curr.data.get(k, 0)) 
                              for k in prev.data.keys())
                    differences.append(diff)
                
                avg_diff = np.mean(differences) if differences else 0
                consistency = np.exp(-avg_diff)  # Exponential decay
        
        iteration = TimeLoop.LoopIteration(
            iteration_number=iteration_num,
            events=events,
            consistency_score=consistency
        )
        
        self.iterations.append(iteration)
        
        # Check convergence
        if len(self.iterations) > 2:
            recent_consistency = [it.consistency_score for it in self.iterations[-3:]]
            if all(c > 0.99 for c in recent_consistency):
                self.converged = True
        
        return {
            'iteration': iteration_num,
            'consistency': consistency,
            'converged': self.converged,
            'events': len(events)
        }
    
    def find_stable_loop(self, initial_state: Dict, max_iterations: int = 100) -> Dict:
        """
        Find self-consistent stable time loop.
        Novikov self-consistency principle.
        """
        for i in range(max_iterations):
            result = self.run_iteration(initial_state)
            
            if result['converged']:
                return {
                    'success': True,
                    'iterations_to_convergence': i + 1,
                    'final_consistency': result['consistency'],
                    'loop_duration': self.duration
                }
            
            # Update initial state based on loop feedback
            if self.iterations:
                final_state = self.iterations[-1].events[-1].data
                initial_state = {
                    k: 0.9 * initial_state.get(k, 0) + 0.1 * final_state.get(k, 0)
                    for k in set(initial_state.keys()) | set(final_state.keys())
                }
        
        return {
            'success': False,
            'iterations': max_iterations,
            'reason': 'Failed to converge'
        }


class RetrocausalityEngine:
    """
    Backward-in-time causation: future events influence past.
    Delayed-choice experiments and retrocausality.
    """
    
    @dataclass
    class RetrocausalEvent:
        """Event that causally affects its own past."""
        event_id: str
        present_time: float
        retro_target_time: float
        influence_strength: float
        
    def __init__(self):
        self.retro_events: List[RetrocausalityEngine.RetrocausalEvent] = []
    
    def create_retro_link(self, future_event_id: str, future_time: float,
                         past_time: float, strength: float = 0.5) -> Dict:
        """
        Create retrocausal link from future to past.
        """
        if future_time <= past_time:
            return {'error': 'Future time must be after past time'}
        
        event = RetrocausalityEngine.RetrocausalEvent(
            event_id=future_event_id,
            present_time=future_time,
            retro_target_time=past_time,
            influence_strength=strength
        )
        
        self.retro_events.append(event)
        
        return {
            'retro_event_id': future_event_id,
            'delta_t': future_time - past_time,
            'strength': strength,
            'paradox_risk': strength * (future_time - past_time) / future_time
        }
    
    def delayed_choice_experiment(self, num_trials: int = 1000) -> Dict:
        """
        Simulate Wheeler's delayed-choice experiment.
        Choice in future affects behavior in past.
        """
        particle_paths = []
        
        for trial in range(num_trials):
            # Particle passes through double slit
            path = np.random.choice(['wave', 'particle'])
            
            # Later: choose measurement (wave or particle detector)
            measurement = np.random.choice(['wave_detector', 'particle_detector'])
            
            # Retrocausality: measurement choice affects past behavior
            if measurement == 'wave_detector':
                # Particle retroactively "was" wave
                final_path = 'wave'
            else:
                # Particle retroactively "was" particle
                final_path = 'particle'
            
            particle_paths.append({
                'initial': path,
                'measurement': measurement,
                'final': final_path,
                'retrocausal': path != final_path
            })
        
        retrocausal_count = sum(1 for p in particle_paths if p['retrocausal'])
        
        return {
            'trials': num_trials,
            'retrocausal_events': retrocausal_count,
            'retrocausal_fraction': retrocausal_count / num_trials,
            'paths': particle_paths[:10]  # Sample
        }


if __name__ == "__main__":
    print("=== Phase XII: Chronos Interface ===\n")
    
    # Causal graph
    print("=== Causal Graph Construction ===")
    graph = CausalGraph()
    
    # Add events
    t0 = datetime.now().timestamp()
    for i in range(5):
        frame = ChronosFrame(
            frame_id=f"event_{i}",
            timestamp=t0 + i,
            temporal_direction=TemporalDirection.FORWARD,
            causal_parent=None,
            time_coordinate=float(i)
        )
        graph.add_event(frame)
    
    # Add causal links
    graph.add_causal_link('event_0', 'event_1', CausalityType.CAUSES)
    graph.add_causal_link('event_1', 'event_2', CausalityType.ENABLES)
    graph.add_causal_link('event_2', 'event_3', CausalityType.CAUSES)
    
    print(f"Events: {len(graph.events)}")
    print(f"Causal edges: {len(graph.edges)}")
    
    # Topological sort
    ordering = graph.topological_sort()
    if ordering:
        print(f"Causal ordering: {' → '.join(ordering[:5])}")
    
    # Find causal cone
    future_cone = graph.get_causal_cone('event_1', 'future')
    print(f"Future cone of event_1: {len(future_cone)} events\n")
    
    # Time loop
    print("=== Closed Timelike Curve (Time Loop) ===")
    loop = TimeLoop(loop_id='alpha', duration_seconds=10.0)
    
    initial_state = {'x': 1.0, 'y': 2.0, 'z': 3.0}
    result = loop.find_stable_loop(initial_state, max_iterations=50)
    
    if result['success']:
        print(f"Stable loop found!")
        print(f"Iterations to convergence: {result['iterations_to_convergence']}")
        print(f"Final consistency: {result['final_consistency']:.4f}")
    else:
        print(f"Loop failed to stabilize: {result['reason']}")
    
    # Detect cycles
    print(f"\nCausal loops detected: {len(graph.find_cycles())}")
    
    # Retrocausality
    print("\n=== Retrocausality (Backward Causation) ===")
    retro = RetrocausalityEngine()
    
    link = retro.create_retro_link('future_event', 100.0, 50.0, strength=0.7)
    print(f"Retrocausal link created")
    print(f"Time delta: {link['delta_t']:.1f} seconds")
    print(f"Paradox risk: {link['paradox_risk']:.2%}")
    
    # Delayed choice experiment
    print("\n=== Wheeler's Delayed-Choice Experiment ===")
    experiment = retro.delayed_choice_experiment(num_trials=1000)
    print(f"Trials: {experiment['trials']}")
    print(f"Retrocausal events: {experiment['retrocausal_events']} ({experiment['retrocausal_fraction']:.1%})")
    print(f"Sample paths:")
    for i, path in enumerate(experiment['paths'][:3]):
        print(f"  Trial {i}: {path['initial']} → {path['final']} (retro: {path['retrocausal']})")
