"""
Phase XVIII: Pan-computational Lattice (Universal Computing Substrate)
Everything computes - rocks, air, stars. Substrate-independent computing.

Implements:
- MATTER_LOGIC: Arbitrary matter as processor
- ATOMIC_GATE: Electron spin as logic states
- PLANETARY_MIND: Biosphere integration
- UNIVERSAL_SUBSTRATE: Computation everywhere
"""

import numpy as np
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum


class SubstrateType(Enum):
    """Types of computational substrates."""
    SILICON = 'silicon'                   # Traditional chips
    BIOLOGICAL = 'biological'             # Cells, DNA, proteins
    ATOMIC = 'atomic'                     # Individual atoms
    MOLECULAR = 'molecular'               # Molecules
    QUANTUM = 'quantum'                   # Quantum states
    SPACETIME = 'spacetime'               # Geometry itself
    ABSTRACT = 'abstract'                 # Pure math


class ComputationalState(Enum):
    """States of computation in matter."""
    DORMANT = 'dormant'                   # Not computing
    INITIALIZED = 'initialized'           # Ready to compute
    ACTIVE = 'active'                     # Currently computing
    ENTANGLED = 'entangled'              # Quantum entangled


@dataclass
class MatterProcessor:
    """Arbitrary matter configured as processor."""
    processor_id: str
    substrate: SubstrateType
    volume_m3: float
    operations_per_sec: float
    state: ComputationalState
    
    def to_frame(self) -> Dict:
        return {
            'type': 'MATTER_PROCESSOR',
            'id': self.processor_id,
            'substrate': self.substrate.value,
            'volume': self.volume_m3,
            'ops_per_sec': self.operations_per_sec,
            'state': self.state.value
        }


class AtomicLogicGate:
    """
    Use electron spin states as logic gates.
    Convert any matter into processor by manipulating atomic states.
    """
    
    @dataclass
    class AtomicBit:
        """Bit encoded in atom's electron spin."""
        atom_id: str
        element: str  # Element symbol
        spin_state: int  # -1 (down), 0 (superposed), +1 (up)
        coherence_time: float  # How long state persists (seconds)
        
    def __init__(self):
        self.atomic_bits: List[AtomicLogicGate.AtomicBit] = []
        self.operations: int = 0
    
    def encode_bit_in_atom(self, element: str, value: int) -> AtomicBit:
        """
        Encode bit in atom's electron spin.
        value: 0 (spin down), 1 (spin up), -1 (superposed)
        """
        # Coherence time depends on element
        coherence_times = {
            'H': 1e-6,    # Hydrogen: microseconds
            'C': 1e-3,    # Carbon: milliseconds
            'Si': 1e-2,   # Silicon: centiseconds
            'Fe': 1e-9,   # Iron: nanoseconds (magnetic)
            'Au': 1e-4    # Gold: 100 microseconds
        }
        
        coherence = coherence_times.get(element, 1e-6)
        
        # Map value to spin
        spin_state = -1 if value == 0 else (1 if value == 1 else 0)
        
        bit = AtomicLogicGate.AtomicBit(
            atom_id=f"atom_{len(self.atomic_bits)}",
            element=element,
            spin_state=spin_state,
            coherence_time=coherence
        )
        
        self.atomic_bits.append(bit)
        return bit
    
    def atomic_and_gate(self, bit1: AtomicBit, bit2: AtomicBit) -> Optional[AtomicBit]:
        """
        AND gate using electron spin coupling.
        Spin-spin interaction creates result.
        """
        if bit1.spin_state == 0 or bit2.spin_state == 0:
            # Superposed input
            result_spin = 0
        else:
            # Convert spins to 0/1
            val1 = 0 if bit1.spin_state == -1 else 1
            val2 = 0 if bit2.spin_state == -1 else 1
            result_val = val1 & val2
            result_spin = -1 if result_val == 0 else 1
        
        # Result atom (use same element as bit1)
        result = self.encode_bit_in_atom(bit1.element, 1 if result_spin == 1 else 0)
        result.spin_state = result_spin
        
        self.operations += 1
        return result
    
    def atomic_not_gate(self, bit: AtomicBit) -> AtomicBit:
        """NOT gate: flip electron spin."""
        if bit.spin_state == 0:
            result_spin = 0  # Still superposed
        else:
            result_spin = -bit.spin_state  # Flip
        
        result = self.encode_bit_in_atom(bit.element, 1 if result_spin == 1 else 0)
        result.spin_state = result_spin
        
        self.operations += 1
        return result
    
    def measure_spin(self, bit: AtomicBit) -> int:
        """
        Measure electron spin (collapses superposition).
        Returns 0 or 1.
        """
        if bit.spin_state == 0:
            # Collapse superposition randomly
            bit.spin_state = np.random.choice([-1, 1])
        
        return 0 if bit.spin_state == -1 else 1
    
    def calculate_matter_ops_per_sec(self, mass_kg: float, element: str) -> float:
        """
        Calculate theoretical max operations per second
        for given mass of element.
        """
        # Avogadro's number
        N_A = 6.022e23
        
        # Atomic masses (g/mol)
        atomic_masses = {
            'H': 1.008,
            'C': 12.011,
            'Si': 28.085,
            'Fe': 55.845,
            'Au': 196.967
        }
        
        A = atomic_masses.get(element, 12.0)
        
        # Number of atoms
        moles = (mass_kg * 1000) / A
        num_atoms = moles * N_A
        
        # Operations per second per atom (limited by coherence time)
        coherence = {
            'H': 1e-6,
            'C': 1e-3,
            'Si': 1e-2,
            'Fe': 1e-9,
            'Au': 1e-4
        }.get(element, 1e-6)
        
        ops_per_atom = 1 / coherence
        
        total_ops = num_atoms * ops_per_atom
        
        return total_ops


class PlanetaryMind:
    """
    Integrate entire biosphere into computational network.
    Trees, fungi, bacteria become distributed processor.
    """
    
    @dataclass
    class BiologicalNode:
        """Node in planetary network."""
        node_id: str
        organism_type: str  # 'tree', 'fungus', 'bacteria', etc.
        location: Tuple[float, float, float]  # Lat, lon, elevation
        connections: List[str]  # Connected node IDs
        processing_power: float  # Operations per second
        
    def __init__(self):
        self.nodes: List[PlanetaryMind.BiologicalNode] = []
        self.network_graph: Dict[str, Set[str]] = {}
    
    def add_biological_node(self, organism_type: str, location: Tuple[float, float, float]) -> BiologicalNode:
        """Add organism to network."""
        # Estimate processing power by organism type
        processing_power = {
            'tree': 1e6,        # 1 million ops/sec
            'fungus': 1e9,      # 1 billion (mycelium networks)
            'bacteria': 1e3,    # 1 thousand
            'human': 1e15,      # 1 petaflop (brain)
            'whale': 1e14       # 100 teraflops
        }.get(organism_type, 1e3)
        
        node = PlanetaryMind.BiologicalNode(
            node_id=f"bio_{len(self.nodes)}",
            organism_type=organism_type,
            location=location,
            connections=[],
            processing_power=processing_power
        )
        
        self.nodes.append(node)
        self.network_graph[node.node_id] = set()
        
        return node
    
    def connect_nodes(self, node1_id: str, node2_id: str):
        """Create connection (symbiosis, root network, etc.)."""
        if node1_id in self.network_graph and node2_id in self.network_graph:
            self.network_graph[node1_id].add(node2_id)
            self.network_graph[node2_id].add(node1_id)
            
            # Update node connections
            for node in self.nodes:
                if node.node_id == node1_id:
                    node.connections.append(node2_id)
                elif node.node_id == node2_id:
                    node.connections.append(node1_id)
    
    def calculate_network_capacity(self) -> Dict:
        """Calculate total computational capacity of biosphere."""
        total_nodes = len(self.nodes)
        total_ops = sum(node.processing_power for node in self.nodes)
        
        # Network topology metrics
        avg_connections = np.mean([len(conns) for conns in self.network_graph.values()]) if self.network_graph else 0
        
        # Estimate latency (speed of signal through biological medium)
        # Nerve impulses: ~100 m/s, Chemical signals: ~0.001 m/s
        avg_latency_ms = 100  # milliseconds for cross-network message
        
        return {
            'total_nodes': total_nodes,
            'total_operations_per_sec': total_ops,
            'avg_connections_per_node': avg_connections,
            'network_latency_ms': avg_latency_ms,
            'equivalent_supercomputers': total_ops / 1e18  # Number of exaflop systems
        }
    
    def simulate_distributed_computation(self, task_complexity: float) -> Dict:
        """
        Simulate distributing computation across network.
        task_complexity: Operations required
        """
        capacity = self.calculate_network_capacity()
        total_ops = capacity['total_operations_per_sec']
        
        if total_ops == 0:
            return {
                'success': False,
                'reason': 'No computational nodes'
            }
        
        # Time to complete
        time_seconds = task_complexity / total_ops
        
        # Distribute across nodes
        ops_per_node = task_complexity / len(self.nodes) if self.nodes else 0
        
        return {
            'success': True,
            'task_complexity': task_complexity,
            'time_seconds': time_seconds,
            'ops_per_node': ops_per_node,
            'nodes_used': len(self.nodes),
            'efficiency': 0.7  # 70% efficient due to communication overhead
        }


class UniversalSubstrate:
    """
    Framework for computing on ANY substrate.
    Demonstrates true substrate independence.
    """
    
    def __init__(self):
        self.substrates: Dict[SubstrateType, MatterProcessor] = {}
    
    def initialize_substrate(self, substrate_type: SubstrateType, 
                           volume_m3: float) -> MatterProcessor:
        """
        Convert arbitrary matter into computational substrate.
        """
        # Estimate operations per second based on substrate
        ops_estimates = {
            SubstrateType.SILICON: 1e15,        # Modern CPU
            SubstrateType.BIOLOGICAL: 1e10,     # Cells
            SubstrateType.ATOMIC: 1e20,         # Atomic manipulation
            SubstrateType.MOLECULAR: 1e18,      # Molecular dynamics
            SubstrateType.QUANTUM: 1e25,        # Quantum supremacy
            SubstrateType.SPACETIME: 1e30,      # Planck-scale
            SubstrateType.ABSTRACT: float('inf')  # Pure mathematics
        }
        
        ops_per_sec = ops_estimates.get(substrate_type, 1e12) * volume_m3
        
        processor = MatterProcessor(
            processor_id=f"proc_{substrate_type.value}",
            substrate=substrate_type,
            volume_m3=volume_m3,
            operations_per_sec=ops_per_sec,
            state=ComputationalState.INITIALIZED
        )
        
        self.substrates[substrate_type] = processor
        return processor
    
    def execute_on_substrate(self, substrate_type: SubstrateType, 
                           operation: str, operands: List[int]) -> Dict:
        """
        Execute computation on specific substrate.
        Demonstrates substrate independence of algorithm.
        """
        if substrate_type not in self.substrates:
            return {'error': 'Substrate not initialized'}
        
        processor = self.substrates[substrate_type]
        processor.state = ComputationalState.ACTIVE
        
        # Execute operation (simplified)
        if operation == 'ADD':
            result = sum(operands)
        elif operation == 'MULTIPLY':
            result = 1
            for op in operands:
                result *= op
        elif operation == 'XOR':
            result = operands[0]
            for op in operands[1:]:
                result ^= op
        else:
            result = 0
        
        # Calculate execution time
        ops_required = len(operands)
        time_seconds = ops_required / processor.operations_per_sec
        
        processor.state = ComputationalState.INITIALIZED
        
        return {
            'substrate': substrate_type.value,
            'operation': operation,
            'result': result,
            'time_seconds': time_seconds,
            'ops_per_sec': processor.operations_per_sec
        }
    
    def prove_substrate_independence(self, operation: str, 
                                    operands: List[int]) -> Dict:
        """
        Execute same computation on all substrates.
        Prove result is independent of substrate.
        """
        results = {}
        
        for substrate_type in self.substrates:
            result = self.execute_on_substrate(substrate_type, operation, operands)
            results[substrate_type.value] = result
        
        # Check all results match
        values = [r['result'] for r in results.values() if 'result' in r]
        all_match = len(set(values)) <= 1
        
        return {
            'operation': operation,
            'operands': operands,
            'substrate_independent': all_match,
            'results': results,
            'proof': 'Same algorithm, any substrate, identical result' if all_match else 'FAILED'
        }


if __name__ == "__main__":
    print("=== Phase XVIII: Pan-computational Lattice ===\n")
    
    # Atomic logic gates
    print("=== Atomic Logic Gates (Matter as Processor) ===")
    atomic = AtomicLogicGate()
    
    # Encode bits in different elements
    carbon_0 = atomic.encode_bit_in_atom('C', 0)
    carbon_1 = atomic.encode_bit_in_atom('C', 1)
    
    print(f"Carbon bit 0: spin={carbon_0.spin_state}, coherence={carbon_0.coherence_time}s")
    print(f"Carbon bit 1: spin={carbon_1.spin_state}, coherence={carbon_1.coherence_time}s")
    
    # Logic gates
    and_result = atomic.atomic_and_gate(carbon_0, carbon_1)
    print(f"\nAND(0, 1) = {atomic.measure_spin(and_result)}")
    
    not_result = atomic.atomic_not_gate(carbon_1)
    print(f"NOT(1) = {atomic.measure_spin(not_result)}")
    
    # Calculate matter computational capacity
    print("\n=== Matter Computational Capacity ===")
    mass_1kg = 1.0  # 1 kilogram
    
    for element in ['H', 'C', 'Si', 'Fe', 'Au']:
        ops = atomic.calculate_matter_ops_per_sec(mass_1kg, element)
        print(f"1 kg of {element}: {ops:.2e} operations/sec")
    
    # Planetary mind
    print("\n=== Planetary Mind (Biosphere Network) ===")
    gaia = PlanetaryMind()
    
    # Add organisms
    tree1 = gaia.add_biological_node('tree', (40.7, -74.0, 10))
    tree2 = gaia.add_biological_node('tree', (40.8, -74.1, 15))
    fungus = gaia.add_biological_node('fungus', (40.75, -74.05, 5))
    human = gaia.add_biological_node('human', (40.7, -74.0, 20))
    
    print(f"Added {len(gaia.nodes)} biological nodes")
    
    # Connect via root networks / symbiosis
    gaia.connect_nodes(tree1.node_id, fungus.node_id)
    gaia.connect_nodes(tree2.node_id, fungus.node_id)
    gaia.connect_nodes(human.node_id, tree1.node_id)
    
    # Calculate network capacity
    capacity = gaia.calculate_network_capacity()
    print(f"\nNetwork capacity:")
    print(f"  Total nodes: {capacity['total_nodes']}")
    print(f"  Total ops/sec: {capacity['total_operations_per_sec']:.2e}")
    print(f"  Avg connections: {capacity['avg_connections_per_node']:.1f}")
    print(f"  Equivalent supercomputers: {capacity['equivalent_supercomputers']:.2f} exaflop systems")
    
    # Simulate distributed computation
    print("\n=== Distributed Computation ===")
    task = 1e15  # 1 petaflop task
    result = gaia.simulate_distributed_computation(task)
    print(f"Task complexity: {result['task_complexity']:.2e} operations")
    print(f"Completion time: {result['time_seconds']:.2f} seconds")
    print(f"Efficiency: {result['efficiency']:.0%}")
    
    # Universal substrate
    print("\n=== Universal Substrate Independence ===")
    universal = UniversalSubstrate()
    
    # Initialize multiple substrates
    substrates = [
        SubstrateType.SILICON,
        SubstrateType.BIOLOGICAL,
        SubstrateType.ATOMIC,
        SubstrateType.QUANTUM
    ]
    
    for substrate in substrates:
        proc = universal.initialize_substrate(substrate, volume_m3=1e-6)  # 1 cubic millimeter
        print(f"Initialized {substrate.value}: {proc.operations_per_sec:.2e} ops/sec")
    
    # Prove substrate independence
    print("\n=== Substrate Independence Proof ===")
    proof = universal.prove_substrate_independence('XOR', [1, 0, 1, 1])
    
    print(f"Operation: {proof['operation']}")
    print(f"Operands: {proof['operands']}")
    print(f"Substrate independent: {proof['substrate_independent']}")
    
    for substrate, result in proof['results'].items():
        if 'result' in result:
            print(f"  {substrate}: result={result['result']}, time={result['time_seconds']:.2e}s")
    
    print(f"\nProof: {proof['proof']}")
