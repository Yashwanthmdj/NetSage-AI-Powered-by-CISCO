from __future__ import annotations

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.tables import Case, RuleRun
from app.services.rules import evaluate
from app.services.rules.result import RuleEngineReport


class RuleRunService:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_case(self, case_id: int, phase: str = "pre_ai") -> tuple[Case, RuleRun, RuleEngineReport]:
        case = self.db.get(Case, case_id)
        if case is None:
            raise NotFoundError("Case %s was not found" % case_id)
        report = evaluate(case.show_outputs, case.topology_note)
        run = RuleRun(
            case_id=case.id,
            diagnosis_id=None,
            phase=phase,
            findings_json=[item.model_dump() for item in report.results],
            error_count=report.fail_count,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return case, run, report
