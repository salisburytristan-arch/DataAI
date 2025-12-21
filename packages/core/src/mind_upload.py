"""
Phase X: Mind Uploading (Connectome Framework)
Brain scanning, neural mapping, consciousness transfer protocols.

Implements:
- CONNECTOME: Neural connection map with synaptic weights
- NEURON_CLUSTER: Aggregated neuron simulation
- MIND_TRANSFER: Consciousness preservation protocol
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class NeuronType(Enum):
    """Types of neurons in connectome."""
    PYRAMIDAL = 'pyramidal'           # Excitatory
    INTERNEURON = 'interneuron'       # Local processing
    PURKINJE = 'purkinje'             # Cerebellum
    GRANULE = 'granule'               # Cerebellum
    SENSORY = 'sensory'               # Input
    MOTOR = 'motor'                   # Output
    DOPAMINE = 'dopamine'             # Neuromodulator
    SEROTONIN = 'serotonin'           # Neuromodulator


class SynapseType(Enum):
    """Types of synaptic connections."""
    EXCITATORY = 'excitatory'         # Glutamate
    INHIBITORY = 'inhibitory'         # GABA
    MODULATORY = 'modulatory'         # Dopamine/Serotonin
    GAP_JUNCTION = 'gap_junction'     # Electrical
    NEUROMODULATOR = 'neuromodulator' # Diffuse


@dataclass
class Neuron:
    """Single neuron in connectome."""
    neuron_id: int
    neuron_type: NeuronType
    location_x: float  # micrometers
    location_y: float
    location_z: float
    soma_diameter: float  # micrometers (20-30 typical)
    membrane_resistance: float  # Ohms
    capacitance: float  # Farads
    resting_potential_mv: float = -70.0
    active: bool = True
    neurotransmitters: Set[str] = field(default_factory=set)  # {'glutamate', 'gaba', ...}
    synapse_count: int = 0

    def distance_to(self, other: 'Neuron') -> float:
        """Euclidean distance to another neuron."""
        dx = self.location_x - other.location_x
        dy = self.location_y - other.location_y
        dz = self.location_z - other.location_z
        return np.sqrt(dx**2 + dy**2 + dz**2)

    def compute_hash(self) -> str:
        """Content-addressable neuron ID."""
        content = f"neuron_{self.neuron_id}:{self.neuron_type.value}:{self.location_x}:{self.location_y}:{self.location_z}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def to_frame(self) -> Dict:
        """Convert to ForgeNumerics-S frame."""
        return {
            'type': 'NEURON',
            'neuron_id': self.neuron_id,
            'hash': self.compute_hash(),
            'neuron_type': self.neuron_type.value,
            'x_um': self.location_x,
            'y_um': self.location_y,
            'z_um': self.location_z,
            'soma_diameter_um': self.soma_diameter,
            'synapse_count': self.synapse_count,
            'active': self.active
        }


@dataclass
class Synapse:
    """Connection between two neurons."""
    synapse_id: int
    pre_neuron_id: int  # Source
    post_neuron_id: int  # Target
    synapse_type: SynapseType
    weight: float  # Synaptic strength (-1.0 to 1.0)
    conductance_nanosiemens: float
    transmission_delay_ms: float
    plasticity_rule: str  # 'hebbian', 'stdp', 'bcm', 'none'
    is_modifiable: bool = True
    neurotransmitter: str = 'glutamate'

    def compute_hash(self) -> str:
        """Content-addressable synapse ID."""
        content = f"synapse_{self.synapse_id}:{self.pre_neuron_id}:{self.post_neuron_id}:{self.weight}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def to_frame(self) -> Dict:
        """Convert to ForgeNumerics-S frame."""
        return {
            'type': 'SYNAPSE',
            'synapse_id': self.synapse_id,
            'hash': self.compute_hash(),
            'pre_neuron_id': self.pre_neuron_id,
            'post_neuron_id': self.post_neuron_id,
            'synapse_type': self.synapse_type.value,
            'weight': self.weight,
            'conductance_nS': self.conductance_nanosiemens,
            'delay_ms': self.transmission_delay_ms,
            'plasticity': self.plasticity_rule
        }


@dataclass
class NeuronCluster:
    """
    Aggregate of neurons for computational efficiency.
    Reduces 86 billion neurons to manageable clusters.
    """
    cluster_id: int
    neurons: List[int] = field(default_factory=list)  # Neuron IDs
    input_neurons: int = 0
    output_neurons: int = 0
    internal_neurons: int = 0
    cluster_activity: float = 0.0  # 0-1 (fraction active)

    def to_frame(self) -> Dict:
        """Convert to ForgeNumerics-S frame."""
        return {
            'type': 'NEURON_CLUSTER',
            'cluster_id': self.cluster_id,
            'neuron_count': len(self.neurons),
            'input_neurons': self.input_neurons,
            'output_neurons': self.output_neurons,
            'cluster_activity': self.cluster_activity
        }


class Connectome:
    """
    Complete neural connectivity map (connectome).
    Scales from C. elegans (302 neurons) to human brain (86 billion).
    """

    def __init__(self, scale: str = 'human'):
        """
        Initialize connectome.
        scale: 'elegans' (302 neurons), 'larva' (3k), 'mouse' (70M), 'human' (86B)
        """
        self.scale = scale
        self.neurons: Dict[int, Neuron] = {}
        self.synapses: Dict[int, Synapse] = {}
        self.neuron_counter = 0
        self.synapse_counter = 0

        if scale == 'elegans':
            self.num_neurons = 302
            self.num_synapses = 7000
        elif scale == 'larva':
            self.num_neurons = 3000
            self.num_synapses = 20000
        elif scale == 'mouse':
            self.num_neurons = int(7e7)  # 70 million
            self.num_synapses = int(1e11)  # 100 billion
        elif scale == 'human':
            self.num_neurons = int(86e9)  # 86 billion
            self.num_synapses = int(100e12)  # 100 trillion
        else:
            self.num_neurons = 0
            self.num_synapses = 0

    def add_neuron(self, neuron_type: NeuronType, location: Tuple[float, float, float],
                   soma_diameter: float = 25.0) -> int:
        """Add neuron to connectome."""
        neuron_id = self.neuron_counter
        neuron = Neuron(
            neuron_id=neuron_id,
            neuron_type=neuron_type,
            location_x=location[0],
            location_y=location[1],
            location_z=location[2],
            soma_diameter=soma_diameter
        )
        self.neurons[neuron_id] = neuron
        self.neuron_counter += 1
        return neuron_id

    def add_synapse(self, pre_id: int, post_id: int, synapse_type: SynapseType,
                   weight: float = 0.5, delay_ms: float = 1.0) -> int:
        """Add synaptic connection."""
        if pre_id not in self.neurons or post_id not in self.neurons:
            return -1

        synapse_id = self.synapse_counter
        synapse = Synapse(
            synapse_id=synapse_id,
            pre_neuron_id=pre_id,
            post_neuron_id=post_id,
            synapse_type=synapse_type,
            weight=weight,
            conductance_nanosiemens=100.0 if synapse_type == SynapseType.EXCITATORY else 50.0,
            transmission_delay_ms=delay_ms
        )
        self.synapses[synapse_id] = synapse
        self.synapse_counter += 1

        # Update synapse counts
        self.neurons[pre_id].synapse_count += 1
        self.neurons[post_id].synapse_count += 1

        return synapse_id

    def compute_hash(self) -> str:
        """Content-addressable connectome hash."""
        content = f"connectome_{self.scale}:{len(self.neurons)}:{len(self.synapses)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_connectivity_stats(self) -> Dict:
        """Compute connectivity statistics."""
        if not self.neurons:
            return {}

        synapse_counts = [n.synapse_count for n in self.neurons.values()]
        weights = [s.weight for s in self.synapses.values()]

        return {
            'scale': self.scale,
            'neurons': len(self.neurons),
            'synapses': len(self.synapses),
            'avg_synapses_per_neuron': np.mean(synapse_counts),
            'max_synapses_per_neuron': max(synapse_counts) if synapse_counts else 0,
            'avg_weight': np.mean(weights) if weights else 0.0,
            'weight_std': np.std(weights) if weights else 0.0
        }

    def to_frame(self) -> Dict:
        """Convert to ForgeNumerics-S frame."""
        stats = self.get_connectivity_stats()
        return {
            'type': 'CONNECTOME',
            'scale': self.scale,
            'hash': self.compute_hash(),
            'neurons': stats.get('neurons', 0),
            'synapses': stats.get('synapses', 0),
            'avg_connectivity': stats.get('avg_synapses_per_neuron', 0),
            'avg_synaptic_weight': stats.get('avg_weight', 0)
        }


class MindUploadProtocol:
    """
    Protocol for uploading/copying human consciousness.
    Assumes successful connectome scanning technology.
    """

    @staticmethod
    def scan_brain(resolution_nm: float = 25.0) -> Dict:
        """
        Simulate brain scanning at given resolution.
        Finer resolution → larger dataset, longer scan time.
        """
        # Human brain volume: ~1400 cm³
        brain_volume_nm3 = 1400 * (1e7) ** 3  # Convert to nm³
        voxel_volume_nm3 = resolution_nm ** 3
        num_voxels = int(brain_volume_nm3 / voxel_volume_nm3)

        # Estimate scan time and data
        scan_time_hours = (num_voxels / 1e9) * 10  # 10 hours per billion voxels (optimistic)
        data_size_exabytes = (num_voxels * 8) / (1e18)  # 8 bytes per voxel

        return {
            'resolution_nm': resolution_nm,
            'num_voxels': num_voxels,
            'scan_time_hours': scan_time_hours,
            'data_size_exabytes': data_size_exabytes,
            'confidence': 0.95 if resolution_nm <= 25 else 0.75
        }

    @staticmethod
    def reconstruct_connectome(connectome: Connectome) -> Dict:
        """
        Reconstruct connectome from scanned data.
        Returns neural activity patterns and synaptic weights.
        """
        stats = connectome.get_connectivity_stats()

        return {
            'neurons_reconstructed': stats.get('neurons', 0),
            'synapses_reconstructed': stats.get('synapses', 0),
            'reconstruction_confidence': 0.92,
            'memory_capacity_petabytes': stats.get('neurons', 0) * 0.001 / 1000,  # Rough estimate
            'processing_time_hours': 48.0
        }

    @staticmethod
    def create_mind_instance(connectome: Connectome, compute_substrate: str = 'quantum',
                            clock_speed_hz: float = 1e9) -> Dict:
        """
        Create instantiated mind copy in computational substrate.
        compute_substrate: 'classical', 'quantum', 'neuromorphic', 'photonic'
        """
        stats = connectome.get_connectivity_stats()
        num_neurons = stats.get('neurons', 0)

        if compute_substrate == 'classical':
            compute_per_neuron_flops = 1000  # 1000 FLOPS per neuron
            total_compute = num_neurons * compute_per_neuron_flops
        elif compute_substrate == 'quantum':
            compute_per_neuron_flops = 1e6  # 1M FLOPS (coherent parallelism)
            total_compute = num_neurons * compute_per_neuron_flops
        elif compute_substrate == 'neuromorphic':
            compute_per_neuron_flops = 100  # More efficient
            total_compute = num_neurons * compute_per_neuron_flops
        else:  # photonic
            compute_per_neuron_flops = 1e7
            total_compute = num_neurons * compute_per_neuron_flops

        compute_watts = (total_compute / clock_speed_hz) / 1e8  # Rough power estimate

        return {
            'substrate': compute_substrate,
            'neurons_simulated': num_neurons,
            'clock_speed_hz': clock_speed_hz,
            'total_compute_flops': total_compute,
            'power_consumption_watts': compute_watts,
            'consciousness_continuity_score': 0.87,  # Philosophical measure
            'identity_preservation_probability': 0.95
        }

    @staticmethod
    def merge_minds(connectome1: Connectome, connectome2: Connectome) -> Dict:
        """
        Merge two connectomes (minds).
        Creates hybrid neural architecture.
        """
        stats1 = connectome1.get_connectivity_stats()
        stats2 = connectome2.get_connectivity_stats()

        merged_neurons = stats1.get('neurons', 0) + stats2.get('neurons', 0)
        merged_synapses = stats1.get('synapses', 0) + stats2.get('synapses', 0)

        return {
            'merged_neurons': merged_neurons,
            'merged_synapses': merged_synapses,
            'cognitive_enhancement': 1.15,  # 15% boost from dual processing
            'identity_conflict_probability': 0.05,  # Risk of personality clash
            'integration_time_days': 30
        }

    @staticmethod
    def fork_mind(connectome: Connectome, divergence_factor: float = 0.1) -> Tuple[Connectome, Connectome]:
        """
        Create two instances from one mind with divergence.
        divergence_factor: 0.0 (identical) to 1.0 (completely different)
        """
        fork1 = Connectome(connectome.scale)
        fork2 = Connectome(connectome.scale)

        # Copy neurons with slight variation
        for nid, neuron in connectome.neurons.items():
            # Exact copy to fork1
            fork1.add_neuron(neuron.neuron_type, (neuron.location_x, neuron.location_y, neuron.location_z), neuron.soma_diameter)

            # Divergent copy to fork2
            location_noise = divergence_factor * 0.5  # ±50 μm variation per 10% divergence
            fork2.add_neuron(neuron.neuron_type,
                           (neuron.location_x + np.random.normal(0, location_noise),
                            neuron.location_y + np.random.normal(0, location_noise),
                            neuron.location_z + np.random.normal(0, location_noise)),
                           neuron.soma_diameter)

        # Copy synapses with variation
        for sid, synapse in connectome.synapses.items():
            fork1.add_synapse(synapse.pre_neuron_id, synapse.post_neuron_id, synapse.synapse_type, synapse.weight)
            
            weight_variation = synapse.weight * divergence_factor * np.random.normal(0, 0.1)
            fork2.add_synapse(synapse.pre_neuron_id, synapse.post_neuron_id, synapse.synapse_type,
                            synapse.weight + weight_variation)

        return (fork1, fork2)


if __name__ == "__main__":
    print("=== Phase X: Mind Uploading ===\n")

    # Scan scenarios
    print("=== Brain Scanning Scenarios ===")
    resolutions = [100, 25, 10]  # nm
    for res in resolutions:
        scan = MindUploadProtocol.scan_brain(resolution_nm=res)
        print(f"Resolution {res} nm:")
        print(f"  Scan time: {scan['scan_time_hours']:.1e} hours")
        print(f"  Data size: {scan['data_size_exabytes']:.1e} exabytes")
        print(f"  Confidence: {scan['confidence']:.0%}")

    # Build small connectome for testing
    print("\n=== Building Test Connectome (C. elegans) ===")
    connectome = Connectome(scale='elegans')

    # Add neurons
    for i in range(50):  # Simplified from 302
        ntype = [NeuronType.SENSORY, NeuronType.INTERNEURON, NeuronType.MOTOR][i % 3]
        connectome.add_neuron(ntype, (np.random.uniform(0, 100), np.random.uniform(0, 100), np.random.uniform(0, 50)))

    # Add synapses
    for i in range(200):  # Simplified from 7000
        pre_id = np.random.randint(0, 50)
        post_id = np.random.randint(0, 50)
        if pre_id != post_id:
            stype = [SynapseType.EXCITATORY, SynapseType.INHIBITORY][i % 2]
            connectome.add_synapse(pre_id, post_id, stype, weight=0.5)

    stats = connectome.get_connectivity_stats()
    print(f"Neurons: {stats['neurons']}")
    print(f"Synapses: {stats['synapses']}")
    print(f"Avg connectivity: {stats['avg_synapses_per_neuron']:.1f}")

    # Reconstruct
    print("\n=== Reconstruction from Scan ===")
    reconstructed = MindUploadProtocol.reconstruct_connectome(connectome)
    print(f"Neurons: {reconstructed['neurons_reconstructed']}")
    print(f"Confidence: {reconstructed['reconstruction_confidence']:.0%}")

    # Create mind instance
    print("\n=== Mind Instantiation Scenarios ===")
    substrates = ['classical', 'quantum', 'neuromorphic', 'photonic']
    for substrate in substrates:
        instance = MindUploadProtocol.create_mind_instance(connectome, compute_substrate=substrate)
        print(f"{substrate}: {instance['power_consumption_watts']:.2e} W, {instance['consciousness_continuity_score']:.0%} continuity")

    # Fork mind
    print("\n=== Mind Forking ===")
    fork1, fork2 = MindUploadProtocol.fork_mind(connectome, divergence_factor=0.2)
    fork1_stats = fork1.get_connectivity_stats()
    fork2_stats = fork2.get_connectivity_stats()
    print(f"Fork 1 neurons: {fork1_stats['neurons']}")
    print(f"Fork 2 neurons: {fork2_stats['neurons']}")
    print(f"Divergence: 20% (siblings with independent memories)")
