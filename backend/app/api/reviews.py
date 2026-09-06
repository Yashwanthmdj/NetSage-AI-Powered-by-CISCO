from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ops import ReviewQueueResponse
from app.schemas.related import ApplyFixCreate, ReviewCreate, ReviewDetail
from app.services.reviews import ReviewQueryService, ReviewService

router = APIRouter(tags=["reviews"])


@router.get("/reviews/queue", response_model=ReviewQueueResponse)
def review_queue(db: Session = Depends(get_db)) -> ReviewQueueResponse:
    return ReviewQueryService(db).queue()


@router.post("/diagnoses/{diagnosis_id}/reviews", response_model=ReviewDetail)
def create_review(
    diagnosis_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
) -> ReviewDetail:
    service = ReviewService(db)
    review = service.submit(diagnosis_id, payload)
    return service.to_detail(review)


@router.get("/diagnoses/{diagnosis_id}/reviews", response_model=list[ReviewDetail])
def list_reviews(diagnosis_id: int, db: Session = Depends(get_db)) -> list[ReviewDetail]:
    service = ReviewService(db)
    return [service.to_detail(row) for row in service.list_for_diagnosis(diagnosis_id)]


@router.post("/reviews/{review_id}/apply-fix", response_model=ReviewDetail)
def apply_fix(
    review_id: int,
    payload: ApplyFixCreate,
    db: Session = Depends(get_db),
) -> ReviewDetail:
    service = ReviewService(db)
    review = service.apply_fix(review_id, payload)
    return service.to_detail(review)
