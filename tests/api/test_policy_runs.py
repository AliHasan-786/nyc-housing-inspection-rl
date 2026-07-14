from datetime import datetime
from pathlib import Path

import polars as pl
from fastapi.testclient import TestClient

from nyc_housing_rl.api.app import create_app


def _write_silver(data_root: Path) -> None:
    destination = data_root / "silver" / "2026-01-02"
    destination.mkdir(parents=True)
    pl.DataFrame(
        {
            "unique_key": ["one", "two"],
            "created_date": [datetime(2026, 1, 2, 23), datetime(2026, 1, 3, 12)],
            "bbl": ["1000000001", "1000000001"],
            "permit_overlap": [False, True],
            "borough": ["MANHATTAN", "MANHATTAN"],
            "outcome_label": ["actionable", "no_action"],
        }
    ).write_parquet(destination / "ahv_complaints.parquet")


def test_policy_run_returns_counterfactual_metrics_and_artifacts(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    artifact_root = tmp_path / "artifacts"
    _write_silver(data_root)
    client = TestClient(create_app(data_root=data_root, artifact_root=artifact_root))

    response = client.post(
        "/v1/policy-runs",
        json={
            "snapshotDate": "2026-01-02",
            "dailyCapacity": 1,
            "accessProbability": 1.0,
            "safetyPriority": 0.65,
            "policy": "safety_floor",
            "seed": 7,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["isCounterfactual"] is True
    assert payload["policy"] == "safety_floor"
    assert len(payload["limitations"]) == 4
    artifact = artifact_root / "policy-runs" / "2026-01-02" / payload["artifactId"]
    assert (artifact / "manifest.json").exists()
    assert (artifact / "metrics.json").exists()
    assert (artifact / "decisions.parquet").exists()
    assert (artifact / "outcomes.parquet").exists()


def test_policy_run_rejects_unbounded_request(tmp_path: Path) -> None:
    client = TestClient(create_app(data_root=tmp_path, artifact_root=tmp_path / "artifacts"))
    response = client.post(
        "/v1/policy-runs",
        json={
            "snapshotDate": "2026-01-02",
            "dailyCapacity": 0,
            "accessProbability": 1.1,
            "safetyPriority": 0.1,
            "policy": "safety_floor",
            "seed": -1,
        },
    )
    assert response.status_code == 422
