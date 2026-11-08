import hashlib
import importlib.util
import json
from pathlib import Path

import polars as pl
import pytest

_SCRIPT = Path(__file__).parents[2] / "scripts" / "export_benchmark_explorer.py"
_SPEC = importlib.util.spec_from_file_location("benchmark_explorer", _SCRIPT)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
export_bundle = _MODULE.export_bundle


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    artifact = tmp_path / "artifact"
    artifact.mkdir(parents=True)
    config = tmp_path / "config.json"
    config.write_text("{}\n")
    source = tmp_path / "repo" / "src" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n")
    decisions = pl.DataFrame(
        {
            "run_id": ["run", "run"],
            "policy": ["fifo_routine", "fifo_routine"],
            "daily_capacity": [1, 1],
            "access_probability": [1.0, 1.0],
            "complaint_id": ["private-a", "private-b"],
            "day": [1, 1],
            "action": ["routine", "defer"],
        }
    )
    outcomes = pl.DataFrame(
        {
            "run_id": ["run"],
            "policy": ["fifo_routine"],
            "daily_capacity": [1],
            "access_probability": [1.0],
            "complaint_id": ["private-a"],
            "arrival_day": [1],
            "inspection_day": [1],
            "delay_days": [0],
            "outcome": ["no_action"],
            "equity_group": ["borough:PRIVATE"],
        }
    )
    runs = pl.DataFrame(
        {
            "run_id": ["run"],
            "policy": ["fifo_routine"],
            "seed": [7],
            "daily_capacity": [1],
            "access_probability": [1.0],
            "actionable_found": [0],
            "actionable_missed": [1],
            "actionable_deferred": [1],
            "actionable_inaccessible": [0],
            "actionable_queued_unserved": [0],
            "actionable_unfound": [1],
            "actionable_mean_delay_days": [None],
            "mean_delay_days": [0.0],
            "max_queue_depth": [1],
            "latent_actionable_total": [1],
            "actionable_accounting": ["{}"],
            "borough_metrics": ["{}"],
        }
    )
    decisions.write_parquet(artifact / "decisions.parquet")
    outcomes.write_parquet(artifact / "outcomes.parquet")
    runs.write_parquet(artifact / "runs.parquet")
    metrics = (
        "actionable_found",
        "actionable_unfound",
        "actionable_deferred",
        "actionable_inaccessible",
        "actionable_queued_unserved",
        "mean_delay_days",
        "max_queue_depth",
    )
    summary = [
        {
            "policy": "fifo_routine",
            "daily_capacity": 1,
            "access_probability": 1.0,
            "metric": metric,
            "mean": 0.0,
            "ci95_low": 0.0,
            "ci95_high": 0.0,
            "n_seeds": 1,
            "n_valid_seeds": 1,
        }
        for metric in metrics
    ]
    (artifact / "summary.json").write_text(json.dumps(summary))
    output_names = ("decisions.parquet", "outcomes.parquet", "runs.parquet", "summary.json")
    manifest = {
        "benchmark": "fixture",
        "schema_version": "temporal-benchmark/v1.1",
        "seeds": [7],
        "limitations": ["fixture"],
        "diagnostics": {
            "train_complaints": 2,
            "evaluation_complaints": 2,
            "evaluation_actionable": 1,
            "repeated_buildings": 0,
        },
        "inputs": {
            "config_sha256": _sha(config),
            "silver_sha256": "fixture",
            "git": {"revision": "fixture", "is_dirty": False, "status_porcelain": []},
            "source_tree": {
                "sha256": hashlib.sha256(
                    b"src/example.py\0" + source.read_bytes() + b"\0"
                ).hexdigest(),
                "files": [
                    {
                        "path": "src/example.py",
                        "bytes": source.stat().st_size,
                        "sha256": _sha(source),
                    }
                ],
            },
        },
        "outputs": {name: _sha(artifact / name) for name in output_names},
    }
    (artifact / "manifest.json").write_text(json.dumps(manifest))
    return artifact, config, source.parents[1]


def test_export_is_deterministic_safe_and_conserves_backlog(tmp_path: Path) -> None:
    artifact, config, repo = _fixture(tmp_path)
    first = tmp_path / "one"
    second = tmp_path / "two"
    bundle = export_bundle(
        artifact_dir=artifact,
        config_path=config,
        repo_root=repo,
        output_dir=first,
        web_manifest=tmp_path / "one.ts",
    )
    export_bundle(
        artifact_dir=artifact,
        config_path=config,
        repo_root=repo,
        output_dir=second,
        web_manifest=tmp_path / "two.ts",
    )

    assert (first / "index.json").read_bytes() == (second / "index.json").read_bytes()
    assert (tmp_path / "one.ts").read_bytes() == (tmp_path / "two.ts").read_bytes()
    assert "private-a" not in (first / "index.json").read_text()
    replay = json.loads((first / "replays" / "run.json").read_text())
    assert replay["daily_event_series"] == [
        {
            "run_id": "run",
            "policy": "fifo_routine",
            "daily_capacity": 1,
            "access_probability": 1.0,
            "event_day": 1,
            "admitted": 1,
            "deferred": 1,
            "inspection_attempts": 1,
            "ending_backlog": 0,
            "intra_day_max_backlog": None,
        }
    ]
    assert bundle["index"]["event_day_semantics"]["intra_day_max_backlog"] is None


def test_export_rejects_tampered_artifact_or_stale_config(tmp_path: Path) -> None:
    artifact, config, repo = _fixture(tmp_path)
    (artifact / "summary.json").write_text("[]")
    with pytest.raises(ValueError, match=r"artifact output summary\.json"):
        export_bundle(
            artifact_dir=artifact,
            config_path=config,
            repo_root=repo,
            output_dir=tmp_path / "out",
            web_manifest=tmp_path / "out.ts",
        )

    artifact, config, repo = _fixture(tmp_path / "stale")
    config.write_text('{"stale": true}\n')
    with pytest.raises(ValueError, match="configuration"):
        export_bundle(
            artifact_dir=artifact,
            config_path=config,
            repo_root=repo,
            output_dir=tmp_path / "out",
            web_manifest=tmp_path / "out.ts",
        )
