from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, NotFoundError
from app.models.tables import AuditEvent, Case, Diagnosis, Review, Verification
from app.schemas.related import VerificationCreate


class VerificationService:
    def __init__(self, db: Session):
        self.db = db

    def submit(self, case_id: int, payload: VerificationCreate) -> Verification:
        case = self.db.get(Case, case_id)
        if case is None:
            raise NotFoundError("Case %s was not found" % case_id)

        diagnosis = self.db.scalar(
            select(Diagnosis).where(Diagnosis.case_id == case.id).order_by(Diagnosis.created_at.desc())
        )
        if diagnosis is None:
            raise ConflictError("Case %s has no diagnosis to verify" % case.case_code)

        review = self.db.scalar(
            select(Review)
            .where(Review.diagnosis_id == diagnosis.id)
            .order_by(Review.created_at.desc())
        )
        if review is None:
            raise ConflictError("Diagnosis must be reviewed before verification")
        if review.verdict == "rejected":
            raise ConflictError("Rejected diagnoses cannot be marked verified")
        if review.verdict not in {"accepted", "edited"}:
            raise ConflictError("Only accepted or edited reviews can be verified")
        if not review.fix_applied:
            raise ConflictError("Mark the recommended fix as applied before verification")

        existing = self.db.scalar(select(Verification).where(Verification.review_id == review.id))
        if existing is not None:
            raise ConflictError("This review is already verified")

        row = Verification(
            case_id=case.id,
            review_id=review.id,
            verified_by=payload.verified_by,
            notes=payload.notes,
        )
        self.db.add(row)
        self.db.flush()
        self.db.add(
            AuditEvent(
                action="verify_fix",
                entity_type="case",
                entity_id=str(case.id),
                payload_json={
                    "verification_id": row.id,
                    "review_id": review.id,
                    "diagnosis_id": diagnosis.id,
                    "verified_by": payload.verified_by,
                },
            )
        )
        self.db.commit()
        self.db.refresh(row)
        return row
