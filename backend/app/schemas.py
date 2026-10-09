"""Input contracts shared by create and partial-update validation."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Priority = Literal["High", "Medium", "Low"]
Status = Literal[
    "Saved",
    "Contacted",
    "Applied",
    "Screening",
    "Assessment",
    "Technical interview",
    "Final interview",
    "Offer",
    "Accepted",
    "Rejected",
    "Withdrawn",
    "Ghosted",
]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("*", mode="before")
    @classmethod
    def limit_text(cls, value):
        if isinstance(value, str) and len(value) > 100000:
            raise ValueError("Text is too long")
        return value

    @field_validator("website", "linkedin", "job_url", "meeting_url", check_fields=False)
    @classmethod
    def safe_url(cls, value):
        if value and not value.startswith(("https://", "http://")):
            raise ValueError("Use a full https:// or http:// URL")
        return value


class Country(Record):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(pattern=r"^[A-Z]{2}$")
    priority: Priority = "Medium"
    notes: str = ""
    visa_notes: str = ""
    language_notes: str = ""
    target_roles: str = ""
    salary_notes: str = ""
    job_boards: str = ""


class Company(Record):
    country_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    website: str = ""
    email: str = ""
    linkedin: str = ""
    sponsorship: Literal["Unknown", "Yes", "No"] = "Unknown"
    notes: str = ""


class Application(Record):
    company_id: int = Field(gt=0)
    resume_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    status: Status = "Saved"
    priority: Priority = "Medium"
    source: str = ""
    job_url: str = ""
    description: str = ""
    salary_notes: str = ""
    location: str = ""
    date_applied: date | None = None
    first_response_at: date | None = None
    notes: str = ""


class Contact(Record):
    country_id: int = Field(gt=0)
    company_id: int | None = None
    name: str = Field(min_length=1, max_length=200)
    title: str = ""
    email: str = ""
    linkedin: str = ""
    contact_type: Literal["Recruiter", "Engineer", "Manager", "Alumni", "Founder", "Other"] = (
        "Recruiter"
    )
    relationship: Literal[
        "Discovered",
        "Connection sent",
        "Connected",
        "Messaged",
        "Replied",
        "Ongoing",
        "Dormant",
    ] = "Discovered"
    notes: str = ""


class Interaction(Record):
    contact_id: int = Field(gt=0)
    application_id: int | None = None
    kind: Literal["Note", "LinkedIn message", "Email sent", "Reply received", "Call", "Meeting"] = (
        "Note"
    )
    content: str = Field(min_length=1)
    occurred_at: datetime


class Followup(Record):
    country_id: int = Field(gt=0)
    application_id: int | None = None
    contact_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    due_date: date
    completed: bool = False
    notes: str = ""


class Interview(Record):
    application_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=200)
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=5, le=720)
    interviewer: str = ""
    meeting_url: str = ""
    status: Literal["Scheduled", "Completed", "Cancelled"] = "Scheduled"
    notes_before: str = ""
    notes_after: str = ""


class ResumeMetadata(Record):
    name: str = Field(min_length=1, max_length=200)
    language: str = ""
    target_role: str = ""
    notes: str = ""
    archived: bool = False


MODELS = {
    "countries": Country,
    "companies": Company,
    "applications": Application,
    "contacts": Contact,
    "interactions": Interaction,
    "followups": Followup,
    "interviews": Interview,
}
