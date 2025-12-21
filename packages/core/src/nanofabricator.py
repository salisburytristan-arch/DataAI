"""
Phase VII: Nanofabricator (Molecular Assembly Engine)
Molecular machines, automated assembly sequences, and quality control.

Implements:
- NANO_ARM: Robotic arm with atomic precision
- ASSEMBLY_PROTOCOL: Step-by-step molecular construction
- QUALITY_CONTROL: Inspection and error correction
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class NanoArmTool(Enum):
    """End-effector tools for nano-scale manipulation."""
    PICKER = 'picker'              # Grab individual atoms
    BONDER = 'bonder'              # Form chemical bonds
    UNBONDER = 'unbonder'          # Break chemical bonds
    PROBE = 'probe'                # Measure distance/force
    HEATER = 'heater'              # Local heating (electron beam)
    COLDER = 'colder'              # Local cooling (liquid He)
    SENSOR = 'sensor'              # Detect elements/properties


@dataclass
class Position3D:
    """3D position in nanometers (nm)."""
    x: float  # nm
    y: float
    z: float

    def distance_to(self, other: 'Position3D') -> float:
        """Euclidean distance."""
        return np.sqrt(
            (self.x - other.x)**2 +
            (self.y - other.y)**2 +
            (self.z - other.z)**2
        )

    def move_towards(self, target: 'Position3D', step_nm: float) -> 'Position3D':
        """Move towards target by step_nm nanometers."""
        dist = self.distance_to(target)
        if dist < step_nm:
            return Position3D(target.x, target.y, target.z)
        
        ratio = step_nm / dist
        return Position3D(
            self.x + (target.x - self.x) * ratio,
            self.y + (target.y - self.y) * ratio,
            self.z + (target.z - self.z) * ratio
        )


@dataclass
class NanoArm:
    """
    Scanning Tunneling Microscope / Atomic Force Microscope arm.
    Can position atoms with ~0.1 nm precision.
    """
    base_position: Position3D
    current_tool: NanoArmTool = NanoArmTool.PICKER
    tip_position: Position3D = field(default_factory=lambda: Position3D(0, 0, 0))
    force_limit_nN: float = 10.0  # Nanonewtons (prevent damage)
    current_force_nN: float = 0.0
    
    def move_to(self, target: Position3D, step_nm: float = 0.001) -> int:
        """Move tip to target position. Returns steps needed."""
        steps = 0
        while self.tip_position.distance_to(target) > 0.001:
            self.tip_position = self.tip_position.move_towards(target, step_nm)
            steps += 1
            if steps > 100000:  # Safety limit
                break
        return steps

    def measure_force(self) -> float:
        """Read current force at tip."""
        # Simulate noise
        noise = np.random.normal(0, 0.5)  # ±0.5 nN noise
        return max(0, self.current_force_nN + noise)

    def pick_atom(self, atom_id: int) -> bool:
        """Attempt to pick up atom. Returns success."""
        if self.current_force_nN > self.force_limit_nN:
            return False
        self.current_force_nN = 3.0  # Adhesion force
        return True

    def place_atom(self, target_pos: Position3D) -> bool:
        """Place atom at target position. Returns success."""
        steps = self.move_to(target_pos)
        self.current_force_nN = 0.0
        return steps < 100000


@dataclass
class AssemblyInstruction:
    """Single step in assembly sequence."""
    step_id: int
    tool_required: NanoArmTool
    target_position: Position3D
    action: str  # 'pick', 'place', 'bond', 'measure'
    atom_id: Optional[int] = None
    expected_force_nN: Optional[float] = None
    timeout_ms: float = 10000
    
    def to_frame(self) -> Dict:
        """Convert to ForgeNumerics-S frame."""
        return {
            'type': 'NANO_INSTRUCTION',
            'step': self.step_id,
            'tool': self.tool_required.value,
            'action': self.action,
            'x_nm': self.target_position.x,
            'y_nm': self.target_position.y,
            'z_nm': self.target_position.z,
            'atom_id': self.atom_id,
            'timeout_ms': self.timeout_ms
        }


@dataclass
class AssemblyProtocol:
    """Complete molecular assembly procedure."""
    protocol_id: str
    description: str
    target_structure: str  # What's being built
    instructions: List[AssemblyInstruction] = field(default_factory=list)
    estimated_time_minutes: float = 0.0
    required_temperature_k: float = 298.15  # 25°C
    required_vacuum_torr: float = 1e-10
    success_probability: float = 0.0
    
    def add_instruction(self, instruction: AssemblyInstruction) -> None:
        """Add step to protocol."""
        instruction.step_id = len(self.instructions)
        self.instructions.append(instruction)

    def compute_hash(self) -> str:
        """Content-addressable hash."""
        content = f"{self.protocol_id}:{self.target_structure}:{len(self.instructions)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_frame(self) -> Dict:
        """Convert to ForgeNumerics-S frame."""
        return {
            'type': 'ASSEMBLY_PROTOCOL',
            'protocol_id': self.protocol_id,
            'target': self.target_structure,
            'hash': self.compute_hash(),
            'steps': len(self.instructions),
            'time_minutes': self.estimated_time_minutes,
            'temperature_k': self.required_temperature_k,
            'vacuum_torr': self.required_vacuum_torr,
            'success_probability': self.success_probability,
            'instructions': [instr.to_frame() for instr in self.instructions[:5]]
        }


class NanofabricatorEngine:
    """
    Orchestrates atomic-scale manufacturing.
    Simulates STM/AFM-based molecule construction.
    """

    @staticmethod
    def design_carbon_nanotube(diameter_nm: float = 1.0, length_nm: float = 100.0) -> AssemblyProtocol:
        """
        Design assembly protocol for carbon nanotube.
        Single-wall or multi-wall carbon nanotubes (CNTs).
        """
        protocol = AssemblyProtocol(
            protocol_id='cnt_synthesis_001',
            description='Single-wall carbon nanotube via nanofabricator',
            target_structure='(10,0) armchair CNT',
            required_temperature_k=298.15,
            required_vacuum_torr=1e-11,
            estimated_time_minutes=240.0  # 4 hours
        )

        # Simplified assembly: place carbon atoms in helix
        base_x, base_y, base_z = 0.0, 0.0, 0.0
        atoms_per_ring = 10
        rings = int(length_nm / 0.34)  # 0.34 nm is C-C bond length in graphite

        for ring in range(rings):
            for atom in range(atoms_per_ring):
                angle = (2 * np.pi * atom) / atoms_per_ring
                x = (diameter_nm / 2) * np.cos(angle)
                y = (diameter_nm / 2) * np.sin(angle)
                z = ring * 0.34

                instr = AssemblyInstruction(
                    step_id=ring * atoms_per_ring + atom,
                    tool_required=NanoArmTool.BONDER,
                    target_position=Position3D(x, y, z),
                    action='bond',
                    atom_id=ring * atoms_per_ring + atom,
                    expected_force_nN=1.5
                )
                protocol.add_instruction(instr)

        protocol.estimated_time_minutes = rings * atoms_per_ring * 0.5
        protocol.success_probability = 0.78 if rings < 500 else 0.65
        return protocol

    @staticmethod
    def design_protein_assembly(amino_acids: List[str],
                               cofactors: List[str] = None) -> AssemblyProtocol:
        """
        Design assembly protocol for custom protein from amino acids.
        Builds peptide bond-by-peptide bond.
        """
        protocol = AssemblyProtocol(
            protocol_id='protein_assembly_001',
            description='Custom peptide synthesis via nanofabricator',
            target_structure=f"Protein[{len(amino_acids)} AA]",
            required_temperature_k=310.15,  # 37°C (body temperature)
            required_vacuum_torr=1e-8,  # Less strict than CNT
            estimated_time_minutes=120.0
        )

        positions = []
        for i in range(len(amino_acids)):
            # Spiral backbone
            angle = i * 0.3  # Radians
            x = 0.4 * np.cos(angle)
            y = 0.4 * np.sin(angle)
            z = i * 0.38  # Peptide bond length
            positions.append(Position3D(x, y, z))

        # Bond amino acids in sequence
        for i in range(len(amino_acids) - 1):
            instr = AssemblyInstruction(
                step_id=i,
                tool_required=NanoArmTool.BONDER,
                target_position=positions[i],
                action='peptide_bond',
                atom_id=i,
                expected_force_nN=2.0
            )
            protocol.add_instruction(instr)

        # Add cofactors if any
        if cofactors:
            for j, cofactor in enumerate(cofactors):
                instr = AssemblyInstruction(
                    step_id=len(amino_acids) + j,
                    tool_required=NanoArmTool.BONDER,
                    target_position=Position3D(0.5, 0.5, len(amino_acids) * 0.38),
                    action='bind_cofactor',
                    expected_force_nN=1.0
                )
                protocol.add_instruction(instr)

        protocol.success_probability = 0.85
        return protocol

    @staticmethod
    def design_memory_storage_molecule(bits: int = 64) -> AssemblyProtocol:
        """
        Design molecule for information storage.
        Each azobenzene switch can store 1 bit via cis/trans isomerization.
        """
        protocol = AssemblyProtocol(
            protocol_id='memory_molecule_001',
            description='Molecular memory storage device',
            target_structure=f"MemoryMol[{bits} bits]",
            required_temperature_k=298.15,
            required_vacuum_torr=1e-9,
            estimated_time_minutes=60.0
        )

        # Assemble backbone (polyyne chain)
        for i in range(bits):
            x = i * 0.5
            y = 0.0
            z = 0.0
            instr = AssemblyInstruction(
                step_id=i,
                tool_required=NanoArmTool.BONDER,
                target_position=Position3D(x, y, z),
                action='place_bit_storage_unit',
                atom_id=i,
                expected_force_nN=1.2
            )
            protocol.add_instruction(instr)

        protocol.success_probability = 0.82
        return protocol


class QualityControl:
    """
    Inspect assembled structures and detect/correct errors.
    """

    @staticmethod
    def scan_structure(protocol: AssemblyProtocol) -> Dict:
        """
        Inspect assembled structure via AFM.
        Returns detected defects and measurements.
        """
        # Simulate measurement error
        measurement_error = 0.05  # 5% error
        
        detected_atoms = len(protocol.instructions)
        defects = max(0, int(detected_atoms * 0.02 * np.random.random()))  # 0-2% defect rate
        
        measurements = {
            'atoms_found': detected_atoms,
            'defects_detected': defects,
            'defect_rate': defects / detected_atoms if detected_atoms > 0 else 0,
            'structural_integrity': 1.0 - (defects / detected_atoms * 0.1),
            'measurement_confidence': 0.95
        }
        
        return measurements

    @staticmethod
    def compute_success_metric(measurements: Dict) -> float:
        """Compute overall quality score (0-1)."""
        defect_penalty = measurements['defect_rate'] * 0.3
        confidence = measurements['measurement_confidence']
        integrity = measurements['structural_integrity']
        
        return (integrity - defect_penalty) * confidence

    @staticmethod
    def propose_repair(measurements: Dict, protocol: AssemblyProtocol) -> Optional[AssemblyProtocol]:
        """
        If defects detected, design repair protocol.
        Uses spatial localization to target only defect regions.
        """
        if measurements['defects_detected'] == 0:
            return None

        repair = AssemblyProtocol(
            protocol_id=f"{protocol.protocol_id}_repair",
            description=f"Repair {measurements['defects_detected']} defects",
            target_structure=protocol.target_structure,
            required_temperature_k=protocol.required_temperature_k,
            estimated_time_minutes=measurements['defects_detected'] * 5.0
        )

        # Add repair instructions for each defect
        for i in range(measurements['defects_detected']):
            instr = AssemblyInstruction(
                step_id=i,
                tool_required=NanoArmTool.UNBONDER,
                target_position=Position3D(
                    np.random.uniform(0, 10),
                    np.random.uniform(0, 10),
                    np.random.uniform(0, 10)
                ),
                action='remove_defect',
                expected_force_nN=2.5
            )
            repair.add_instruction(instr)

        repair.success_probability = 0.90
        return repair


if __name__ == "__main__":
    print("=== Phase VII: Nanofabricator ===\n")

    # Test CNT assembly
    print("=== Carbon Nanotube Assembly ===")
    cnt = NanofabricatorEngine.design_carbon_nanotube(diameter_nm=1.4, length_nm=50.0)
    print(f"Protocol: {cnt.protocol_id}")
    print(f"Steps: {len(cnt.instructions)}")
    print(f"Estimated time: {cnt.estimated_time_minutes:.1f} minutes")
    print(f"Success probability: {cnt.success_probability:.0%}\n")

    # Test protein assembly
    print("=== Protein Assembly ===")
    protein = NanofabricatorEngine.design_protein_assembly(
        amino_acids=['M', 'A', 'L', 'E', 'G'],
        cofactors=['NAD+', 'FAD']
    )
    print(f"Protocol: {protein.protocol_id}")
    print(f"Steps: {len(protein.instructions)}")
    print(f"Temperature: {protein.required_temperature_k - 273.15:.0f}°C")
    print(f"Success probability: {protein.success_probability:.0%}\n")

    # Test memory molecule
    print("=== Memory Storage Molecule ===")
    memory = NanofabricatorEngine.design_memory_storage_molecule(bits=32)
    print(f"Protocol: {memory.protocol_id}")
    print(f"Capacity: {len(memory.instructions)} bits")
    print(f"Success probability: {memory.success_probability:.0%}\n")

    # Test quality control
    print("=== Quality Control Inspection ===")
    measurements = QualityControl.scan_structure(protein)
    print(f"Atoms found: {measurements['atoms_found']}")
    print(f"Defects detected: {measurements['defects_detected']}")
    print(f"Defect rate: {measurements['defect_rate']:.1%}")
    print(f"Structural integrity: {measurements['structural_integrity']:.0%}\n")

    quality_score = QualityControl.compute_success_metric(measurements)
    print(f"Overall quality score: {quality_score:.2%}")

    if measurements['defects_detected'] > 0:
        repair = QualityControl.propose_repair(measurements, protein)
        print(f"Repair protocol designed: {repair.protocol_id}")
        print(f"Repair steps: {len(repair.instructions)}")
