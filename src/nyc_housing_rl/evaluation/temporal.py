"""Temporal scenario boundaries for learned-policy evaluation."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import polars as pl

from nyc_housing_rl.simulation.scenarios import complaints_from_silver
from nyc_housing_rl.simulation.types import Complaint


def temporal_split_from_silver(
    path: Path, *, train_end: date
) -> tuple[list[Complaint], list[Complaint]]:
    """Split after point-in-time feature construction; no random-row headline split."""

    rows = (
        pl.read_parquet(path).sort("created_date", "unique_key").select("created_date").to_dicts()
    )
    complaints = complaints_from_silver(path)
    train: list[Complaint] = []
    evaluation: list[Complaint] = []
    for row, complaint in zip(rows, complaints, strict=True):
        created = row["created_date"]
        timestamp = created if isinstance(created, datetime) else datetime.fromisoformat(created)
        (train if timestamp.date() <= train_end else evaluation).append(complaint)
    if not train or not evaluation:
        raise ValueError("Temporal cutoff must produce non-empty train and evaluation scenarios")
    return train, evaluation
