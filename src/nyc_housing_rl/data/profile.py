"""Generate a compact, versioned profile from the linked AHV cohort."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

import polars as pl


def build_profile(
    *, silver_path: Path, output_root: Path, snapshot_date: date
) -> tuple[Path, Path]:
    rows = pl.read_parquet(silver_path).to_dicts()
    profile = profile_rows(rows, snapshot_date=snapshot_date)
    output_directory = output_root / snapshot_date.isoformat()
    output_directory.mkdir(parents=True, exist_ok=True)
    json_path = output_directory / "ahv-cohort-profile.json"
    markdown_path = output_directory / "ahv-cohort-data-card.md"
    json_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(profile), encoding="utf-8")
    return json_path, markdown_path


def profile_rows(rows: list[dict[str, Any]], *, snapshot_date: date) -> dict[str, Any]:
    created = [_as_datetime(row["created_date"]) for row in rows]
    label_counts = Counter(str(row["outcome_label"]) for row in rows)
    return {
        "snapshot_date": snapshot_date.isoformat(),
        "row_count": len(rows),
        "unique_keys": len({row["unique_key"] for row in rows}),
        "created_min": min(created).isoformat() if created else None,
        "created_max": max(created).isoformat() if created else None,
        "outcome_counts": dict(sorted(label_counts.items())),
        "borough_counts": dict(
            sorted(Counter(str(row.get("borough") or "MISSING") for row in rows).items())
        ),
        "match_counts": dict(sorted(Counter(str(row["dob_match_status"]) for row in rows).items())),
        "missing_bbl": sum(not row.get("bbl") for row in rows),
        "permit_overlap_rows": sum(bool(row.get("permit_overlap")) for row in rows),
    }


def render_markdown(profile: dict[str, Any]) -> str:
    def table(counts: dict[str, int]) -> str:
        lines = ["| Value | Rows | Share |", "|---|---:|---:|"]
        total = int(profile["row_count"])
        for value, count in counts.items():
            share = count / total if total else 0.0
            lines.append(f"| {value} | {count:,} | {share:.1%} |")
        return "\n".join(lines)

    return f"""# AHV Complaint Cohort Data Card

Snapshot date: {profile["snapshot_date"]}

## Scope

Official NYC 311 records where agency is DOB and problem is `AHV Inspection Unit`, linked
to DOB complaint category `4X` and complaint-address AHV permit candidates. This is an
observational administrative cohort, not a randomized policy dataset.

## Coverage

- Rows: {profile["row_count"]:,}
- Unique service-request keys: {profile["unique_keys"]:,}
- Created range: {profile["created_min"]} to {profile["created_max"]}
- Missing BBL: {profile["missing_bbl"]:,}
- Complaints with a permit interval overlapping creation: {profile["permit_overlap_rows"]:,}

## Research outcome labels

{table(profile["outcome_counts"])}

Open/censored, unknown, and unclassified outcomes remain `unresolved`; they are not
negative examples.

## DOB record linkage

{table(profile["match_counts"])}

Record linkage uses normalized address and a +/- 1 day entry window. Match status and
candidate count remain in the analytical table so ambiguous links can be excluded or tested
in sensitivity analysis.

## Borough distribution

{table(profile["borough_counts"])}

## Limitations

- Resolution and disposition fields are administrative outcomes, not causal treatment effects.
- Address-based linkage may miss formatting differences or select among same-day duplicates.
- The AHV permit source currently stops before some newer 311 complaints.
- Outcome mappings are research definitions and require sensitivity analysis.
- Protected-class fairness cannot be inferred from borough balance.
"""


def _as_datetime(value: datetime | str) -> datetime:
    return value if isinstance(value, datetime) else datetime.fromisoformat(value)
