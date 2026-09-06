from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import CoverageBucket, ORMModel


class RateMetric(ORMModel):
    sample_size: int = Field(ge=0)
    value: float | None = None


class AnalyticsSummary(ORMModel):
    case_count: int
    diagnosed_count: int
    pending_review_count: int
    reviewed_count: int
    accepted_count: int = 0
    edited_count: int = 0
    rejected_count: int = 0
    unresolved_count: int = 0
    verified_count: int = 0
    rai_event_count: int
    rule_error_count: int
    counts_by_concept: list[CoverageBucket]
    counts_by_severity: list[CoverageBucket]
    review_verdicts: list[CoverageBucket]
    rai_failure_classes: list[CoverageBucket] = Field(default_factory=list)
    ai_human_agreement: RateMetric
    ai_expected_match: RateMetric
    verification_success: RateMetric = Field(default_factory=lambda: RateMetric(sample_size=0, value=None))


class ReviewQueueItem(ORMModel):
    review_id: int | None = None
    diagnosis_id: int
    case_id: int
    case_code: str
    title: str
    concept_tag: str
    status: str
    created_at: datetime


class ReviewQueueResponse(ORMModel):
    items: list[ReviewQueueItem]
    total: int


class RaiEventRead(ORMModel):
    id: int
    review_id: int
    case_id: int
    case_code: str | None = None
    verdict: str | None = None
    failure_class: str
    explanation: str
    record_kind: str = "reviewed_lab_case"
    ai_snapshot_json: dict = Field(default_factory=dict)
    human_correction_json: dict = Field(default_factory=dict)
    created_at: datetime


class RaiEventListResponse(ORMModel):
    items: list[RaiEventRead]
    total: int
