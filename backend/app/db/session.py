from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db.base import Base

settings = get_settings()

connect_args: dict[str, object] = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    db_path = settings.database_url.replace("sqlite:///", "", 1)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def session_scope() -> Session:
    return SessionLocal()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        _ensure_sqlite_columns()


def _ensure_sqlite_columns() -> None:
    _add_missing_columns(
        "diagnoses",
        {
            "severity": "ALTER TABLE diagnoses ADD COLUMN severity VARCHAR(16) NOT NULL DEFAULT 'medium'",
            "verification_command": "ALTER TABLE diagnoses ADD COLUMN verification_command TEXT NOT NULL DEFAULT ''",
        },
    )
    _add_missing_columns(
        "reviews",
        {
            "fix_applied": "ALTER TABLE reviews ADD COLUMN fix_applied BOOLEAN NOT NULL DEFAULT 0",
            "fix_applied_by": "ALTER TABLE reviews ADD COLUMN fix_applied_by VARCHAR(120)",
            "fix_applied_at": "ALTER TABLE reviews ADD COLUMN fix_applied_at DATETIME",
        },
    )


def _add_missing_columns(table: str, needed: dict[str, str]) -> None:
    from sqlalchemy import text

    with engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(%s)" % table)).fetchall()
        if not rows:
            return
        existing = {row[1] for row in rows}
        for name, ddl in needed.items():
            if name not in existing:
                conn.execute(text(ddl))
