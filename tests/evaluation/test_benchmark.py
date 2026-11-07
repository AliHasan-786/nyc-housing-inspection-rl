import json
from datetime import datetime
from pathlib import Path

import polars as pl

from nyc_housing_rl.evaluation.benchmark import run_temporal_benchmark


def _write_silver(data_root: Path) -> None:
    destination = data_root / "silver" / "2026-01-04"
    destination.mkdir(parents=True)
    pl.DataFrame(
        {
            "unique_key": ["one", "two", "three", "four"],
            "created_date": [
                datetime(2026, 1, 1, 23),
                datetime(2026, 1, 2, 12),
                datetime(2026, 1, 3, 23),
                datetime(2026, 1, 4, 12),
            ],
            "bbl": ["1000000001", "1000000001", "1000000001", "2000000001"],
            "permit_overlap": [False, True, False, False],
            "borough": ["MANHATTAN", "MANHATTAN", "MANHATTAN", "BRONX"],
            "outcome_label": ["actionable", "no_action", "actionable", "no_action"],
        }
    ).write_parquet(destination / "ahv_complaints.parquet")


def test_benchmark_writes_checksums_rows_and_temporal_diagnostics(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    _write_silver(data_root)
    config = {
        "name": "fixture",
        "data_snapshot": "2026-01-04",
        "temporal_split": {"train_end": "2026-01-02"},
        "seeds": [3, 5],
        "training": {"episodes": 4, "learning_rate": 0.15, "gamma": 0.95, "epsilon": 0.15},
        "simulation": {"daily_capacity": [1], "access_probability": [1.0], "max_drain_days": 3},
        "policies": ["fifo_routine", "contextual_bandit"],
        "uncertainty": "fixture",
        "equity_boundary": "operational only",
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    output = run_temporal_benchmark(
        config_path=config_path, data_root=data_root, artifact_root=tmp_path / "artifacts"
    )

    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["diagnostics"]["train_complaints"] == 2
    assert manifest["diagnostics"]["evaluation_complaints"] == 2
    assert manifest["diagnostics"]["repeated_buildings"] == 1
    assert set(manifest["outputs"]) == {
        "runs.parquet",
        "decisions.parquet",
        "outcomes.parquet",
        "summary.json",
        "operational-geography.json",
        "trained-policies.json",
        "summary.md",
    }
    runs = pl.read_parquet(output / "runs.parquet")
    assert runs.height == 4
    assert set(runs["policy"].to_list()) == {"fifo_routine", "contextual_bandit"}
    trained = json.loads((output / "trained-policies.json").read_text())
    assert len(trained) == 2
    assert all(item["values_sha256"] for item in trained)
