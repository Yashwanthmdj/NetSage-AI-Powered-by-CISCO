from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.tables import User

DEFAULT_REVIEWER_NAME = "Lab Reviewer"
_UNUSED_PASSWORD_HASH = "local-unused"


def get_or_create_reviewer(db: Session, name: str | None = None) -> User:
    cleaned = (name or DEFAULT_REVIEWER_NAME).strip() or DEFAULT_REVIEWER_NAME
    existing = db.scalar(select(User).where(User.name == cleaned))
    if existing is not None:
        return existing
    user = User(
        name=cleaned,
        role=UserRole.REVIEWER.value,
        password_hash=_UNUSED_PASSWORD_HASH,
    )
    db.add(user)
    db.flush()
    return user


def seed_default_reviewer(db: Session) -> User:
    user = get_or_create_reviewer(db, DEFAULT_REVIEWER_NAME)
    db.commit()
    return user
