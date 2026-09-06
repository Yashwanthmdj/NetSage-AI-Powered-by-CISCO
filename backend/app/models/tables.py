from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    reviews: Mapped[List["Review"]] = relationship(back_populates="reviewer")
    audit_events: Mapped[List["AuditEvent"]] = relationship(back_populates="actor")


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    symptom: Mapped[str] = mapped_column(Text, nullable=False)
    topology_note: Mapped[str] = mapped_column(Text, nullable=False)
    show_outputs: Mapped[str] = mapped_column(Text, nullable=False)
    expected_fault: Mapped[str] = mapped_column(Text, nullable=False)
    osi_layer: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    concept_tag: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="packet_tracer")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    diagnoses: Mapped[List["Diagnosis"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    rule_runs: Mapped[List["RuleRun"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    rai_events: Mapped[List["RaiEvent"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    verifications: Mapped[List["Verification"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    diagnoses: Mapped[List["Diagnosis"]] = relationship(back_populates="prompt_version")

    __table_args__ = (UniqueConstraint("name", "version", name="uq_prompt_name_version"),)


class Diagnosis(Base):
    __tablename__ = "diagnoses"
    __table_args__ = (
        Index(
            "uq_diagnoses_one_pending_per_case",
            "case_id",
            unique=True,
            sqlite_where=text("status = 'pending_review'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    prompt_version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("prompt_versions.id", ondelete="SET NULL")
    )
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    osi_layer: Mapped[str] = mapped_column(String(8), nullable=False)
    concept_tag: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_label: Mapped[str] = mapped_column(String(16), nullable=False)
    evidence_json: Mapped[List] = mapped_column(JSON, nullable=False, default=list)
    next_commands_json: Mapped[List] = mapped_column(JSON, nullable=False, default=list)
    fix_steps_json: Mapped[List] = mapped_column(JSON, nullable=False, default=list)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    verification_command: Mapped[str] = mapped_column(Text, nullable=False, default="")
    raw_response: Mapped[str] = mapped_column(Text, nullable=False)
    grounded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expected_match: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    case: Mapped[Case] = relationship(back_populates="diagnoses")
    prompt_version: Mapped[Optional["PromptVersion"]] = relationship(back_populates="diagnoses")
    reviews: Mapped[List["Review"]] = relationship(
        back_populates="diagnosis", cascade="all, delete-orphan"
    )
    rule_runs: Mapped[List["RuleRun"]] = relationship(back_populates="diagnosis")


class RuleRun(Base):
    __tablename__ = "rule_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    diagnosis_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("diagnoses.id", ondelete="SET NULL")
    )
    phase: Mapped[str] = mapped_column(String(16), nullable=False)
    findings_json: Mapped[List] = mapped_column(JSON, nullable=False, default=list)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    case: Mapped[Case] = relationship(back_populates="rule_runs")
    diagnosis: Mapped[Optional["Diagnosis"]] = relationship(back_populates="rule_runs")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    diagnosis_id: Mapped[int] = mapped_column(
        ForeignKey("diagnoses.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    verdict: Mapped[str] = mapped_column(String(16), nullable=False)
    corrected_root_cause: Mapped[Optional[str]] = mapped_column(Text)
    corrected_osi_layer: Mapped[Optional[str]] = mapped_column(String(8))
    corrected_concept_tag: Mapped[Optional[str]] = mapped_column(String(32))
    corrected_fix_steps_json: Mapped[Optional[List]] = mapped_column(JSON)
    correction_reason: Mapped[Optional[str]] = mapped_column(Text)
    override_ungrounded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fix_applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fix_applied_by: Mapped[Optional[str]] = mapped_column(String(120))
    fix_applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    diagnosis: Mapped[Diagnosis] = relationship(back_populates="reviews")
    reviewer: Mapped[User] = relationship(back_populates="reviews")
    rai_event: Mapped[Optional["RaiEvent"]] = relationship(
        back_populates="review", uselist=False, cascade="all, delete-orphan"
    )
    verification: Mapped[Optional["Verification"]] = relationship(
        back_populates="review", uselist=False
    )


class RaiEvent(Base):
    __tablename__ = "rai_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    review_id: Mapped[int] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    failure_class: Mapped[str] = mapped_column(String(64), nullable=False)
    ai_snapshot_json: Mapped[Dict] = mapped_column(JSON, nullable=False, default=dict)
    human_correction_json: Mapped[Dict] = mapped_column(JSON, nullable=False, default=dict)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    review: Mapped[Review] = relationship(back_populates="rai_event")
    case: Mapped[Case] = relationship(back_populates="rai_events")


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    review_id: Mapped[int] = mapped_column(
        ForeignKey("reviews.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    verified_by: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    case: Mapped[Case] = relationship(back_populates="verifications")
    review: Mapped[Review] = relationship(back_populates="verification")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[Dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    actor: Mapped[Optional["User"]] = relationship(back_populates="audit_events")
