from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import Case, Diagnosis, Review, Verification


def case_lifecycle_status(db: Session, case: Case) -> str:
    verification = db.scalar(
        select(Verification)
        .where(Verification.case_id == case.id)
        .order_by(Verification.created_at.desc())
    )
    if verification is not None:
        return "verified"

    diagnosis = db.scalar(
        select(Diagnosis)
        .where(Diagnosis.case_id == case.id)
        .order_by(Diagnosis.created_at.desc())
    )
    if diagnosis is None:
        return "imported"

    review = db.scalar(
        select(Review)
        .where(Review.diagnosis_id == diagnosis.id)
        .order_by(Review.created_at.desc())
    )
    if review is not None:
        if review.fix_applied:
            return "fix_applied"
        return review.verdict
    return diagnosis.status
