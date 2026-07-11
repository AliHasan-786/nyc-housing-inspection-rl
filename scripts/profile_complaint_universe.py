"""Profile the full NYC DOB complaint universe from a local bulk export.

Sprint 3 groundwork: the first real cohort (782 AHV complaints, ~16
actionable outcomes) is too thin a positive class for the predictive tier.
This script profiles the entire DOB Complaints Received dataset — every
complaint the Department of Buildings has recorded — so cohort widening is
an evidence-based scope decision instead of a guess.

Input: the official Socrata bulk CSV export (eabe-havv), fetched locally:

    curl -o dob_complaints_full.csv \
      "https://data.cityofnewyork.us/api/views/eabe-havv/rows.csv?accessType=DOWNLOAD"

Raw data stays local, consistent with the repository's data policy. The
committed outputs are aggregates only: a markdown data card and a JSON
summary whose manifest records the source file's size and SHA-256 so the
profile is reproducible against the same export.

Usage:

    python scripts/profile_complaint_universe.py \
      --input /path/to/dob_complaints_full.csv \
      --data-card docs/data/dob-complaint-universe.md \
      --summary data/manifests/dob-complaint-universe.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import polars as pl


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--data-card", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--top-n", type=int, default=15)
    args = parser.parse_args()

    source = Path(args.input)
    frame = pl.scan_csv(source, infer_schema_length=0)

    parsed = frame.with_columns(
        pl.col("Date Entered").str.strptime(pl.Date, "%m/%d/%Y", strict=False).alias("entered"),
        pl.col("Inspection Date").str.strptime(pl.Date, "%m/%d/%Y", strict=False).alias("inspected"),
    )

    total = parsed.select(pl.len()).collect().item()
    date_range = parsed.select(
        pl.col("entered").min().alias("min"),
        pl.col("entered").max().alias("max"),
    ).collect()
    inspected_share = parsed.select(
        (pl.col("inspected").is_not_null().sum() / pl.len()).alias("share")
    ).collect().item()

    def counted(column: str, limit: int) -> list[dict[str, object]]:
        rows = (
            parsed.group_by(column)
            .agg(pl.len().alias("count"))
            .sort("count", descending=True)
            .head(limit)
            .collect()
        )
        return [
            {
                "value": row[column] if row[column] is not None else "(blank)",
                "count": row["count"],
                "share": round(row["count"] / total, 4),
            }
            for row in rows.to_dicts()
        ]

    per_year = (
        parsed.with_columns(pl.col("entered").dt.year().alias("year"))
        .group_by("year")
        .agg(pl.len().alias("count"))
        .sort("year")
        .collect()
    )
    year_counts = [
        {"year": row["year"], "count": row["count"]}
        for row in per_year.to_dicts()
        if row["year"] is not None
    ]

    summary = {
        "generatedAt": datetime.now(UTC).strftime("%Y-%m-%d"),
        "source": {
            "dataset": "DOB Complaints Received (NYC Open Data, eabe-havv)",
            "file": source.name,
            "bytes": source.stat().st_size,
            "sha256": sha256_file(source),
        },
        "totalComplaints": total,
        "dateRange": {
            "first": str(date_range["min"][0]),
            "last": str(date_range["max"][0]),
        },
        "inspectionDateShare": round(inspected_share, 4),
        "complaintsPerYear": year_counts,
        "topComplaintCategories": counted("Complaint Category", args.top_n),
        "statusCounts": counted("Status", 5),
        "topUnits": counted("Unit", 10),
        "topDispositionCodes": counted("Disposition Code", args.top_n),
        "interpretation": (
            "Category, unit, and disposition codes are profiled as raw codes "
            "on purpose: mapping them to labels and outcome semantics is the "
            "documented Sprint 3 modeling decision, not a profiling step. "
            "Counts are complaint-level; one building can generate many "
            "complaints, so building-level dedup happens downstream."
        ),
    }

    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    card_lines = [
        "# Data Card: DOB Complaint Universe",
        "",
        f"Generated {summary['generatedAt']} from the official bulk export of "
        "*DOB Complaints Received* (NYC Open Data `eabe-havv`). Raw data stays "
        "local; this card and its JSON summary are aggregates with a source "
        "checksum for exact reproducibility.",
        "",
        f"- **Total complaints:** {total:,}",
        f"- **First / last complaint date:** {summary['dateRange']['first']} → "
        f"{summary['dateRange']['last']}",
        f"- **Rows with an inspection date:** {inspected_share:.1%}",
        f"- **Source:** {summary['source']['bytes']:,} bytes, SHA-256 "
        f"`{summary['source']['sha256'][:16]}…`",
        "",
        "## Complaints per year",
        "",
        "| Year | Complaints |",
        "| --- | ---: |",
    ]
    for row in year_counts:
        card_lines.append(f"| {row['year']} | {row['count']:,} |")
    card_lines += [
        "",
        "## Top complaint categories (raw codes)",
        "",
        "| Category code | Count | Share |",
        "| --- | ---: | ---: |",
    ]
    for row in summary["topComplaintCategories"]:
        card_lines.append(f"| {row['value']} | {row['count']:,} | {row['share']:.2%} |")
    card_lines += [
        "",
        "## Status",
        "",
        "| Status | Count | Share |",
        "| --- | ---: | ---: |",
    ]
    for row in summary["statusCounts"]:
        card_lines.append(f"| {row['value']} | {row['count']:,} | {row['share']:.2%} |")
    card_lines += [
        "",
        "## Why this exists",
        "",
        "The current AHV cohort (782 complaints, ~16 actionable outcomes) cannot "
        "support the Sprint 3 predictive tier on its own. This profile scopes the "
        "cohort-widening decision across the full complaint universe: which "
        "categories carry enough volume and enough disposition variation to give "
        "temporal validation a real positive class.",
        "",
        summary["interpretation"],
        "",
    ]
    card_path = Path(args.data_card)
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text("\n".join(card_lines), encoding="utf-8")

    print(
        json.dumps(
            {
                "totalComplaints": total,
                "years": len(year_counts),
                "dataCard": str(card_path),
                "summary": str(summary_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
