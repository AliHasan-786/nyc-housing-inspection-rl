"""Versioned source definitions for the first real AHV cohort."""

from dataclasses import dataclass, field
from typing import Final


@dataclass(frozen=True, slots=True)
class DatasetSpec:
    """A public Socrata dataset and the cohort query used by this project."""

    name: str
    dataset_id: str
    title: str
    page_url: str
    select: tuple[str, ...]
    where: str | None = None
    order: tuple[str, ...] = field(default_factory=tuple)

    def query(self) -> dict[str, str]:
        params = {"$select": ",".join(self.select)}
        if self.where:
            params["$where"] = self.where
        if self.order:
            params["$order"] = ",".join(self.order)
        return params


AHV_311 = DatasetSpec(
    name="ahv_311",
    dataset_id="erm2-nwe9",
    title="311 Service Requests from 2020 to Present - AHV Inspection Unit cohort",
    page_url="https://data.cityofnewyork.us/d/erm2-nwe9",
    select=(
        "unique_key",
        "created_date",
        "closed_date",
        "agency",
        "agency_name",
        "complaint_type",
        "descriptor",
        "incident_zip",
        "incident_address",
        "street_name",
        "address_type",
        "city",
        "status",
        "resolution_description",
        "resolution_action_updated_date",
        "community_board",
        "council_district",
        "police_precinct",
        "bbl",
        "borough",
        "latitude",
        "longitude",
        "open_data_channel_type",
    ),
    where="agency = 'DOB' AND complaint_type = 'AHV Inspection Unit'",
    order=("unique_key",),
)

DOB_4X = DatasetSpec(
    name="dob_4x",
    dataset_id="eabe-havv",
    title="DOB Complaints Received - complaint category 4X",
    page_url="https://data.cityofnewyork.us/d/eabe-havv",
    select=(
        "complaint_number",
        "status",
        "date_entered",
        "house_number",
        "house_street",
        "zip_code",
        "bin",
        "community_board",
        "complaint_category",
        "unit",
        "disposition_date",
        "disposition_code",
        "inspection_date",
        "dobrundate",
    ),
    where="complaint_category = '4X'",
    order=("complaint_number",),
)

DISPOSITION_CODES = DatasetSpec(
    name="disposition_codes",
    dataset_id="6v9u-ndjg",
    title="Building Complaint Disposition Codes",
    page_url="https://data.cityofnewyork.us/d/6v9u-ndjg",
    select=("code", "disposition"),
    order=("code",),
)

AHV_PERMITS = DatasetSpec(
    name="ahv_permits",
    dataset_id="g76y-dcqj",
    title="DOB After Hour Variance Permits - complaint-linked BBL cohort",
    page_url="https://data.cityofnewyork.us/d/g76y-dcqj",
    select=(
        "ahv_permit_number",
        "ahvpermitstatus",
        "variancetype",
        "variance_start_date_time",
        "variance_end_date_time",
        "reasonforvariance",
        "bin",
        "bbl",
        "borough",
        "housenumber",
        "streetname",
        "workpermitnumber",
        "residence_200ft",
        "enclosed_work",
        "demolition",
        "crane_use",
        "latitude",
        "longitude",
    ),
    order=("ahv_permit_number", "variance_start_date_time", "variance_end_date_time"),
)

DATASETS: Final[dict[str, DatasetSpec]] = {
    spec.name: spec for spec in (AHV_311, DOB_4X, DISPOSITION_CODES, AHV_PERMITS)
}
