from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ops import RaiEventListResponse
from app.services.reviews import ReviewQueryService

router = APIRouter(prefix="/rai-events", tags=["responsible-ai"])


@router.get("", response_model=RaiEventListResponse)
def list_rai_events(db: Session = Depends(get_db)) -> RaiEventListResponse:
    return ReviewQueryService(db).rai_events()
