from datetime import datetime

from nyc_housing_rl.data.silver import classify_outcome, link_complaints, normalize_address
from nyc_housing_rl.domain import OutcomeLabel


def test_address_normalization_collapses_source_formatting() -> None:
    assert normalize_address("216 East   201 Street.") == "216 EAST 201 STREET"


def test_outcome_classifier_does_not_treat_open_as_negative() -> None:
    assert (
        classify_outcome(status="Open", resolution="no further action", disposition_code="I2")
        == OutcomeLabel.UNRESOLVED
    )


def test_linkage_keeps_match_audit_and_permit_overlap() -> None:
    complaints = [
        {
            "unique_key": "69558903",
            "created_date": datetime(2026, 6, 29, 23, 36, 50),
            "status": "Closed",
            "incident_address": "216 EAST  201 STREET",
            "resolution_description": "The Department investigated and issued an Office summons.",
            "bbl": "2033060022",
        }
    ]
    dob = [
        {
            "complaint_number": "2444256",
            "date_entered": datetime(2026, 6, 29),
            "house_number": "216",
            "house_street": "EAST 201 STREET",
            "bin": "2017194",
            "disposition_code": "A8",
            "inspection_date": datetime(2026, 6, 30),
        }
    ]
    permits = [
        {
            "ahv_permit_number": "X1",
            "bbl": "2033060022",
            "variance_start_date_time": datetime(2026, 6, 29, 18),
            "variance_end_date_time": datetime(2026, 6, 30, 2),
        }
    ]

    row = link_complaints(complaints, dob, permits)[0]

    assert row["dob_match_status"] == "exact"
    assert row["dob_complaint_number"] == "2444256"
    assert row["outcome_label"] == OutcomeLabel.ACTIONABLE.value
    assert row["permit_overlap"] is True
    assert row["permit_numbers"] == ["X1"]
