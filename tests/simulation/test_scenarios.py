from datetime import datetime
from pathlib import Path

import polars as pl

from nyc_housing_rl.simulation.scenarios import complaints_from_silver


def test_scenario_builder_uses_only_prior_history_for_risk(tmp_path: Path) -> None:
    path = tmp_path / "silver.parquet"
    pl.DataFrame(
        {
            "unique_key": ["1", "2"],
            "created_date": [datetime(2026, 1, 1, 23), datetime(2026, 1, 2, 12)],
            "bbl": ["1000000001", "1000000001"],
            "permit_overlap": [False, True],
            "borough": ["MANHATTAN", "MANHATTAN"],
            "outcome_label": ["no_action", "actionable"],
        }
    ).write_parquet(path)
    complaints = complaints_from_silver(path)
    assert complaints[0].prior_complaints == 0
    assert complaints[1].prior_complaints == 1
    assert complaints[0].risk_score > complaints[1].risk_score - 0.2
