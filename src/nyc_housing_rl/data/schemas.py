"""Strict-enough source contracts that retain forward-compatible extra fields."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

NonEmpty = Annotated[str, Field(min_length=1)]


class SourceModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class Ahv311Record(SourceModel):
    unique_key: NonEmpty
    created_date: datetime
    agency: Literal["DOB"]
    complaint_type: Literal["AHV Inspection Unit"]
    descriptor: str | None = None
    status: NonEmpty
    closed_date: datetime | None = None
    resolution_description: str | None = None
    resolution_action_updated_date: datetime | None = None
    incident_address: str | None = None
    street_name: str | None = None
    incident_zip: str | None = None
    community_board: str | None = None
    council_district: str | None = None
    police_precinct: str | None = None
    bbl: str | None = None
    borough: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    open_data_channel_type: str | None = None

    @field_validator("bbl")
    @classmethod
    def validate_bbl(cls, value: str | None) -> str | None:
        if value is not None and (not value.isdigit() or len(value) != 10):
            raise ValueError("BBL must be a 10-digit string")
        return value


class DobComplaintRecord(SourceModel):
    complaint_number: NonEmpty
    status: NonEmpty
    date_entered: datetime
    complaint_category: Literal["4X"]
    house_number: str | None = None
    house_street: str | None = None
    zip_code: str | None = None
    bin: str | None = None
    community_board: str | None = None
    unit: str | None = None
    disposition_date: datetime | None = None
    disposition_code: str | None = None
    inspection_date: datetime | None = None
    dobrundate: str | None = None

    @field_validator("date_entered", "disposition_date", "inspection_date", mode="before")
    @classmethod
    def parse_us_date(cls, value: object) -> object:
        if isinstance(value, str) and "/" in value:
            return datetime.strptime(value, "%m/%d/%Y")
        return value


class DispositionCodeRecord(SourceModel):
    code: NonEmpty
    disposition: NonEmpty


class AhvPermitRecord(SourceModel):
    ahv_permit_number: NonEmpty
    variance_start_date_time: datetime
    variance_end_date_time: datetime
    bbl: str | None = None
    bin: str | None = None
    ahvpermitstatus: str | None = None
    variancetype: str | None = None
    reasonforvariance: str | None = None
    borough: str | None = None
    housenumber: str | None = None
    streetname: str | None = None
    workpermitnumber: str | None = None
    residence_200ft: bool | None = None
    enclosed_work: bool | None = None
    demolition: bool | None = None
    crane_use: bool | None = None
    latitude: float | None = None
    longitude: float | None = None


SCHEMAS: dict[str, type[SourceModel]] = {
    "ahv_311": Ahv311Record,
    "dob_4x": DobComplaintRecord,
    "disposition_codes": DispositionCodeRecord,
    "ahv_permits": AhvPermitRecord,
}
