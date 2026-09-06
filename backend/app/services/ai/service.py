from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.exceptions import ConflictError, NotFoundError
from app.models.enums import DiagnosisStatus
from app.models.tables import Case, Diagnosis, PromptVersion, RuleRun
from app.services.ai.client import LlmClient, OpenAICompatibleClient
from app.services.ai.expected_match import expected_match
from app.services.ai.grounding import ungrounded_quotes
from app.services.ai.parse import parse_diagnosis_json
from app.services.ai.prompt_loader import system_prompt
from app.services.ai.schema import DiagnosisOutput
from app.services.ai.user_message import build_user_message
from app.services.rule_runs import RuleRunService
from app.services.rules.result import RuleEngineReport


class DiagnosisService:
    def __init__(self, db: Session, llm: LlmClient | None = None):
        self.db = db
        self.llm = llm or OpenAICompatibleClient()

    def diagnose(self, case_id: int) -> Diagnosis:
        case = self.db.get(Case, case_id)
        if case is None:
            raise NotFoundError("Case %s was not found" % case_id)
        pending = self.db.scalar(
            select(Diagnosis).where(
                Diagnosis.case_id == case.id,
                Diagnosis.status == DiagnosisStatus.PENDING_REVIEW.value,
            )
        )
        if pending is not None:
            raise ConflictError("Case %s already has a diagnosis pending review" % case.case_code)

        ensure = getattr(self.llm, "ensure_ready", None)
        if callable(ensure):
            ensure()

        _case, rule_run, report = RuleRunService(self.db).evaluate_case(case.id, phase="pre_ai")
        system, digest, path = system_prompt()
        prompt_row = self._prompt_version(digest, path, system)
        user = build_user_message(case, report.results)
        raw = self.llm.complete_json(system, user)
        output = parse_diagnosis_json(raw)
        missing = ungrounded_quotes(output, case.show_outputs)
        row = self._persist(case, prompt_row, output, raw, missing, report)
        rule_run.diagnosis_id = row.id
        self.db.add(rule_run)
        self._store_post_ai_rules(case, row, report)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get(self, diagnosis_id: int) -> Diagnosis:
        row = self.db.get(Diagnosis, diagnosis_id)
        if row is None:
            raise NotFoundError("Diagnosis %s was not found" % diagnosis_id)
        return row

    def _prompt_version(self, digest: str, path, body: str) -> PromptVersion:
        existing = self.db.scalar(select(PromptVersion).where(PromptVersion.content_hash == digest))
        if existing is not None:
            return existing
        row = PromptVersion(
            name="diagnose_prompt",
            version=digest[:12],
            file_path=str(path),
            content_hash=digest,
            body=body,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def _persist(
        self,
        case: Case,
        prompt_row: PromptVersion,
        output: DiagnosisOutput,
        raw: str,
        missing,
        report: RuleEngineReport,
    ) -> Diagnosis:
        settings = get_settings()
        row = Diagnosis(
            case_id=case.id,
            prompt_version_id=prompt_row.id,
            model_name=settings.llm_model,
            root_cause=output.root_cause,
            osi_layer=output.osi_layer.value,
            concept_tag=output.concept_tag.value,
            confidence=output.confidence,
            confidence_label=output.confidence_label.value,
            evidence_json=[item.model_dump() for item in output.evidence],
            next_commands_json=output.next_commands,
            fix_steps_json=output.fix_steps,
            severity=output.severity.value,
            verification_command=output.verification_command,
            raw_response=raw,
            grounded=len(missing) == 0,
            expected_match=expected_match(case.expected_fault, case.concept_tag, output),
            status=DiagnosisStatus.PENDING_REVIEW.value,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def _store_post_ai_rules(self, case: Case, diagnosis: Diagnosis, report: RuleEngineReport) -> None:
        # Same deterministic facts, stored after diagnosis for the audit trail.
        run = RuleRun(
            case_id=case.id,
            diagnosis_id=diagnosis.id,
            phase="post_ai",
            findings_json=[item.model_dump() for item in report.results],
            error_count=report.fail_count,
        )
        self.db.add(run)
