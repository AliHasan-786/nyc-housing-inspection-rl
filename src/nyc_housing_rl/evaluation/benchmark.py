"""Artifact-backed temporal benchmark for the first learned simulator policies."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, cast

import numpy as np
import polars as pl

from nyc_housing_rl.evaluation.runner import Policy, run_policy
from nyc_housing_rl.evaluation.temporal import temporal_split_from_silver
from nyc_housing_rl.policies.baselines import Fifo, RandomPolicy, RiskTier, SafetyFloor
from nyc_housing_rl.policies.learned import LearningKind, train_tabular_policy
from nyc_housing_rl.simulation.environment import InspectionTriageEnv
from nyc_housing_rl.simulation.types import Complaint, SimulationConfig

POLICY_NAMES = (
    "fifo_routine",
    "random",
    "risk_tier",
    "safety_floor",
    "contextual_bandit",
    "tabular_q_learning",
)
METRICS = (
    "actionable_found",
    "actionable_missed",
    "actionable_mean_delay_days",
    "mean_delay_days",
    "max_queue_depth",
)


@dataclass(frozen=True, slots=True)
class TemporalDiagnostics:
    train_complaints: int
    evaluation_complaints: int
    train_actionable: int
    evaluation_actionable: int
    repeated_buildings: int
    evaluation_buildings_seen_in_train: int


def run_temporal_benchmark(*, config_path: Path, data_root: Path, artifact_root: Path) -> Path:
    """Train/evaluate declared policies and emit checksummed machine-readable artifacts."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    snapshot = str(config["data_snapshot"])
    silver_path = data_root / "silver" / snapshot / "ahv_complaints.parquet"
    train_end = date.fromisoformat(str(config["temporal_split"]["train_end"]))
    train, evaluation = temporal_split_from_silver(silver_path, train_end=train_end)
    diagnostics = _diagnostics(silver_path, train_end=train_end, train=train, evaluation=evaluation)
    output = artifact_root / "benchmarks" / str(config["name"])
    output.mkdir(parents=True, exist_ok=True)

    run_rows: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    outcomes: list[dict[str, Any]] = []
    trained_policies: list[dict[str, Any]] = []
    for capacity in config["simulation"]["daily_capacity"]:
        for access_probability in config["simulation"]["access_probability"]:
            scenario = {
                "daily_capacity": int(capacity),
                "access_probability": float(access_probability),
            }
            for seed in config["seeds"]:
                for policy_name in config["policies"]:
                    result, trained_policy = _evaluate_policy(
                        policy_name=str(policy_name),
                        train=train,
                        evaluation=evaluation,
                        seed=int(seed),
                        scenario=scenario,
                        max_drain_days=int(config["simulation"]["max_drain_days"]),
                        training=dict(config["training"]),
                    )
                    run_id = _run_id(policy=str(policy_name), seed=int(seed), scenario=scenario)
                    if trained_policy is not None:
                        trained_policies.append({"run_id": run_id, **trained_policy})
                    run_rows.append(_metrics_row(run_id=run_id, result=result, scenario=scenario))
                    decisions.extend(
                        {"run_id": run_id, "policy": policy_name, **scenario, **row}
                        for row in result["decisions"]
                    )
                    outcomes.extend(
                        {"run_id": run_id, "policy": policy_name, **scenario, **row}
                        for row in result["outcomes"]
                    )

    runs_path = output / "runs.parquet"
    decisions_path = output / "decisions.parquet"
    outcomes_path = output / "outcomes.parquet"
    trained_policies_path = output / "trained-policies.json"
    pl.DataFrame(run_rows).write_parquet(runs_path)
    pl.DataFrame(decisions).write_parquet(decisions_path)
    pl.DataFrame(outcomes).write_parquet(outcomes_path)
    summary = _summarize(run_rows, seeds=list(config["seeds"]))
    geography = _summarize_geography(run_rows, seeds=list(config["seeds"]))
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (output / "operational-geography.json").write_text(
        json.dumps(geography, indent=2, sort_keys=True) + "\n"
    )
    trained_policies_path.write_text(
        json.dumps(trained_policies, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    table_path = output / "summary.md"
    table_path.write_text(_markdown_table(summary), encoding="utf-8")
    manifest = {
        "schema_version": "temporal-benchmark/v1",
        "benchmark": config["name"],
        "counterfactual": True,
        "data_snapshot": snapshot,
        "temporal_split": config["temporal_split"],
        "seeds": config["seeds"],
        "policy_names": config["policies"],
        "scenario_grid": config["simulation"],
        "uncertainty": config["uncertainty"],
        "operational_geography_boundary": config["equity_boundary"],
        "diagnostics": asdict(diagnostics),
        "inputs": {
            "config_sha256": _sha256(config_path),
            "silver_sha256": _sha256(silver_path),
            "code_revision": _git_revision(),
            "implementation_sha256": _implementation_hash(),
        },
        "outputs": {
            path.name: _sha256(path)
            for path in (
                runs_path,
                decisions_path,
                outcomes_path,
                trained_policies_path,
                output / "summary.json",
                output / "operational-geography.json",
                table_path,
            )
        },
        "limitations": [
            "Simulator outcomes are counterfactual and do not establish causal dispatch effects.",
            (
                "The 782-record AHV cohort contains only 16 administrative actionable labels; "
                "this is a small simulator-policy study, not a predictive-performance headline."
            ),
            (
                "Borough slices are operational geography metrics, not demographic fairness "
                "measures or proxies."
            ),
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return output


def _evaluate_policy(
    *,
    policy_name: str,
    train: list[Complaint],
    evaluation: list[Complaint],
    seed: int,
    scenario: dict[str, float | int],
    max_drain_days: int,
    training: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    config = SimulationConfig(
        daily_capacity=int(scenario["daily_capacity"]),
        access_probability=float(scenario["access_probability"]),
        max_drain_days=max_drain_days,
    )
    policy: Policy
    trained_policy: dict[str, Any] | None = None
    if policy_name in {"contextual_bandit", "tabular_q_learning"}:
        learned = train_tabular_policy(
            InspectionTriageEnv(train, config),
            kind=cast(LearningKind, policy_name),
            seed=seed,
            **training,
        )
        policy = learned
        values = {
            ",".join(map(str, state)): [float(value) for value in action_values]
            for state, action_values in sorted(learned.q_values.items())
        }
        encoded = json.dumps(values, sort_keys=True).encode()
        trained_policy = {
            "policy": policy_name,
            "seed": seed,
            **scenario,
            "training": training,
            "state_count": len(values),
            "values_sha256": hashlib.sha256(encoded).hexdigest(),
            "values": values,
        }
    else:
        policy = _baseline_policy(policy_name, seed=seed)
    return run_policy(InspectionTriageEnv(evaluation, config), policy, seed=seed), trained_policy


def _baseline_policy(name: str, *, seed: int) -> Policy:
    policies: dict[str, Policy] = {
        "fifo_routine": Fifo(),
        "random": RandomPolicy(seed=seed),
        "risk_tier": RiskTier(),
        "safety_floor": SafetyFloor(),
    }
    return policies[name]


def _metrics_row(
    *, run_id: str, result: dict[str, Any], scenario: dict[str, float | int]
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "policy": result["policy"],
        "seed": result["seed"],
        **scenario,
        **{metric: result[metric] for metric in METRICS},
        "borough_metrics": json.dumps(result["group_metrics"], sort_keys=True),
    }


def _summarize(rows: list[dict[str, Any]], *, seeds: list[int]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for policy in POLICY_NAMES:
        for capacity in sorted({int(row["daily_capacity"]) for row in rows}):
            for access in sorted({float(row["access_probability"]) for row in rows}):
                selected = [
                    row
                    for row in rows
                    if row["policy"] == policy
                    and row["daily_capacity"] == capacity
                    and row["access_probability"] == access
                ]
                if not selected:
                    continue
                for metric in METRICS:
                    values = np.array([float(row[metric]) for row in selected])
                    low, high = _bootstrap_interval(
                        values, seed=_summary_seed(policy, metric, capacity, access)
                    )
                    summaries.append(
                        {
                            "policy": policy,
                            "daily_capacity": capacity,
                            "access_probability": access,
                            "metric": metric,
                            "mean": float(values.mean()),
                            "ci95_low": low,
                            "ci95_high": high,
                            "n_seeds": len(values),
                            "declared_seeds": seeds,
                        }
                    )
    return summaries


def _summarize_geography(rows: list[dict[str, Any]], *, seeds: list[int]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for row in rows:
        metrics = json.loads(str(row["borough_metrics"]))
        for borough, values in metrics.items():
            summaries.append(
                {
                    "policy": row["policy"],
                    "daily_capacity": row["daily_capacity"],
                    "access_probability": row["access_probability"],
                    "seed": row["seed"],
                    "borough": borough,
                    "service_rate": values["service_rate"],
                    "mean_delay_days": values["mean_delay_days"],
                }
            )
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in summaries:
        key = tuple(
            row[field] for field in ("policy", "daily_capacity", "access_probability", "borough")
        )
        grouped.setdefault(key, []).append(row)
    output: list[dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        for metric in ("service_rate", "mean_delay_days"):
            values = np.array([float(row[metric]) for row in group])
            low, high = _bootstrap_interval(values, seed=_summary_seed(*key, metric))
            output.append(
                {
                    "policy": key[0],
                    "daily_capacity": key[1],
                    "access_probability": key[2],
                    "borough": key[3],
                    "metric": metric,
                    "mean": float(values.mean()),
                    "ci95_low": low,
                    "ci95_high": high,
                    "n_seeds": len(values),
                    "declared_seeds": seeds,
                    "interpretation": (
                        "Operational geography only; not a demographic fairness measure or proxy."
                    ),
                }
            )
    return output


def _bootstrap_interval(
    values: np.ndarray, *, seed: int, resamples: int = 2_000
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(resamples, len(values)), replace=True).mean(axis=1)
    return float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def _diagnostics(
    silver_path: Path, *, train_end: date, train: list[Complaint], evaluation: list[Complaint]
) -> TemporalDiagnostics:
    frame = pl.read_parquet(silver_path).with_columns(pl.col("created_date").dt.date().alias("day"))
    train_bbls = set(
        frame.filter(pl.col("day") <= train_end).get_column("bbl").drop_nulls().cast(pl.String)
    )
    evaluation_bbls = set(
        frame.filter(pl.col("day") > train_end).get_column("bbl").drop_nulls().cast(pl.String)
    )
    return TemporalDiagnostics(
        train_complaints=len(train),
        evaluation_complaints=len(evaluation),
        train_actionable=sum(item.latent_outcome.value == "actionable" for item in train),
        evaluation_actionable=sum(item.latent_outcome.value == "actionable" for item in evaluation),
        repeated_buildings=len(train_bbls & evaluation_bbls),
        evaluation_buildings_seen_in_train=len(train_bbls & evaluation_bbls),
    )


def _run_id(*, policy: str, seed: int, scenario: dict[str, float | int]) -> str:
    payload = json.dumps({"policy": policy, "seed": seed, **scenario}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _summary_seed(*parts: object) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_revision() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def _implementation_hash() -> str:
    root = Path(__file__).parents[3]
    files = (
        root / "src/nyc_housing_rl/evaluation/benchmark.py",
        root / "src/nyc_housing_rl/evaluation/temporal.py",
        root / "src/nyc_housing_rl/policies/learned.py",
        root / "src/nyc_housing_rl/simulation/environment.py",
    )
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _markdown_table(summary: list[dict[str, Any]]) -> str:
    rows = [
        "# Temporal benchmark summary (counterfactual simulator)",
        "",
        (
            "This table is generated from `summary.json`. It is not a causal or demographic "
            "fairness claim."
        ),
        "",
        (
            "| Capacity | Access | Policy | Actionables found, mean [95% CI] | "
            "Actionables missed, mean [95% CI] |"
        ),
        "| ---: | ---: | --- | --- | --- |",
    ]
    grouped: dict[tuple[int, float, str], dict[str, dict[str, Any]]] = {}
    for item in summary:
        key = (
            int(item["daily_capacity"]),
            float(item["access_probability"]),
            str(item["policy"]),
        )
        grouped.setdefault(key, {})[str(item["metric"])] = item
    for key, metrics in sorted(grouped.items()):
        found = metrics["actionable_found"]
        missed = metrics["actionable_missed"]
        rows.append(
            f"| {key[0]} | {key[1]:.1f} | {key[2]} | "
            f"{found['mean']:.2f} [{found['ci95_low']:.2f}, {found['ci95_high']:.2f}] | "
            f"{missed['mean']:.2f} [{missed['ci95_low']:.2f}, {missed['ci95_high']:.2f}] |"
        )
    return "\n".join(rows) + "\n"
