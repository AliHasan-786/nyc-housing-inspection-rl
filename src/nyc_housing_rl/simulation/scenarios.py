"""Build leakage-safe simulation scenarios from the silver AHV cohort."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path

import polars as pl

from nyc_housing_rl.domain import OutcomeLabel
from nyc_housing_rl.simulation.types import Complaint

BOROUGH_CODES = {"MANHATTAN": 0, "BROOKLYN": 1, "QUEENS": 2, "BRONX": 3, "STATEN ISLAND": 4}


def complaints_from_silver(path: Path, *, max_complaints: int | None = None) -> list[Complaint]:
    """Create a scenario with state features available by complaint creation time.

    ``outcome_label`` becomes a latent simulation result and is never used in the risk
    score. Borough is used only as an operational geography/grouping key, never as a
    protected-class proxy or a fairness conclusion.
    """

    rows = pl.read_parquet(path).sort("created_date", "unique_key").to_dicts()
    if max_complaints is not None:
        rows = rows[:max_complaints]
    first_day = _as_datetime(rows[0]["created_date"]).date()
    prior_by_bbl: defaultdict[str, int] = defaultdict(int)
    complaints: list[Complaint] = []
    for row in rows:
        created = _as_datetime(row["created_date"])
        bbl = str(row.get("bbl") or row["unique_key"])
        prior = prior_by_bbl[bbl]
        night = created.hour >= 22 or created.hour < 6
        permit_overlap = bool(row.get("permit_overlap"))
        risk = min(
            1.0,
            0.15 + 0.25 * float(night) + 0.18 * min(prior, 3) + 0.12 * float(not permit_overlap),
        )
        label = OutcomeLabel(str(row["outcome_label"]))
        borough_name = str(row.get("borough") or "").upper()
        complaints.append(
            Complaint(
                complaint_id=str(row["unique_key"]),
                arrival_day=(created.date() - first_day).days,
                borough=BOROUGH_CODES.get(borough_name, 0),
                risk_score=risk,
                prior_complaints=prior,
                permit_overlap=permit_overlap,
                equity_group=f"borough:{borough_name or 'unknown'}",
                latent_outcome=label,
            )
        )
        prior_by_bbl[bbl] += 1
    return complaints


def _as_datetime(value: datetime | str) -> datetime:
    return value if isinstance(value, datetime) else datetime.fromisoformat(value)
