from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.models.enums import CaseSource, ConceptTag, OsiLayer, Severity
from app.schemas.common import ORMModel, Pagination
from app.schemas.related import DiagnosisRead, ReviewRead, RuleRunRead, VerificationRead


def _require_text(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("field cannot be empty")
    return cleaned


class CaseBase(ORMModel):
    title: str = Field(min_length=1, max_length=200)
    symptom: str = Field(min_length=1)
    topology_note: str = Field(min_length=1)
    show_outputs: str = Field(min_length=1)
    expected_fault: str = Field(min_length=1)
    osi_layer: OsiLayer
    concept_tag: ConceptTag
    severity: Severity
    source: CaseSource = CaseSource.PACKET_TRACER

    @field_validator("title", "symptom", "topology_note", "show_outputs", "expected_fault")
    @classmethod
    def not_blank(cls, value: str) -> str:
        return _require_text(value)


class CaseCreate(CaseBase):
    case_code: str = Field(min_length=3, max_length=32, pattern=r"^[A-Z]+-\d{3}$")


class CaseUpdate(ORMModel):
    title: str | None = None
    symptom: str | None = None
    topology_note: str | None = None
    show_outputs: str | None = None
    expected_fault: str | None = None
    osi_layer: OsiLayer | None = None
    concept_tag: ConceptTag | None = None
    severity: Severity | None = None
    source: CaseSource | None = None

    @field_validator("title", "symptom", "topology_note", "show_outputs", "expected_fault")
    @classmethod
    def not_blank_optional(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _require_text(value)


class CaseSummary(ORMModel):
    id: int
    case_code: str
    title: str
    osi_layer: OsiLayer
    concept_tag: ConceptTag
    severity: Severity
    source: CaseSource
    lifecycle_status: str
    created_at: datetime
    updated_at: datetime


class CaseDetail(CaseSummary):
    symptom: str
    topology_note: str
    show_outputs: str
    expected_fault: str
    latest_rule_run: RuleRunRead | None = None
    latest_diagnosis: DiagnosisRead | None = None
    latest_review: ReviewRead | None = None
    latest_verification: VerificationRead | None = None


class CaseListResponse(ORMModel):
    items: list[CaseSummary]
    pagination: Pagination


class CaseImportResult(ORMModel):
    created: int
    updated: int
    skipped: int
    errors: list[str] = Field(default_factory=list)
