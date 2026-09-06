from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.models.tables import Case
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    db.execute(text("SELECT 1"))
    case_count = db.scalar(select(func.count()).select_from(Case)) or 0
    settings = get_settings()
    return HealthResponse(
        status="ok",
        database="ok",
        case_count=case_count,
        app=settings.app_name,
        llm_configured=bool(settings.llm_api_key.strip()),
    )
