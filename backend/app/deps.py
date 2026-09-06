from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.analytics import AnalyticsService
from app.services.cases import CaseService
from app.services.reviews import ReviewQueryService


def db_session() -> Generator[Session, None, None]:
    yield from get_db()


def case_service(db: Session) -> CaseService:
    return CaseService(db)


def analytics_service(db: Session) -> AnalyticsService:
    return AnalyticsService(db)


def review_query_service(db: Session) -> ReviewQueryService:
    return ReviewQueryService(db)
