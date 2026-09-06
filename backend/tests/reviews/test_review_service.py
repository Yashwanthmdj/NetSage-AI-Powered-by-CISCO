from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.exceptions import ConflictError, InvalidReviewError
from app.models.tables import Case, Diagnosis, RaiEvent, Review
from app.schemas.related import ReviewCreate
from app.services.reviews import ReviewService
from app.services.seed import catalog_payloads

RAW_AI = '{"root_cause":"VLAN 30 is missing","concept_tag":"vlan"}'


def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    return TestingSession()


def _pending(db, *, grounded: bool = True) -> Diagnosis:
    payload = next(item for item in catalog_payloads() if item.case_code == "VLAN-001")
    case = Case(**payload.model_dump(mode="json"))
    db.add(case)
    db.flush()
    row = Diagnosis(
        case_id=case.id,
        model_name="test-model",
        root_cause="VLAN 30 is missing from the VLAN database.",
        osi_layer="L2",
        concept_tag="vlan",
        confidence=0.84,
        confidence_label="high",
        evidence_json=[{"quote": "Access Mode VLAN: 30 (Inactive)", "command": "show", "why": "inactive"}],
        next_commands_json=["show vlan brief"],
        fix_steps_json=["Create VLAN 30."],
        severity="high",
        verification_command="ping 192.168.30.10",
        raw_response=RAW_AI,
        grounded=grounded,
        expected_match=True,
        status="pending_review",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_accept_preserves_original_ai_and_skips_rai() -> None:
    db = _session()
    diagnosis = _pending(db)
    review = ReviewService(db).submit(
        diagnosis.id,
        ReviewCreate(verdict="accepted", reviewer_name="Ada"),
    )
    db.refresh(diagnosis)
    assert review.verdict == "accepted"
    assert diagnosis.status == "accepted"
    assert diagnosis.raw_response == RAW_AI
    assert diagnosis.root_cause.startswith("VLAN 30")
    assert db.scalar(select(RaiEvent)) is None
    detail = ReviewService(db).to_detail(review)
    assert detail.reviewer_name == "Ada"
    assert detail.original_ai["raw_response"] == RAW_AI
    assert detail.rai_event_id is None


def test_edit_writes_corrections_and_rai_event() -> None:
    db = _session()
    diagnosis = _pending(db)
    original = diagnosis.root_cause
    review = ReviewService(db).submit(
        diagnosis.id,
        ReviewCreate(
            verdict="edited",
            reviewer_name="Ada",
            correction_reason="VLAN is present; the access port is in the wrong VLAN.",
            corrected_root_cause="Fa0/24 is in VLAN 10 instead of VLAN 30.",
            corrected_osi_layer="L2",
            corrected_concept_tag="vlan",
            corrected_fix_steps=["Move Fa0/24 to VLAN 30."],
            failure_class="wrong_concept",
        ),
    )
    db.refresh(diagnosis)
    assert diagnosis.status == "edited"
    assert diagnosis.root_cause == original
    assert review.corrected_root_cause.startswith("Fa0/24")
    assert review.correction_reason.startswith("VLAN is present")
    event = db.scalar(select(RaiEvent))
    assert event is not None
    assert event.review_id == review.id
    assert event.failure_class == "wrong_concept"
    assert event.ai_snapshot_json["raw_response"] == RAW_AI
    assert event.human_correction_json["corrected_root_cause"].startswith("Fa0/24")
    assert event.explanation.startswith("VLAN is present")


def test_reject_writes_rai_and_clears_pending_gate() -> None:
    db = _session()
    diagnosis = _pending(db)
    ReviewService(db).submit(
        diagnosis.id,
        ReviewCreate(
            verdict="rejected",
            correction_reason="Evidence does not support a VLAN fault.",
            failure_class="hallucinated_evidence",
        ),
    )
    db.refresh(diagnosis)
    assert diagnosis.status == "rejected"
    assert db.scalar(select(RaiEvent)) is not None
    pending = db.scalar(select(Diagnosis).where(Diagnosis.status == "pending_review"))
    assert pending is None


def test_ungrounded_accept_requires_override_and_notes() -> None:
    db = _session()
    diagnosis = _pending(db, grounded=False)
    try:
        ReviewService(db).submit(diagnosis.id, ReviewCreate(verdict="accepted"))
        assert False, "expected InvalidReviewError"
    except InvalidReviewError as exc:
        assert exc.status_code == 422
    ReviewService(db).submit(
        diagnosis.id,
        ReviewCreate(
            verdict="accepted",
            override_ungrounded=True,
            correction_reason="Quote is close enough after whitespace normalize.",
        ),
    )
    db.refresh(diagnosis)
    assert diagnosis.status == "accepted"
    assert db.scalar(select(RaiEvent)) is None


def test_cannot_review_twice() -> None:
    db = _session()
    diagnosis = _pending(db)
    ReviewService(db).submit(diagnosis.id, ReviewCreate(verdict="accepted"))
    try:
        ReviewService(db).submit(diagnosis.id, ReviewCreate(verdict="rejected", correction_reason="no", failure_class="incomplete_fix"))
        assert False, "expected ConflictError"
    except ConflictError as exc:
        assert exc.status_code == 409
    assert db.scalars(select(Review)).all().__len__() == 1
