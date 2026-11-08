"""Create a compact, public-safe explorer bundle from a verified benchmark artifact.

The output deliberately contains aggregates and event-day counts only. It never copies complaint,
building, address, borough, or restricted-course identifiers into the public web bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

SCHEMA_VERSION = "benchmark-explorer/v1"
PUBLIC_COLUMNS = {
    "run_id",
    "policy",
    "seed",
    "daily_capacity",
    "access_probability",
    "actionable_found",
    "actionable_unfound",
    "actionable_deferred",
    "actionable_inaccessible",
    "actionable_queued_unserved",
    "latent_actionable_total",
    "mean_delay_days",
    "max_queue_depth",
}


def export_bundle(
    *, artifact_dir: Path, config_path: Path, repo_root: Path, output_path: Path
) -> dict[str, Any]:
    """Verify pinned inputs and emit a deterministic aggregate-only JSON bundle."""

    manifest = _read_json(artifact_dir / "manifest.json")
    _verify_manifest_outputs(artifact_dir, manifest)
    _verify_sha256(config_path, manifest["inputs"]["config_sha256"], "configuration")
    _verify_source_tree(repo_root, manifest["inputs"]["source_tree"])

    decisions = pl.read_parquet(artifact_dir / "decisions.parquet")
    outcomes = pl.read_parquet(artifact_dir / "outcomes.parquet")
    runs = pl.read_parquet(artifact_dir / "runs.parquet")
    summary = _read_json(artifact_dir / "summary.json")
    _validate_input_schemas(decisions=decisions, outcomes=outcomes, runs=runs)

    daily = _daily_series(decisions=decisions, outcomes=outcomes)
    _validate_daily_conservation(daily)
    _validate_actionable_partitions(runs)
    bundle = {
        "schema_version": SCHEMA_VERSION,
        "counterfactual": True,
        "provenance": {
            "benchmark": manifest["benchmark"],
            "artifact_schema_version": manifest["schema_version"],
            "config_sha256": manifest["inputs"]["config_sha256"],
            "silver_sha256": manifest["inputs"]["silver_sha256"],
            "source_tree_sha256": manifest["inputs"]["source_tree"]["sha256"],
            "output_sha256": manifest["outputs"],
            "generator": {
                "path": "scripts/export_benchmark_explorer.py",
                "sha256": _sha256(Path(__file__)),
            },
        },
        "scope": {
            "train_complaints": manifest["diagnostics"]["train_complaints"],
            "evaluation_complaints": manifest["diagnostics"]["evaluation_complaints"],
            "evaluation_actionables": manifest["diagnostics"]["evaluation_actionable"],
            "repeated_buildings": manifest["diagnostics"]["repeated_buildings"],
            "declared_seeds": manifest["seeds"],
            "ci_interpretation": "95% bootstrap intervals across declared simulation seeds only.",
            "limitations": manifest["limitations"],
        },
        "scenarios": _scenario_aggregates(
            runs=runs,
            outcomes=outcomes,
            summary=summary,
            evaluation_complaints=int(manifest["diagnostics"]["evaluation_complaints"]),
        ),
        "seed_runs": _seed_runs(runs),
        "daily_event_series": daily,
        "event_day_semantics": {
            "day": "Simulator-relative event day, not a calendar date.",
            "admitted": "Non-deferred decisions recorded on that event day.",
            "inspection_attempts": "Recorded simulated inspection outcomes on that event day.",
            "ending_backlog": "Prior ending backlog + admitted - inspection attempts.",
            "intra_day_max_backlog": None,
            "intra_day_max_note": (
                "Not exported: day-level records have no within-day event order, so an exact "
                "intra-day maximum would be invented."
            ),
        },
    }
    _assert_public_safe(bundle)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return bundle


def _scenario_aggregates(
    *,
    runs: pl.DataFrame,
    outcomes: pl.DataFrame,
    summary: list[dict[str, Any]],
    evaluation_complaints: int,
) -> list[dict[str, Any]]:
    summary_by_key = {
        (item["policy"], item["daily_capacity"], item["access_probability"], item["metric"]): item
        for item in summary
    }
    rows: list[dict[str, Any]] = []
    dimensions = ("policy", "daily_capacity", "access_probability")
    for keys, group in runs.group_by(list(dimensions), maintain_order=True):
        policy, capacity, access = keys
        metrics: dict[str, Any] = {}
        for metric in (
            "actionable_found",
            "actionable_unfound",
            "actionable_deferred",
            "actionable_inaccessible",
            "actionable_queued_unserved",
            "mean_delay_days",
            "max_queue_depth",
        ):
            item = summary_by_key[(policy, capacity, access, metric)]
            metrics[metric] = _interval(item)
        run_ids = group.get_column("run_id").to_list()
        attempts = [float(outcomes.filter(pl.col("run_id") == run_id).height) for run_id in run_ids]
        metrics["inspection_attempts"] = _values_interval(
            attempts, policy, capacity, access, "attempts"
        )
        metrics["service_rate"] = _values_interval(
            [value / evaluation_complaints for value in attempts],
            policy,
            capacity,
            access,
            "service_rate",
        )
        rows.append(
            {
                "policy": policy,
                "daily_capacity": capacity,
                "access_probability": access,
                "metrics": metrics,
            }
        )
    return sorted(
        rows, key=lambda item: (item["daily_capacity"], item["access_probability"], item["policy"])
    )


def _seed_runs(runs: pl.DataFrame) -> list[dict[str, Any]]:
    return [
        {column: row[column] for column in sorted(PUBLIC_COLUMNS & set(runs.columns))}
        for row in runs.sort(["daily_capacity", "access_probability", "policy", "seed"]).to_dicts()
    ]


def _daily_series(*, decisions: pl.DataFrame, outcomes: pl.DataFrame) -> list[dict[str, Any]]:
    keys = ["run_id", "policy", "daily_capacity", "access_probability"]
    decision_days = (
        decisions.group_by([*keys, "day"])
        .agg(
            pl.len().alias("decisions"),
            (pl.col("action") == "defer").sum().alias("deferred"),
            (pl.col("action") != "defer").sum().alias("admitted"),
        )
        .rename({"day": "event_day"})
    )
    outcome_days = (
        outcomes.group_by([*keys, "inspection_day"])
        .agg(pl.len().alias("inspection_attempts"))
        .rename({"inspection_day": "event_day"})
    )
    events = decision_days.join(
        outcome_days, on=[*keys, "event_day"], how="full", coalesce=True
    ).fill_null(0)
    output: list[dict[str, Any]] = []
    for run_keys, group in events.sort([*keys, "event_day"]).group_by(keys, maintain_order=True):
        backlog = 0
        run_id, policy, capacity, access = run_keys
        for row in group.iter_rows(named=True):
            admitted = int(row["admitted"])
            attempts = int(row["inspection_attempts"])
            backlog = backlog + admitted - attempts
            if backlog < 0:
                raise ValueError("Inspection attempts exceed reconstructed backlog")
            output.append(
                {
                    "run_id": run_id,
                    "policy": policy,
                    "daily_capacity": capacity,
                    "access_probability": access,
                    "event_day": int(row["event_day"]),
                    "admitted": admitted,
                    "deferred": int(row["deferred"]),
                    "inspection_attempts": attempts,
                    "ending_backlog": backlog,
                    "intra_day_max_backlog": None,
                }
            )
    return output


def _validate_daily_conservation(rows: list[dict[str, Any]]) -> None:
    previous: dict[str, int] = {}
    for row in rows:
        prior = previous.get(str(row["run_id"]), 0)
        expected = prior + int(row["admitted"]) - int(row["inspection_attempts"])
        if expected != row["ending_backlog"]:
            raise ValueError("Daily backlog conservation failed")
        previous[str(row["run_id"])] = int(row["ending_backlog"])


def _validate_actionable_partitions(runs: pl.DataFrame) -> None:
    for row in runs.iter_rows(named=True):
        partition = (
            int(row["actionable_found"])
            + int(row["actionable_deferred"])
            + int(row["actionable_inaccessible"])
            + int(row["actionable_queued_unserved"])
        )
        if partition != int(row["latent_actionable_total"]):
            raise ValueError("Actionable partition does not reconcile")
        if int(row["actionable_unfound"]) != partition - int(row["actionable_found"]):
            raise ValueError("Unfound actionable total does not reconcile")


def _interval(item: dict[str, Any]) -> dict[str, Any]:
    return {key: item[key] for key in ("mean", "ci95_low", "ci95_high", "n_seeds", "n_valid_seeds")}


def _values_interval(
    values: list[float], policy: str, capacity: int, access: float, metric: str
) -> dict[str, Any]:
    if not values:
        return {"mean": None, "ci95_low": None, "ci95_high": None, "n_seeds": 0, "n_valid_seeds": 0}
    array = np.array(values, dtype=float)
    seed = int(
        hashlib.sha256(f"{policy}|{capacity}|{access}|{metric}".encode()).hexdigest()[:8], 16
    )
    rng = np.random.default_rng(seed)
    samples = rng.choice(array, size=(2_000, len(array)), replace=True).mean(axis=1)
    return {
        "mean": float(array.mean()),
        "ci95_low": float(np.quantile(samples, 0.025)),
        "ci95_high": float(np.quantile(samples, 0.975)),
        "n_seeds": len(values),
        "n_valid_seeds": len(values),
    }


def _validate_input_schemas(
    *, decisions: pl.DataFrame, outcomes: pl.DataFrame, runs: pl.DataFrame
) -> None:
    required = {
        "decisions": {
            "run_id",
            "policy",
            "daily_capacity",
            "access_probability",
            "complaint_id",
            "day",
            "action",
        },
        "outcomes": {
            "run_id",
            "policy",
            "daily_capacity",
            "access_probability",
            "complaint_id",
            "inspection_day",
        },
        "runs": PUBLIC_COLUMNS | {"actionable_accounting"},
    }
    actual = {
        "decisions": set(decisions.columns),
        "outcomes": set(outcomes.columns),
        "runs": set(runs.columns),
    }
    for name, expected in required.items():
        if not expected <= actual[name]:
            raise ValueError(f"{name} artifact schema is missing required columns")


def _verify_manifest_outputs(artifact_dir: Path, manifest: dict[str, Any]) -> None:
    for filename, expected in manifest["outputs"].items():
        _verify_sha256(artifact_dir / filename, expected, f"artifact output {filename}")


def _verify_source_tree(repo_root: Path, source_tree: dict[str, Any]) -> None:
    digest = hashlib.sha256()
    for item in source_tree["files"]:
        path = repo_root / item["path"]
        contents = path.read_bytes()
        if len(contents) != item["bytes"] or hashlib.sha256(contents).hexdigest() != item["sha256"]:
            raise ValueError(f"source tree does not match artifact provenance: {item['path']}")
        digest.update(item["path"].encode() + b"\0" + contents + b"\0")
    if digest.hexdigest() != source_tree["sha256"]:
        raise ValueError("source-tree aggregate hash does not match artifact provenance")


def _verify_sha256(path: Path, expected: str, label: str) -> None:
    if _sha256(path) != expected:
        raise ValueError(f"{label} SHA256 does not match pinned provenance")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_public_safe(bundle: dict[str, Any]) -> None:
    rendered = json.dumps(bundle, sort_keys=True)
    forbidden = ("complaint_id", "unique_key", "address", "bbl", "borough:")
    if any(token in rendered.lower() for token in forbidden):
        raise ValueError("public bundle contains a forbidden source identifier")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export_bundle(
        artifact_dir=args.artifact_dir,
        config_path=args.config,
        repo_root=args.repo_root,
        output_path=args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
