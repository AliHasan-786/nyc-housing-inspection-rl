from datetime import date, datetime

from nyc_housing_rl.data.profile import profile_rows, render_markdown


def test_profile_reports_unresolved_and_match_quality() -> None:
    rows = [
        {
            "unique_key": "1",
            "created_date": datetime(2026, 1, 1),
            "outcome_label": "unresolved",
            "borough": "BRONX",
            "dob_match_status": "unmatched",
            "bbl": None,
            "permit_overlap": False,
        }
    ]
    profile = profile_rows(rows, snapshot_date=date(2026, 7, 6))
    markdown = render_markdown(profile)
    assert profile["outcome_counts"] == {"unresolved": 1}
    assert "Open/censored" in markdown
