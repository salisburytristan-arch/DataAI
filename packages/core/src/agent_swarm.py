"""
Phase XXXI: Agent Swarm (Autonomous Cooperation)
================================================

Implements a hive protocol with task frames, drone execution, and
consensus voting. Provides deterministic simulation for debugging
and exports TASK, RESULT, and SWARM_SUMMARY frames.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple
import hashlib
import random
import math


PRIORITY_WEIGHT = {"CRITICAL": 1.2, "HIGH": 1.0, "MED": 0.8, "LOW": 0.6}


def _hash(obj: Any) -> str:
    return hashlib.sha256(repr(obj).encode()).hexdigest()[:12]


def _clamp(val: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, val))


def _confidence(seed: str, base: float = 0.65) -> float:
    r = random.Random(int(hashlib.sha256(seed.encode()).hexdigest(), 16))
    return _clamp(base + (r.random() - 0.5) * 0.3)


@dataclass
class TaskFrame:
    action: str
    priority: str
    payload: Dict[str, Any]
    task_id: str = field(default_factory=lambda: _hash("task"))

    def to_frame(self) -> str:
        payload_hash = _hash(self.payload)
        return f"""⧆≛TYPE⦙≛TASK∴
≛ID⦙≛{self.task_id}∷
≛PRIORITY⦙≛{self.priority}∷
≛ACTION⦙≛{self.action}∷
≛PAYLOAD_HASH⦙≛{payload_hash}
⧈"""


@dataclass
class DroneAgent:
    name: str
    specialization: str
    skill: float = 0.7

    def execute(self, task: TaskFrame) -> Dict[str, Any]:
        seed = f"{self.name}:{task.action}:{task.task_id}"
        r = random.Random(int(hashlib.sha256(seed.encode()).hexdigest(), 16))
        base = _clamp(self.skill + (r.random() - 0.5) * 0.2)
        difficulty = 0.2 if task.priority in ("CRITICAL", "HIGH") else 0.1
        success_prob = _clamp(base - difficulty + (0.1 if self.specialization.lower() in task.action.lower() else 0.0))
        success = r.random() < success_prob
        confidence = _clamp(success_prob + (r.random() - 0.5) * 0.1)
        return {
            "drone": self.name,
            "specialization": self.specialization,
            "success": success,
            "confidence": confidence,
            "log": f"handled:{task.action}:p={success_prob:.2f}"
        }

    def result_frame(self, task: TaskFrame, result: Dict[str, Any]) -> str:
        status = "PASS" if result["success"] else "FAIL"
        return f"""⧆≛TYPE⦙≛TASK_RESULT∴
≛TASK_ID⦙≛{task.task_id}∷
≛DRONE⦙≛{self.name}∷
≛STATUS⦙≛{status}∷
≛CONF⦙≛{result['confidence']:.3f}∷
≛LOG⦙≛{result['log']}
⧈"""


class HiveCoordinator:
    def __init__(self, drones: List[DroneAgent]):
        self.drones = drones

    def _select_team(self, task: TaskFrame, k: int = 3) -> List[DroneAgent]:
        scored: List[Tuple[float, DroneAgent]] = []
        for d in self.drones:
            spec_bonus = 0.2 if d.specialization.lower() in task.action.lower() else 0.0
            weight = PRIORITY_WEIGHT.get(task.priority, 0.8)
            score = weight * (d.skill + spec_bonus)
            scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:k]]

    def execute_task(self, task: TaskFrame) -> Dict[str, Any]:
        team = self._select_team(task)
        drone_results = []
        votes = []
        for drone in team:
            result = drone.execute(task)
            drone_results.append(drone.result_frame(task, result))
            votes.append(result["confidence"] * (1 if result["success"] else -0.5))
        consensus = sum(votes) / len(votes) if votes else 0.0
        final_status = "PASS" if consensus > 0 else "FAIL"
        summary_frame = f"""⧆≛TYPE⦙≛SWARM_SUMMARY∴
≛TASK_ID⦙≛{task.task_id}∷
≛TEAM⦙≛{"∷".join([d.name for d in team])}∷
≛CONSENSUS⦙≛{consensus:.3f}∷
≛FINAL⦙≛{final_status}
⧈"""
        return {
            "task_frame": task.to_frame(),
            "drone_frames": drone_results,
            "summary_frame": summary_frame,
        }


# ============================================================================
# SELF-TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PHASE XXXI: AGENT SWARM - AUTONOMOUS COOPERATION")
    print("=" * 70)
    print()

    drones = [
        DroneAgent(name="alpha", specialization="code", skill=0.78),
        DroneAgent(name="beta", specialization="research", skill=0.74),
        DroneAgent(name="gamma", specialization="ops", skill=0.70),
        DroneAgent(name="delta", specialization="vision", skill=0.72),
    ]

    hive = HiveCoordinator(drones)
    task = TaskFrame(action="debug_code_path", priority="HIGH", payload={"file": "core.py", "line": 128})

    print("1) Emitting task frame:")
    result = hive.execute_task(task)
    print(result["task_frame"])
    print()

    print("2) Drone results:")
    for frame in result["drone_frames"]:
        print(frame)
        print()

    print("3) Swarm summary:")
    print(result["summary_frame"])
    print()

    print("=" * 70)
    print("PHASE XXXI COMPLETE: Agent swarm online")
    print("=" * 70)
    print("✓ TASK frame produced")
    print("✓ Drone execution + votes")
    print("✓ Consensus summary exported")
    print("Next: Phase XXXII - Deployment (ubiquitous presence)")
