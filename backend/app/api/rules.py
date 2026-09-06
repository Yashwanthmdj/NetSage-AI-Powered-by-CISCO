from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.related import RuleEvaluateRequest, RuleEvaluateResponse
from app.services.rule_runs import RuleRunService
from app.services.rules import evaluate

router = APIRouter(tags=["rules"])


@router.post("/rules/evaluate", response_model=RuleEvaluateResponse)
def evaluate_rules(payload: RuleEvaluateRequest) -> RuleEvaluateResponse:
    report = evaluate(payload.show_outputs, payload.topology_note)
    return RuleEvaluateResponse(
        results=report.results,
        fail_count=report.fail_count,
        pass_count=report.pass_count,
    )


@router.post("/cases/{case_id}/rules", response_model=RuleEvaluateResponse)
def evaluate_case_rules(case_id: int, db: Session = Depends(get_db)) -> RuleEvaluateResponse:
    case, run, report = RuleRunService(db).evaluate_case(case_id)
    return RuleEvaluateResponse(
        results=report.results,
        fail_count=report.fail_count,
        pass_count=report.pass_count,
        rule_run_id=run.id,
        case_id=case.id,
    )
