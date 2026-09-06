from __future__ import annotations

from datetime import datetime

from pydantic import Field, computed_field, model_validator

from app.models.enums import ConceptTag, OsiLayer, RaiFailureClass, ReviewVerdict
from app.schemas.common import ORMModel


class RuleFinding(ORMModel):
    rule_name: str
    status: str
    evidence: list[str] = Field(default_factory=list)
    explanation: str
    devices: list[str] = Field(default_factory=list)
    severity: str | None = None


class RuleEvaluateRequest(ORMModel):
    show_outputs: str = Field(min_length=1)
    topology_note: str = ""


class RuleEvaluateResponse(ORMModel):
    results: list[RuleFinding]
    fail_count: int
    pass_count: int
    rule_run_id: int | None = None
    case_id: int | None = None


class RuleRunRead(ORMModel):
    id: int
    case_id: int
    diagnosis_id: int | None
    phase: str
    findings_json: list
    error_count: int
    created_at: datetime


class DiagnosisRead(ORMModel):
    id: int
    case_id: int
    model_name: str
    root_cause: str
    osi_layer: str
    concept_tag: str
    severity: str
    verification_command: str
    confidence: float
    confidence_label: str
    evidence_json: list
    next_commands_json: list
    fix_steps_json: list
    grounded: bool
    expected_match: bool | None
    status: str
    raw_response: str | None = None
    created_at: datetime

    @computed_field
    @property
    def concept(self) -> str:
        return self.concept_tag


class DiagnosisDetail(DiagnosisRead):
    ungrounded_quotes: list[str] = Field(default_factory=list)
    next_command: str | None = None
    raw_response: str | None = None


class ReviewCreate(ORMModel):
    verdict: ReviewVerdict
    reviewer_name: str = "Lab Reviewer"
    correction_reason: str | None = None
    corrected_root_cause: str | None = None
    corrected_osi_layer: OsiLayer | None = None
    corrected_concept_tag: ConceptTag | None = None
    corrected_fix_steps: list[str] | None = None
    override_ungrounded: bool = False
    failure_class: RaiFailureClass | None = None

    @model_validator(mode="after")
    def require_fields_for_verdict(self) -> "ReviewCreate":
        notes = (self.correction_reason or "").strip()
        if self.verdict == ReviewVerdict.EDITED:
            missing: list[str] = []
            if not (self.corrected_root_cause or "").strip():
                missing.append("corrected_root_cause")
            if self.corrected_osi_layer is None:
                missing.append("corrected_osi_layer")
            if self.corrected_concept_tag is None:
                missing.append("corrected_concept_tag")
            steps = [step.strip() for step in (self.corrected_fix_steps or []) if step and step.strip()]
            if not steps:
                missing.append("corrected_fix_steps")
            if not notes:
                missing.append("correction_reason")
            if self.failure_class is None:
                missing.append("failure_class")
            if missing:
                raise ValueError("Edited reviews require: " + ", ".join(missing))
            self.corrected_fix_steps = steps
            self.correction_reason = notes
        elif self.verdict == ReviewVerdict.REJECTED:
            if not notes or self.failure_class is None:
                raise ValueError("Rejected reviews require correction_reason and failure_class")
            self.correction_reason = notes
        elif self.override_ungrounded and not notes:
            raise ValueError("override_ungrounded requires correction_reason")
        return self


class ReviewRead(ORMModel):
    id: int
    diagnosis_id: int
    reviewer_id: int
    verdict: str
    corrected_root_cause: str | None
    corrected_osi_layer: str | None
    corrected_concept_tag: str | None
    corrected_fix_steps_json: list | None
    correction_reason: str | None
    override_ungrounded: bool
    fix_applied: bool = False
    fix_applied_by: str | None = None
    fix_applied_at: datetime | None = None
    created_at: datetime


class ApplyFixCreate(ORMModel):
    applied_by: str = Field(default="Lab Reviewer", min_length=1, max_length=120)

    @model_validator(mode="after")
    def strip_applied_by(self) -> "ApplyFixCreate":
        self.applied_by = self.applied_by.strip()
        if not self.applied_by:
            raise ValueError("applied_by cannot be blank")
        return self


class ReviewDetail(ReviewRead):
    reviewer_name: str
    diagnosis_status: str
    rai_event_id: int | None = None
    original_ai: dict = Field(default_factory=dict)


class VerificationCreate(ORMModel):
    verified_by: str = Field(default="Lab Reviewer", min_length=1, max_length=120)
    notes: str | None = None

    @model_validator(mode="after")
    def strip_fields(self) -> "VerificationCreate":
        self.verified_by = self.verified_by.strip()
        if not self.verified_by:
            raise ValueError("verified_by cannot be blank")
        if self.notes is not None:
            self.notes = self.notes.strip() or None
        return self


class VerificationRead(ORMModel):
    id: int
    case_id: int
    review_id: int
    verified_by: str
    notes: str | None
    created_at: datetime
