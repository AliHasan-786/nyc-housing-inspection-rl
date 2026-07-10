from datetime import date
from pathlib import Path

import httpx
import polars as pl

from nyc_housing_rl.data.bronze import build_bronze
from nyc_housing_rl.data.client import SocrataClient
from nyc_housing_rl.data.profile import build_profile
from nyc_housing_rl.data.silver import build_silver
from nyc_housing_rl.data.snapshot import write_snapshot
from nyc_housing_rl.data.sources import AHV_311


def test_bronze_builder_validates_and_writes_parquet(tmp_path: Path) -> None:
    payload = [
        {
            "unique_key": "1",
            "created_date": "2026-06-30T22:40:05.000",
            "agency": "DOB",
            "complaint_type": "AHV Inspection Unit",
            "status": "Closed",
        }
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload, request=request)

    snapshot_date = date(2026, 7, 6)
    raw_root = tmp_path / "raw"
    with SocrataClient(page_size=10, transport=httpx.MockTransport(handler)) as client:
        write_snapshot(
            client=client,
            spec=AHV_311,
            root=raw_root,
            snapshot_date=snapshot_date,
        )

    output, report = build_bronze(
        source_name="ahv_311",
        raw_root=raw_root,
        bronze_root=tmp_path / "bronze",
        snapshot_date=snapshot_date,
    )

    assert report.valid_rows == 1
    assert pl.read_parquet(output).select("unique_key").item() == "1"


def test_silver_and_profile_build_from_typed_parquet(tmp_path: Path) -> None:
    snapshot_date = date(2026, 7, 6)
    bronze = tmp_path / "bronze" / snapshot_date.isoformat()
    bronze.mkdir(parents=True)
    pl.DataFrame(
        {
            "unique_key": ["1"],
            "created_date": ["2026-06-29T23:36:50"],
            "status": ["Closed"],
            "incident_address": ["216 EAST 201 STREET"],
            "resolution_description": ["Issued an Office summons."],
            "bbl": ["2033060022"],
            "borough": ["BRONX"],
        }
    ).write_parquet(bronze / "ahv_311.parquet")
    pl.DataFrame(
        {
            "complaint_number": ["2444256"],
            "date_entered": ["2026-06-29T00:00:00"],
            "house_number": ["216"],
            "house_street": ["EAST 201 STREET"],
            "bin": ["2017194"],
            "disposition_code": ["A8"],
            "inspection_date": ["2026-06-30T00:00:00"],
        }
    ).write_parquet(bronze / "dob_4x.parquet")
    pl.DataFrame(
        {
            "ahv_permit_number": ["X1"],
            "bbl": ["2033060022"],
            "variance_start_date_time": ["2026-06-29T18:00:00"],
            "variance_end_date_time": ["2026-06-30T02:00:00"],
        }
    ).write_parquet(bronze / "ahv_permits.parquet")

    silver = build_silver(
        bronze_root=tmp_path / "bronze",
        silver_root=tmp_path / "silver",
        snapshot_date=snapshot_date,
    )
    profile_json, profile_markdown = build_profile(
        silver_path=silver,
        output_root=tmp_path / "artifacts",
        snapshot_date=snapshot_date,
    )

    assert pl.read_parquet(silver).select("outcome_label").item() == "actionable"
    assert profile_json.exists()
    assert "AHV Complaint Cohort Data Card" in profile_markdown.read_text(encoding="utf-8")
