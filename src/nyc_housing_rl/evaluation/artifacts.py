"""Immutable, inspectable artifacts for a single bounded policy scenario."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

import polars as pl

ARTIFACT_SCHEMA_VERSION = "policy-run/v1"


def policy_run_id(
    *,
    snapshot_date: date,
    daily_capacity: int,
    access_probability: float,
    safety_priority: float,
    policy: str,
    seed: int,
) -> str:
    """Return a stable ID for the exact scenario inputs, never a random run label."""

    payload = {
        "access_probability": access_probability,
        "daily_capacity": daily_capacity,
        "policy": policy,
        "safety_priority": safety_priority,
        "seed": seed,
        "snapshot_date": snapshot_date.isoformat(),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:12]
    return f"{snapshot_date.isoformat()}-{policy}-{digest}"


def write_policy_run_artifact(
    *,
    result: dict[str, Any],
    artifact_root: Path,
    artifact_id: str,
    snapshot_date: date,
    safety_priority: float,
) -> Path:
    """Write aggregate and row-level outputs without embedding source complaint fields."""

    destination = artifact_root / "policy-runs" / snapshot_date.isoformat() / artifact_id
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {
        "artifact_id": artifact_id,
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "snapshot_date": snapshot_date.isoformat(),
        "policy": result["policy"],
        "seed": result["seed"],
        "counterfactual": True,
        "safety_priority": safety_priority,
        "limitations": _limitations(),
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    metrics = {key: value for key, value in result.items() if key not in {"decisions", "outcomes"}}
    (destination / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    pl.DataFrame(result["decisions"]).write_parquet(destination / "decisions.parquet")
    pl.DataFrame(result["outcomes"]).write_parquet(destination / "outcomes.parquet")
    return destination


def _limitations() -> list[str]:
    return [
        (
            "This is a counterfactual queue simulation, not a causal forecast or deployment "
            "recommendation."
        ),
        (
            "Historical outcome labels are revealed only after simulated inspection and do not "
            "establish the effect of triage."
        ),
        "Borough slices are operational groups, not demographic fairness findings.",
        (
            "Any real expedite or defer decision requires accountable human review and an "
            "appeal/correction path."
        ),
    ]
