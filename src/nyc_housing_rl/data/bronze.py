"""Validate raw snapshots and write typed, source-level Parquet tables."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

import polars as pl
from pydantic import ValidationError

from nyc_housing_rl.data.schemas import SCHEMAS
from nyc_housing_rl.data.snapshot import read_snapshot_rows, snapshot_directory

PRIMARY_KEYS: dict[str, tuple[str, ...]] = {
    "ahv_311": ("unique_key",),
    "dob_4x": ("complaint_number",),
    "disposition_codes": ("code",),
    "ahv_permits": (
        "ahv_permit_number",
        "variance_start_date_time",
        "variance_end_date_time",
    ),
}


@dataclass(frozen=True, slots=True)
class ValidationReport:
    source_name: str
    input_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_primary_keys: int
    errors: tuple[str, ...]


def build_bronze(
    *,
    source_name: str,
    raw_root: Path,
    bronze_root: Path,
    snapshot_date: date,
) -> tuple[Path, ValidationReport]:
    if source_name not in SCHEMAS:
        raise KeyError(f"No source schema registered for {source_name}")
    raw_directory = snapshot_directory(raw_root, snapshot_date, source_name)
    raw_rows = read_snapshot_rows(raw_directory)
    model = SCHEMAS[source_name]
    valid_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, row in enumerate(raw_rows):
        try:
            valid_rows.append(model.model_validate(row).model_dump(mode="python"))
        except ValidationError as error:
            if len(errors) < 25:
                errors.append(f"row {index}: {error}")

    if errors:
        report = ValidationReport(
            source_name=source_name,
            input_rows=len(raw_rows),
            valid_rows=len(valid_rows),
            invalid_rows=len(raw_rows) - len(valid_rows),
            duplicate_primary_keys=0,
            errors=tuple(errors),
        )
        _write_report(bronze_root, snapshot_date, report)
        raise ValueError(f"{source_name} failed schema validation; see validation report")

    frame = pl.from_dicts(valid_rows, infer_schema_length=None) if valid_rows else pl.DataFrame()
    keys = PRIMARY_KEYS[source_name]
    duplicate_count = 0
    if not frame.is_empty():
        duplicate_count = int(frame.select(pl.struct(keys).is_duplicated().sum()).item())
        frame = frame.sort(list(keys))

    report = ValidationReport(
        source_name=source_name,
        input_rows=len(raw_rows),
        valid_rows=len(valid_rows),
        invalid_rows=0,
        duplicate_primary_keys=duplicate_count,
        errors=(),
    )
    _write_report(bronze_root, snapshot_date, report)
    if duplicate_count:
        raise ValueError(f"{source_name} contains {duplicate_count} duplicate primary keys")

    output_directory = bronze_root / snapshot_date.isoformat()
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / f"{source_name}.parquet"
    frame.write_parquet(output_path, compression="zstd", statistics=True)
    return output_path, report


def _write_report(root: Path, snapshot_date: date, report: ValidationReport) -> None:
    directory = root / snapshot_date.isoformat()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{report.source_name}.validation.json"
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
