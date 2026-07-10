"""Auditable record linkage and research outcome labels for AHV complaints."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path
from typing import Any

import polars as pl

from nyc_housing_rl.domain import OutcomeLabel

_NON_ALPHANUMERIC = re.compile(r"[^A-Z0-9 ]+")
_WHITESPACE = re.compile(r"\s+")


def normalize_address(value: str | None) -> str | None:
    if not value:
        return None
    normalized = _NON_ALPHANUMERIC.sub(" ", value.upper())
    normalized = _WHITESPACE.sub(" ", normalized).strip()
    return normalized or None


def classify_outcome(
    *,
    status: str,
    resolution: str | None,
    disposition_code: str | None,
) -> OutcomeLabel:
    text = (resolution or "").upper()
    code = (disposition_code or "").upper()
    if status.upper() != "CLOSED" or (not text and not code):
        return OutcomeLabel.UNRESOLVED
    if any(phrase in text for phrase in ("ISSUED AN OFFICE", "ISSUED A STOP WORK ORDER")):
        return OutcomeLabel.ACTIONABLE
    if code in {"A1", "A2", "A3", "A5", "A6", "A8", "A9", "V3", "W1"}:
        return OutcomeLabel.ACTIONABLE
    if "COULD NOT GAIN ACCESS" in text or code in {"C2", "C3", "C4", "C5", "C8"}:
        return OutcomeLabel.INACCESSIBLE
    if (
        "ANOTHER SERVICE REQUEST" in text
        or "REFERRED" in text
        or code.startswith("F")
        or code == "H1"
    ):
        return OutcomeLabel.REFERRED_OR_DUPLICATE
    if "NO FURTHER ACTION" in text or code == "I2":
        return OutcomeLabel.NO_ACTION
    return OutcomeLabel.UNRESOLVED


def build_silver(
    *,
    bronze_root: Path,
    silver_root: Path,
    snapshot_date: date,
) -> Path:
    bronze_directory = bronze_root / snapshot_date.isoformat()
    complaints = pl.read_parquet(bronze_directory / "ahv_311.parquet").to_dicts()
    dob_rows = pl.read_parquet(bronze_directory / "dob_4x.parquet").to_dicts()
    permit_path = bronze_directory / "ahv_permits.parquet"
    permits = pl.read_parquet(permit_path).to_dicts() if permit_path.exists() else []

    linked = link_complaints(complaints, dob_rows, permits)
    frame = pl.from_dicts(linked, infer_schema_length=None).sort("created_date", "unique_key")
    output_directory = silver_root / snapshot_date.isoformat()
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / "ahv_complaints.parquet"
    frame.write_parquet(output_path, compression="zstd", statistics=True)
    return output_path


def link_complaints(
    complaints: Iterable[dict[str, Any]],
    dob_rows: Iterable[dict[str, Any]],
    permits: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    dob_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in dob_rows:
        address = normalize_address(
            " ".join(part for part in (row.get("house_number"), row.get("house_street")) if part)
        )
        if address:
            dob_index[address].append(row)

    permit_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for permit in permits:
        bbl = permit.get("bbl")
        if bbl:
            permit_index[str(bbl)].append(permit)

    output: list[dict[str, Any]] = []
    for complaint in complaints:
        created = _as_datetime(complaint["created_date"])
        address = normalize_address(complaint.get("incident_address"))
        candidates = []
        if address:
            for row in dob_index.get(address, []):
                entered = _as_datetime(row["date_entered"])
                candidate_delta = (entered.date() - created.date()).days
                if abs(candidate_delta) <= 1:
                    candidates.append((abs(candidate_delta), row, candidate_delta))
        candidates.sort(key=lambda item: (item[0], str(item[1].get("complaint_number", ""))))

        match_status = "unmatched"
        match: dict[str, Any] | None = None
        delta_days: int | None = None
        if len(candidates) == 1:
            _, match, delta_days = candidates[0]
            match_status = "exact" if delta_days == 0 else "date_window"
        elif len(candidates) > 1:
            best_delta = candidates[0][0]
            best = [candidate for candidate in candidates if candidate[0] == best_delta]
            if len(best) == 1:
                _, match, delta_days = best[0]
                match_status = "exact" if delta_days == 0 else "date_window"
            else:
                match_status = "ambiguous"

        overlap = _permit_overlap(permit_index.get(str(complaint.get("bbl") or ""), []), created)
        disposition_code = (
            str(match.get("disposition_code")) if match and match.get("disposition_code") else None
        )
        label = classify_outcome(
            status=str(complaint["status"]),
            resolution=complaint.get("resolution_description"),
            disposition_code=disposition_code,
        )
        output.append(
            {
                **complaint,
                "normalized_address": address,
                "dob_match_status": match_status,
                "dob_match_candidate_count": len(candidates),
                "dob_match_delta_days": delta_days,
                "dob_complaint_number": match.get("complaint_number") if match else None,
                "dob_bin": match.get("bin") if match else None,
                "dob_disposition_code": disposition_code,
                "dob_inspection_date": match.get("inspection_date") if match else None,
                "outcome_label": label.value,
                "permit_overlap_count": len(overlap),
                "permit_overlap": bool(overlap),
                "permit_numbers": sorted(
                    str(item["ahv_permit_number"])
                    for item in overlap
                    if item.get("ahv_permit_number")
                ),
            }
        )
    return output


def _permit_overlap(permits: Iterable[dict[str, Any]], created: datetime) -> list[dict[str, Any]]:
    return [
        permit
        for permit in permits
        if _as_datetime(permit["variance_start_date_time"])
        <= created
        <= _as_datetime(permit["variance_end_date_time"])
    ]


def _as_datetime(value: datetime | str) -> datetime:
    return value if isinstance(value, datetime) else datetime.fromisoformat(value)
