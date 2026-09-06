from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, InvalidReviewError, NotFoundError
from app.models.enums import DiagnosisStatus, ReviewVerdict
from app.models.tables import AuditEvent, Case, Diagnosis, RaiEvent, Review, User
from app.schemas.ops import RaiEventListResponse, RaiEventRead, ReviewQueueItem, ReviewQueueResponse
from app.schemas.related import ApplyFixCreate, ReviewCreate, ReviewDetail, ReviewRead
from app.services.users import get_or_create_reviewer


def ai_snapshot(diagnosis: Diagnosis) -> dict:
    return {
        "root_cause": diagnosis.root_cause,
        "osi_layer": diagnosis.osi_layer,
        "concept_tag": diagnosis.concept_tag,
        "concept": diagnosis.concept_tag,
        "severity": diagnosis.severity,
        "confidence": diagnosis.confidence,
        "confidence_label": diagnosis.confidence_label,
        "evidence": diagnosis.evidence_json,
        "fix_steps": diagnosis.fix_steps_json,
        "next_commands": diagnosis.next_commands_json,
        "verification_command": diagnosis.verification_command,
        "grounded": diagnosis.grounded,
        "raw_response": diagnosis.raw_response,
    }


def human_correction(payload: ReviewCreate) -> dict:
    return {
        "verdict": payload.verdict.value,
        "corrected_root_cause": payload.corrected_root_cause,
        "corrected_osi_layer": payload.corrected_osi_layer.value if payload.corrected_osi_layer else None,
        "corrected_concept_tag": payload.corrected_concept_tag.value if payload.corrected_concept_tag else None,
        "corrected_fix_steps": payload.corrected_fix_steps,
        "correction_reason": payload.correction_reason,
        "failure_class": payload.failure_class.value if payload.failure_class else None,
        "override_ungrounded": payload.override_ungrounded,
        "reviewer_name": payload.reviewer_name,
    }


class ReviewQueryService:
    def __init__(self, db: Session):
        self.db = db

    def queue(self) -> ReviewQueueResponse:
        rows = self.db.execute(
            select(Diagnosis, Case)
            .join(Case, Case.id == Diagnosis.case_id)
            .where(Diagnosis.status == DiagnosisStatus.PENDING_REVIEW.value)
            .order_by(Diagnosis.created_at.desc())
        ).all()
        items = [
            ReviewQueueItem(
                diagnosis_id=diagnosis.id,
                case_id=case.id,
                case_code=case.case_code,
                title=case.title,
                concept_tag=case.concept_tag,
                status=diagnosis.status,
                created_at=diagnosis.created_at,
            )
            for diagnosis, case in rows
        ]
        return ReviewQueueResponse(items=items, total=len(items))

    def rai_events(self) -> RaiEventListResponse:
        rows = self.db.execute(
            select(RaiEvent, Case, Review)
            .join(Case, Case.id == RaiEvent.case_id)
            .join(Review, Review.id == RaiEvent.review_id)
            .order_by(RaiEvent.created_at.desc())
        ).all()
        items = [
            RaiEventRead(
                id=event.id,
                review_id=event.review_id,
                case_id=event.case_id,
                case_code=case.case_code,
                verdict=review.verdict,
                failure_class=event.failure_class,
                explanation=event.explanation,
                record_kind="reviewed_lab_case",
                ai_snapshot_json=event.ai_snapshot_json or {},
                human_correction_json=event.human_correction_json or {},
                created_at=event.created_at,
            )
            for event, case, review in rows
        ]
        return RaiEventListResponse(items=items, total=len(items))


class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def submit(self, diagnosis_id: int, payload: ReviewCreate) -> Review:
        diagnosis = self.db.get(Diagnosis, diagnosis_id)
        if diagnosis is None:
            raise NotFoundError("Diagnosis %s was not found" % diagnosis_id)
        if diagnosis.status != DiagnosisStatus.PENDING_REVIEW.value:
            raise ConflictError("Diagnosis %s is not pending review" % diagnosis_id)
        existing = self.db.scalar(select(Review).where(Review.diagnosis_id == diagnosis.id))
        if existing is not None:
            raise ConflictError("Diagnosis %s already has a reviewer decision" % diagnosis_id)

        self._validate(diagnosis, payload)
        reviewer = get_or_create_reviewer(self.db, payload.reviewer_name)
        review = Review(
            diagnosis_id=diagnosis.id,
            reviewer_id=reviewer.id,
            verdict=payload.verdict.value,
            corrected_root_cause=payload.corrected_root_cause,
            corrected_osi_layer=payload.corrected_osi_layer.value if payload.corrected_osi_layer else None,
            corrected_concept_tag=payload.corrected_concept_tag.value if payload.corrected_concept_tag else None,
            corrected_fix_steps_json=payload.corrected_fix_steps,
            correction_reason=payload.correction_reason,
            override_ungrounded=payload.override_ungrounded,
        )
        self.db.add(review)
        self.db.flush()

        diagnosis.status = payload.verdict.value
        if payload.verdict in (ReviewVerdict.EDITED, ReviewVerdict.REJECTED):
            self._write_rai(diagnosis, review, payload)

        self.db.add(
            AuditEvent(
                actor_id=reviewer.id,
                action="review_%s" % payload.verdict.value,
                entity_type="diagnosis",
                entity_id=str(diagnosis.id),
                payload_json={
                    "review_id": review.id,
                    "verdict": payload.verdict.value,
                    "rai_written": payload.verdict != ReviewVerdict.ACCEPTED,
                },
            )
        )
        self.db.commit()
        self.db.refresh(review)
        return review

    def apply_fix(self, review_id: int, payload: ApplyFixCreate) -> Review:
        review = self.db.get(Review, review_id)
        if review is None:
            raise NotFoundError("Review %s was not found" % review_id)
        if review.verdict == "rejected":
            raise ConflictError("Rejected reviews cannot be marked as applied")
        if review.verdict not in {"accepted", "edited"}:
            raise ConflictError("Only accepted or edited reviews can be marked as applied")
        if review.fix_applied:
            raise ConflictError("Review %s is already marked as applied" % review_id)

        review.fix_applied = True
        review.fix_applied_by = payload.applied_by
        review.fix_applied_at = datetime.now(timezone.utc)
        self.db.add(
            AuditEvent(
                action="apply_fix",
                entity_type="review",
                entity_id=str(review.id),
                payload_json={"applied_by": payload.applied_by, "diagnosis_id": review.diagnosis_id},
            )
        )
        self.db.commit()
        self.db.refresh(review)
        return review

    def list_for_diagnosis(self, diagnosis_id: int) -> list[Review]:
        diagnosis = self.db.get(Diagnosis, diagnosis_id)
        if diagnosis is None:
            raise NotFoundError("Diagnosis %s was not found" % diagnosis_id)
        return list(
            self.db.scalars(
                select(Review).where(Review.diagnosis_id == diagnosis_id).order_by(Review.created_at.asc())
            ).all()
        )

    def to_detail(self, review: Review) -> ReviewDetail:
        diagnosis = review.diagnosis or self.db.get(Diagnosis, review.diagnosis_id)
        reviewer = review.reviewer or self.db.get(User, review.reviewer_id)
        rai = review.rai_event
        return ReviewDetail(
            **ReviewRead.model_validate(review).model_dump(),
            reviewer_name=reviewer.name if reviewer else "unknown",
            diagnosis_status=diagnosis.status if diagnosis else "",
            rai_event_id=rai.id if rai else None,
            original_ai=ai_snapshot(diagnosis) if diagnosis else {},
        )

    def _validate(self, diagnosis: Diagnosis, payload: ReviewCreate) -> None:
        if payload.verdict == ReviewVerdict.ACCEPTED and not diagnosis.grounded:
            if not payload.override_ungrounded:
                raise InvalidReviewError(
                    "Ungrounded diagnoses cannot be accepted without override_ungrounded and reviewer notes"
                )
            if not (payload.correction_reason or "").strip():
                raise InvalidReviewError("Accepting an ungrounded diagnosis requires reviewer notes")

    def _write_rai(self, diagnosis: Diagnosis, review: Review, payload: ReviewCreate) -> None:
        if payload.failure_class is None:
            raise InvalidReviewError("Edited and rejected reviews require a failure_class")
        event = RaiEvent(
            review_id=review.id,
            case_id=diagnosis.case_id,
            failure_class=payload.failure_class.value,
            ai_snapshot_json=ai_snapshot(diagnosis),
            human_correction_json=human_correction(payload),
            explanation=payload.correction_reason or "",
        )
        self.db.add(event)
