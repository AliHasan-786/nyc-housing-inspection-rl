"""Scenario orchestration shared by the HTTP service and reproducibility CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nyc_housing_rl.api.schemas import PolicyName, PolicyRunRequest
from nyc_housing_rl.evaluation.artifacts import policy_run_id, write_policy_run_artifact
from nyc_housing_rl.evaluation.runner import Policy, run_policy
from nyc_housing_rl.policies.baselines import (
    AlwaysExpedite,
    Fifo,
    NeverInspect,
    RandomPolicy,
    RiskTier,
    SafetyFloor,
)
from nyc_housing_rl.simulation.environment import InspectionTriageEnv
from nyc_housing_rl.simulation.scenarios import complaints_from_silver
from nyc_housing_rl.simulation.types import SimulationConfig


def run_scenario(
    request: PolicyRunRequest, *, data_root: Path, artifact_root: Path
) -> tuple[str, dict[str, Any]]:
    """Run one data-versioned policy and persist the inspectable result."""

    silver_path = (
        data_root / "silver" / request.snapshot_date.isoformat() / "ahv_complaints.parquet"
    )
    if not silver_path.exists():
        message = f"No silver AHV cohort exists for snapshot {request.snapshot_date.isoformat()}"
        raise FileNotFoundError(message)
    env = InspectionTriageEnv(
        complaints_from_silver(silver_path),
        SimulationConfig(
            daily_capacity=request.daily_capacity,
            access_probability=request.access_probability,
        ),
    )
    result = run_policy(
        env,
        _policy_from_request(request.policy, request.seed, request.safety_priority),
        seed=request.seed,
    )
    artifact_id = policy_run_id(
        snapshot_date=request.snapshot_date,
        daily_capacity=request.daily_capacity,
        access_probability=request.access_probability,
        safety_priority=request.safety_priority,
        policy=request.policy,
        seed=request.seed,
    )
    write_policy_run_artifact(
        result=result,
        artifact_root=artifact_root,
        artifact_id=artifact_id,
        snapshot_date=request.snapshot_date,
        safety_priority=request.safety_priority,
    )
    return artifact_id, result


def _policy_from_request(name: PolicyName, seed: int, safety_priority: float) -> Policy:
    policies: dict[str, Policy] = {
        "fifo_routine": Fifo(),
        "always_expedite": AlwaysExpedite(),
        "never_inspect": NeverInspect(),
        "random": RandomPolicy(seed=seed),
        "risk_tier": RiskTier(),
        "safety_floor": SafetyFloor(expedite_threshold=0.8 - 0.5 * safety_priority),
    }
    return policies[name]
