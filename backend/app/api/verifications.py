from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.related import VerificationCreate, VerificationRead
from app.services.verifications import VerificationService

router = APIRouter(tags=["verifications"])


@router.post("/cases/{case_id}/verifications", response_model=VerificationRead, status_code=201)
def create_verification(
    case_id: int,
    payload: VerificationCreate,
    db: Session = Depends(get_db),
) -> VerificationRead:
    row = VerificationService(db).submit(case_id, payload)
    return VerificationRead.model_validate(row)
