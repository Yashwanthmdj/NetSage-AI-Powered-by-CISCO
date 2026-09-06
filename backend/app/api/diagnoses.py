from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.related import DiagnosisDetail
from app.services.ai.grounding import quote_is_grounded
from app.services.ai.service import DiagnosisService

router = APIRouter(tags=["diagnoses"])


def _service(db: Session = Depends(get_db)) -> DiagnosisService:
    return DiagnosisService(db)


def _to_detail(row, show_outputs: str | None = None) -> DiagnosisDetail:
    next_command = row.next_commands_json[0] if row.next_commands_json else None
    ungrounded: list[str] = []
    if show_outputs:
        for item in row.evidence_json or []:
            quote = item.get("quote") if isinstance(item, dict) else None
            if quote and not quote_is_grounded(str(quote), show_outputs):
                ungrounded.append(str(quote))
    return DiagnosisDetail.model_validate(row).model_copy(
        update={"ungrounded_quotes": ungrounded, "next_command": next_command}
    )


@router.post("/cases/{case_id}/diagnoses", response_model=DiagnosisDetail)
def create_diagnosis(case_id: int, service: DiagnosisService = Depends(_service)) -> DiagnosisDetail:
    row = service.diagnose(case_id)
    return _to_detail(row, row.case.show_outputs if row.case else None)


@router.get("/diagnoses/{diagnosis_id}", response_model=DiagnosisDetail)
def get_diagnosis(diagnosis_id: int, service: DiagnosisService = Depends(_service)) -> DiagnosisDetail:
    row = service.get(diagnosis_id)
    show_outputs = row.case.show_outputs if row.case else None
    return _to_detail(row, show_outputs)
