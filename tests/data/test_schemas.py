import pytest
from pydantic import ValidationError

from nyc_housing_rl.data.schemas import Ahv311Record, DobComplaintRecord


def test_311_schema_preserves_identifiers_and_parses_timestamp() -> None:
    record = Ahv311Record.model_validate(
        {
            "unique_key": "00123",
            "created_date": "2026-06-30T22:40:05.000",
            "agency": "DOB",
            "complaint_type": "AHV Inspection Unit",
            "status": "Closed",
            "bbl": "3001750001",
        }
    )
    assert record.unique_key == "00123"
    assert record.created_date.year == 2026


def test_311_schema_rejects_malformed_bbl() -> None:
    with pytest.raises(ValidationError, match="10-digit"):
        Ahv311Record.model_validate(
            {
                "unique_key": "1",
                "created_date": "2026-06-30T22:40:05.000",
                "agency": "DOB",
                "complaint_type": "AHV Inspection Unit",
                "status": "Closed",
                "bbl": "123",
            }
        )


def test_dob_schema_parses_us_dates() -> None:
    record = DobComplaintRecord.model_validate(
        {
            "complaint_number": "2444256",
            "status": "CLOSED",
            "date_entered": "06/29/2026",
            "complaint_category": "4X",
        }
    )
    assert record.date_entered.date().isoformat() == "2026-06-29"
