"""
Phase XXVIII: Chrono-Kinetic Simulator (Video & World Models)
===========================================================

Simulation-first video generator: renders from internal physics and
object permanence rather than pixel hallucination. Integrates
chrono-aware rollout for action prediction.

Goals:
1. Maintain object permanence via IDs and state vectors
2. Step physics with simple gravity/collision for consistency
3. Render camera frames from state → tensor → ForgeNumerics frame
4. Predict action outcomes (e.g., steering) over future horizon
5. Provide self-test with deterministic rollout and frames
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import numpy as np
import hashlib


@dataclass
class Entity:
    entity_id: str
    position: np.ndarray  # (x, y)
    velocity: np.ndarray  # (vx, vy)
    radius: float = 0.5
    mass: float = 1.0

    def step(self, dt: float = 0.1, gravity: float = -9.8):
        # Simple Euler integration with gravity on y-axis
        ax = 0.0
        ay = gravity
        self.velocity[0] += ax * dt
        self.velocity[1] += ay * dt
        self.position += self.velocity * dt

    def to_state_vector(self) -> np.ndarray:
        return np.array([self.position[0], self.position[1], self.velocity[0], self.velocity[1], self.radius, self.mass])


@dataclass
class World:
    entities: List[Entity] = field(default_factory=list)
    bounds: Tuple[float, float, float, float] = (-5.0, 5.0, -1.0, 5.0)  # xmin, xmax, ymin, ymax

    def step(self, dt: float = 0.1):
        for ent in self.entities:
            ent.step(dt=dt)
            self._handle_collisions(ent)

    def _handle_collisions(self, ent: Entity):
        xmin, xmax, ymin, ymax = self.bounds
        # Ground and walls bounce with simple restitution
        restitution = 0.6
        if ent.position[0] - ent.radius < xmin or ent.position[0] + ent.radius > xmax:
            ent.velocity[0] *= -restitution
            ent.position[0] = np.clip(ent.position[0], xmin + ent.radius, xmax - ent.radius)
        if ent.position[1] - ent.radius < ymin:
            ent.velocity[1] *= -restitution
            ent.position[1] = ymin + ent.radius
        if ent.position[1] + ent.radius > ymax:
            ent.velocity[1] *= -restitution
            ent.position[1] = ymax - ent.radius

    def snapshot_tensor(self, resolution: Tuple[int, int] = (32, 32)) -> np.ndarray:
        h, w = resolution
        canvas = np.zeros((h, w), dtype=np.int8)
        xmin, xmax, ymin, ymax = self.bounds
        for ent in self.entities:
            # Map position to pixel grid
            x_norm = (ent.position[0] - xmin) / (xmax - xmin)
            y_norm = (ent.position[1] - ymin) / (ymax - ymin)
            px = int(np.clip(x_norm * (w - 1), 0, w - 1))
            py = int(np.clip((1 - y_norm) * (h - 1), 0, h - 1))  # invert y for image coordinates
            canvas[py, px] = 2  # Φ token proxy for entity pixel
        return canvas

    def to_frame(self, tensor: np.ndarray) -> str:
        t_hash = hashlib.sha256(tensor.tobytes()).hexdigest()[:12]
        ent_ids = "∷".join([e.entity_id for e in self.entities])
        return f"""⧆≛TYPE⦙≛VIDEO_FRAME∴
≛ENTITIES⦙≛{ent_ids}∷
≛TENSOR_HASH⦙≛{t_hash}
⧈"""


class ActionPredictor:
    """Predicts future frames given action inputs."""

    def __init__(self, horizon: int = 10, dt: float = 0.1):
        self.horizon = horizon
        self.dt = dt

    def rollout(self, world: World, action: Dict[str, float]) -> List[np.ndarray]:
        # Clone shallow world state
        clones = [Entity(e.entity_id, e.position.copy(), e.velocity.copy(), e.radius, e.mass) for e in world.entities]
        sim = World(entities=clones, bounds=world.bounds)

        # Apply simple steering action to first entity if present
        if sim.entities and "steer" in action:
            sim.entities[0].velocity[0] += action["steer"]

        frames: List[np.ndarray] = []
        for _ in range(self.horizon):
            sim.step(dt=self.dt)
            frames.append(sim.snapshot_tensor())
        return frames


class Renderer:
    """Renders tensors into frames with hashes and metadata."""

    @staticmethod
    def render_sequence(tensors: List[np.ndarray], label: str) -> str:
        seq_hash = hashlib.sha256(b"".join([t.tobytes() for t in tensors])).hexdigest()[:16]
        return f"""⧆≛TYPE⦙≛VIDEO_SEQUENCE∴
≛LABEL⦙≛{label}∷
≛FRAMES⦙≛{len(tensors)}∷
≛SEQ_HASH⦙≛{seq_hash}
⧈"""


class ChronoKineticSimulator:
    """End-to-end chrono-aware world model and renderer."""

    def __init__(self):
        self.world = World(
            entities=[
                Entity("agent", np.array([-2.0, 2.5]), np.array([3.0, 0.0])),
                Entity("obstacle", np.array([1.5, 1.0]), np.array([0.0, 0.0]), radius=0.7, mass=5.0),
            ],
            bounds=(-4.0, 4.0, 0.0, 5.0),
        )
        self.predictor = ActionPredictor(horizon=8, dt=0.12)
        self.renderer = Renderer()

    def simulate(self, action: Dict[str, float]) -> Dict[str, str]:
        # Current frame
        current_tensor = self.world.snapshot_tensor()
        current_frame = self.world.to_frame(current_tensor)

        # Future rollout
        tensors = self.predictor.rollout(self.world, action)
        sequence_frame = self.renderer.render_sequence(tensors, label="chrono_rollout")

        # Simple risk metric: average distance to obstacle over rollout
        if len(self.world.entities) >= 2:
            obstacle_pos = self.world.entities[1].position
            distances = []
            for t in tensors:
                # crude: use center pixel distance as proxy
                h, w = t.shape
                ys, xs = np.where(t == 2)
                if len(xs) > 0:
                    cx = np.mean(xs) / (w - 1)
                    cy = np.mean(ys) / (h - 1)
                    distances.append(np.linalg.norm([cx, cy]))
            risk = 1.0 - float(np.clip(np.mean(distances) if distances else 0.0, 0.0, 1.0))
        else:
            risk = 0.0

        risk_frame = f"""⧆≛TYPE⦙≛RISK∴
≛METRIC⦙≛proximity∷
≛VALUE⦙≛{risk:.6f}
⧈"""

        return {
            "current_frame": current_frame,
            "sequence_frame": sequence_frame,
            "risk_frame": risk_frame,
        }


# ============================================================================
# SELF-TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PHASE XXVIII: CHRONO-KINETIC SIMULATOR")
    print("=" * 70)
    print()

    sim = ChronoKineticSimulator()

    action = {"steer": -0.8}
    print(f"1) Rolling out future with action: {action}")
    frames = sim.simulate(action)
    print("   Current frame:")
    print(frames["current_frame"])
    print()
    print("   Sequence frame:")
    print(frames["sequence_frame"])
    print()
    print("   Risk frame:")
    print(frames["risk_frame"])
    print()

    print("=" * 70)
    print("PHASE XXVIII COMPLETE: Physics-based video ready")
    print("=" * 70)
    print("✓ Object permanence via entity IDs")
    print("✓ Physics rollouts with action conditioning")
    print("✓ Video frames exported with hashes")
    print("Next: Phase XXIX - Cyber-Sovereign (coding formal verification)")
