"""Checksummed lineage manifest for a complete data build."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import polars as pl

from nyc_housing_rl.data.snapshot import load_manifest
from nyc_housing_rl.data.sources import DATASETS


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_lineage_manifest(
    *,
    data_root: Path,
    artifact_root: Path,
    snapshot_date: date,
) -> Path:
    stamp = snapshot_date.isoformat()
    raw_sources: dict[str, Any] = {}
    for source_name in DATASETS:
        manifest_path = data_root / "raw" / stamp / source_name / "manifest.json"
        manifest = load_manifest(manifest_path)
        raw_sources[source_name] = {
            "dataset_id": manifest.dataset_id,
            "source_url": manifest.source_url,
            "row_count": manifest.row_count,
            "manifest_sha256": sha256_file(manifest_path),
            "parts": [
                {"file": part.file, "rows": part.rows, "sha256": part.sha256}
                for part in manifest.parts
            ],
        }

    generated: dict[str, Any] = {}
    generated_paths = [
        *(data_root / "bronze" / stamp).glob("*.parquet"),
        data_root / "silver" / stamp / "ahv_complaints.parquet",
        artifact_root / stamp / "ahv-cohort-profile.json",
        artifact_root / stamp / "ahv-cohort-data-card.md",
    ]
    for path in sorted(generated_paths):
        if not path.exists():
            continue
        details: dict[str, Any] = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        if path.suffix == ".parquet":
            details["row_count"] = pl.scan_parquet(path).select(pl.len()).collect().item()
        generated[str(path)] = details

    payload = {
        "format_version": 1,
        "snapshot_date": stamp,
        "generated_at": datetime.now(UTC).isoformat(),
        "raw_sources": raw_sources,
        "generated_files": generated,
    }
    output_directory = data_root / "manifests"
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / f"{stamp}.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path
