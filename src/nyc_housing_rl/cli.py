"""Command-line entry point for reproducible data snapshots and builds."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable
from datetime import date
from pathlib import Path

from nyc_housing_rl.api.schemas import PolicyRunRequest
from nyc_housing_rl.api.service import run_scenario
from nyc_housing_rl.data.bronze import build_bronze
from nyc_housing_rl.data.client import SocrataClient
from nyc_housing_rl.data.lineage import build_lineage_manifest
from nyc_housing_rl.data.profile import build_profile
from nyc_housing_rl.data.silver import build_silver
from nyc_housing_rl.data.snapshot import (
    read_snapshot_rows,
    snapshot_directory,
    verify_snapshot,
    write_snapshot,
)
from nyc_housing_rl.data.sources import AHV_311, AHV_PERMITS, DATASETS

DEFAULT_DATA_ROOT = Path("data")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="civic-inspection")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser("fetch", help="write immutable NYC Open Data snapshots")
    fetch.add_argument("--snapshot-date", type=date.fromisoformat, default=date.today())
    fetch.add_argument("--source", choices=["all", *DATASETS], default="all")
    fetch.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    fetch.add_argument("--page-size", type=int, default=50_000)
    fetch.add_argument("--force", action="store_true")

    verify = subparsers.add_parser("verify", help="verify snapshot checksums and row counts")
    verify.add_argument("--snapshot-date", type=date.fromisoformat, required=True)
    verify.add_argument("--source", choices=["all", *DATASETS], default="all")
    verify.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)

    build = subparsers.add_parser("build", help="validate and build bronze/silver/profile data")
    build.add_argument("--snapshot-date", type=date.fromisoformat, required=True)
    build.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)

    run = subparsers.add_parser("run-policy", help="run and archive one bounded simulator scenario")
    run.add_argument("--snapshot-date", type=date.fromisoformat, required=True)
    run.add_argument(
        "--policy",
        choices=[
            "fifo_routine",
            "always_expedite",
            "never_inspect",
            "random",
            "risk_tier",
            "safety_floor",
        ],
        default="safety_floor",
    )
    run.add_argument("--daily-capacity", type=int, default=2)
    run.add_argument("--access-probability", type=float, default=1.0)
    run.add_argument("--safety-priority", type=float, default=0.65)
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    run.add_argument("--artifact-root", type=Path, default=Path("artifacts"))

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "fetch":
        return _fetch(args)
    if args.command == "verify":
        return _verify(args)
    if args.command == "build":
        return _build(args)
    if args.command == "run-policy":
        return _run_policy(args)
    raise AssertionError("unreachable")


def _fetch(args: argparse.Namespace) -> int:
    raw_root = args.data_root / "raw"
    selected = list(DATASETS) if args.source == "all" else [args.source]
    if "ahv_permits" in selected and "ahv_311" not in selected:
        cohort_directory = snapshot_directory(raw_root, args.snapshot_date, AHV_311.name)
        if not cohort_directory.exists():
            raise FileNotFoundError("Fetch ahv_311 before linked permits")
    with SocrataClient(
        app_token=os.getenv("SOCRATA_APP_TOKEN"), page_size=args.page_size
    ) as client:
        for source_name in selected:
            spec = DATASETS[source_name]
            queries = _permit_queries(raw_root, args.snapshot_date) if spec == AHV_PERMITS else None
            manifest = write_snapshot(
                client=client,
                spec=spec,
                root=raw_root,
                snapshot_date=args.snapshot_date,
                queries=queries,
                force=args.force,
            )
            print(json.dumps({"source": source_name, "rows": manifest.row_count}))
    return 0


def _verify(args: argparse.Namespace) -> int:
    selected = list(DATASETS) if args.source == "all" else [args.source]
    for source_name in selected:
        directory = snapshot_directory(args.data_root / "raw", args.snapshot_date, source_name)
        manifest = verify_snapshot(directory)
        print(json.dumps({"source": source_name, "rows": manifest.row_count, "verified": True}))
    return 0


def _build(args: argparse.Namespace) -> int:
    for source_name in DATASETS:
        path, report = build_bronze(
            source_name=source_name,
            raw_root=args.data_root / "raw",
            bronze_root=args.data_root / "bronze",
            snapshot_date=args.snapshot_date,
        )
        print(json.dumps({"source": source_name, "rows": report.valid_rows, "path": str(path)}))
    silver = build_silver(
        bronze_root=args.data_root / "bronze",
        silver_root=args.data_root / "silver",
        snapshot_date=args.snapshot_date,
    )
    profile_json, profile_markdown = build_profile(
        silver_path=silver,
        output_root=Path("artifacts/data"),
        snapshot_date=args.snapshot_date,
    )
    lineage = build_lineage_manifest(
        data_root=args.data_root,
        artifact_root=Path("artifacts/data"),
        snapshot_date=args.snapshot_date,
    )
    print(
        json.dumps(
            {
                "silver": str(silver),
                "profile": str(profile_json),
                "card": str(profile_markdown),
                "lineage": str(lineage),
            }
        )
    )
    return 0


def _run_policy(args: argparse.Namespace) -> int:
    request = PolicyRunRequest(
        snapshotDate=args.snapshot_date,
        policy=args.policy,
        dailyCapacity=args.daily_capacity,
        accessProbability=args.access_probability,
        safetyPriority=args.safety_priority,
        seed=args.seed,
    )
    artifact_id, result = run_scenario(
        request, data_root=args.data_root, artifact_root=args.artifact_root
    )
    print(
        json.dumps(
            {
                "artifact_id": artifact_id,
                "policy": result["policy"],
                "total_reward": result["total_reward"],
                "inspected": result["inspected"],
                "actionable_found": result["actionable_found"],
            }
        )
    )
    return 0


def _permit_queries(raw_root: Path, snapshot_date: date) -> list[dict[str, str]]:
    cohort_directory = snapshot_directory(raw_root, snapshot_date, AHV_311.name)
    rows = read_snapshot_rows(cohort_directory)
    bbls = sorted({str(row["bbl"]) for row in rows if row.get("bbl")})
    queries: list[dict[str, str]] = []
    for chunk in _chunked(bbls, 40):
        quoted = ",".join(f"'{bbl}'" for bbl in chunk)
        query = AHV_PERMITS.query()
        query["$where"] = f"bbl in ({quoted})"
        queries.append(query)
    return queries or [AHV_PERMITS.query() | {"$where": "1 = 0"}]


def _chunked(values: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


if __name__ == "__main__":
    raise SystemExit(main())
