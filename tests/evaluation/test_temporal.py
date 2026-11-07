from datetime import date, datetime
from pathlib import Path

import polars as pl
import pytest

from nyc_housing_rl.evaluation.temporal import temporal_split_from_silver


def test_temporal_split_rejects_an_undeclared_gap(tmp_path: Path) -> None:
    path = tmp_path / "silver.parquet"
    pl.DataFrame(
        {
            "unique_key": ["train", "gap", "evaluation"],
            "created_date": [
                datetime(2026, 1, 1),
                datetime(2026, 1, 2),
                datetime(2026, 1, 3),
            ],
            "bbl": ["1000000001", "1000000001", "1000000001"],
            "permit_overlap": [False, False, False],
            "borough": ["MANHATTAN", "MANHATTAN", "MANHATTAN"],
            "outcome_label": ["no_action", "no_action", "actionable"],
        }
    ).write_parquet(path)

    with pytest.raises(ValueError, match="between train and evaluation"):
        temporal_split_from_silver(
            path, train_end=date(2026, 1, 1), evaluation_start=date(2026, 1, 3)
        )
