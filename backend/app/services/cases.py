from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, NotFoundError
from app.models.enums import ConceptTag
from app.models.tables import Case, Diagnosis, Review, RuleRun, Verification
from app.schemas.case import (
    CaseCreate,
    CaseDetail,
    CaseImportResult,
    CaseListResponse,
    CaseSummary,
    CaseUpdate,
)
from app.schemas.common import CoverageBucket, DatasetCoverage, Pagination
from app.services.lifecycle import case_lifecycle_status


class CaseService:
    def __init__(self, db: Session):
        self.db = db

    def _get_or_404(self, case_id: int) -> Case:
        case = self.db.get(Case, case_id)
        if case is None:
            raise NotFoundError(f"Case {case_id} was not found")
        return case

    def get_by_code(self, case_code: str) -> Case:
        case = self.db.scalar(select(Case).where(Case.case_code == case_code))
        if case is None:
            raise NotFoundError(f"Case {case_code} was not found")
        return case

    def _summary(self, case: Case) -> CaseSummary:
        return CaseSummary(
            id=case.id,
            case_code=case.case_code,
            title=case.title,
            osi_layer=case.osi_layer,
            concept_tag=case.concept_tag,
            severity=case.severity,
            source=case.source,
            lifecycle_status=case_lifecycle_status(self.db, case),
            created_at=case.created_at,
            updated_at=case.updated_at,
        )

    def _detail(self, case: Case) -> CaseDetail:
        latest_rule = self.db.scalar(
            select(RuleRun)
            .where(RuleRun.case_id == case.id)
            .order_by(RuleRun.created_at.desc())
        )
        latest_diagnosis, latest_review, latest_verification = self._primary_diagnosis(case)
        return CaseDetail(
            **self._summary(case).model_dump(),
            symptom=case.symptom,
            topology_note=case.topology_note,
            show_outputs=case.show_outputs,
            expected_fault=case.expected_fault,
            latest_rule_run=latest_rule,
            latest_diagnosis=latest_diagnosis,
            latest_review=latest_review,
            latest_verification=latest_verification,
        )

    def _primary_diagnosis(
        self, case: Case
    ) -> tuple[Diagnosis | None, Review | None, Verification | None]:
        verification = self.db.scalar(
            select(Verification)
            .where(Verification.case_id == case.id)
            .order_by(Verification.created_at.desc())
        )
        if verification is not None:
            review = self.db.get(Review, verification.review_id)
            diagnosis = self.db.get(Diagnosis, review.diagnosis_id) if review is not None else None
            return diagnosis, review, verification

        diagnosis = self.db.scalar(
            select(Diagnosis)
            .where(Diagnosis.case_id == case.id)
            .order_by(Diagnosis.created_at.desc())
        )
        review = None
        if diagnosis is not None:
            review = self.db.scalar(
                select(Review)
                .where(Review.diagnosis_id == diagnosis.id)
                .order_by(Review.created_at.desc())
            )
        return diagnosis, review, None

    def list_cases(
        self,
        *,
        concept_tag: str | None = None,
        severity: str | None = None,
        osi_layer: str | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> CaseListResponse:
        stmt = select(Case)
        if concept_tag:
            stmt = stmt.where(Case.concept_tag == concept_tag)
        if severity:
            stmt = stmt.where(Case.severity == severity)
        if osi_layer:
            stmt = stmt.where(Case.osi_layer == osi_layer)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Case.case_code.ilike(like),
                    Case.title.ilike(like),
                    Case.symptom.ilike(like),
                    Case.expected_fault.ilike(like),
                )
            )

        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self.db.scalars(
            stmt.order_by(Case.case_code).limit(limit).offset(offset)
        ).all()
        return CaseListResponse(
            items=[self._summary(row) for row in rows],
            pagination=Pagination(total=total, limit=limit, offset=offset),
        )

    def get_case(self, case_id: int) -> CaseDetail:
        return self._detail(self._get_or_404(case_id))

    def get_case_by_code(self, case_code: str) -> CaseDetail:
        return self._detail(self.get_by_code(case_code))

    def create_case(self, payload: CaseCreate) -> CaseDetail:
        existing = self.db.scalar(select(Case).where(Case.case_code == payload.case_code))
        if existing is not None:
            raise ConflictError(f"Case {payload.case_code} already exists")
        case = Case(**payload.model_dump(mode="json"))
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return self._detail(case)

    def update_case(self, case_id: int, payload: CaseUpdate) -> CaseDetail:
        case = self._get_or_404(case_id)
        updates = payload.model_dump(exclude_unset=True, mode="json")
        for key, value in updates.items():
            setattr(case, key, value)
        case.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(case)
        return self._detail(case)

    def upsert_record(self, payload: CaseCreate) -> str:
        existing = self.db.scalar(select(Case).where(Case.case_code == payload.case_code))
        data = payload.model_dump(mode="json")
        if existing is None:
            self.db.add(Case(**data))
            return "created"
        for key, value in data.items():
            if key != "case_code":
                setattr(existing, key, value)
        existing.updated_at = datetime.now(timezone.utc)
        return "updated"

    def import_records(self, records: list[CaseCreate]) -> CaseImportResult:
        created = updated = skipped = 0
        errors: list[str] = []
        for record in records:
            try:
                action = self.upsert_record(record)
                if action == "created":
                    created += 1
                else:
                    updated += 1
            except Exception as exc:  # noqa: BLE001 - collect row errors for import report
                skipped += 1
                errors.append(f"{record.case_code}: {exc}")
        self.db.commit()
        return CaseImportResult(created=created, updated=updated, skipped=skipped, errors=errors)

    def coverage(self) -> DatasetCoverage:
        rows = self.db.scalars(select(Case)).all()
        concepts = Counter(row.concept_tag for row in rows)
        layers = Counter(row.osi_layer for row in rows)
        severities = Counter(row.severity for row in rows)
        present = set(concepts)
        missing = [tag for tag in ConceptTag if tag.value not in present]
        return DatasetCoverage(
            case_count=len(rows),
            concepts=[CoverageBucket(key=key, count=count) for key, count in sorted(concepts.items())],
            osi_layers=[CoverageBucket(key=key, count=count) for key, count in sorted(layers.items())],
            severities=[
                CoverageBucket(key=key, count=count) for key, count in sorted(severities.items())
            ],
            missing_concepts=missing,
            meets_coverage_gate=len(rows) >= 30 and not missing,
        )
