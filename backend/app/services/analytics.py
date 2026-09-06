from __future__ import annotations

from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.tables import Case, Diagnosis, RaiEvent, Review, RuleRun, Verification
from app.schemas.common import CoverageBucket
from app.schemas.ops import AnalyticsSummary, RateMetric


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def summary(self) -> AnalyticsSummary:
        cases = self.db.scalars(select(Case)).all()
        diagnoses = self.db.scalars(select(Diagnosis)).all()
        reviews = self.db.scalars(select(Review)).all()
        rai_events = self.db.scalars(select(RaiEvent)).all()
        verified_count = self.db.scalar(select(func.count()).select_from(Verification)) or 0
        rule_errors = self.db.scalar(select(func.coalesce(func.sum(RuleRun.error_count), 0))) or 0

        pending = sum(1 for item in diagnoses if item.status == "pending_review")
        accepted = sum(1 for item in reviews if item.verdict == "accepted")
        edited = sum(1 for item in reviews if item.verdict == "edited")
        rejected = sum(1 for item in reviews if item.verdict == "rejected")
        expected_true = sum(1 for item in diagnoses if item.expected_match is True)
        verifiable = accepted + edited
        verified = int(verified_count)
        unresolved = max(len(cases) - verified, 0)

        return AnalyticsSummary(
            case_count=len(cases),
            diagnosed_count=len(diagnoses),
            pending_review_count=pending,
            reviewed_count=len(reviews),
            accepted_count=accepted,
            edited_count=edited,
            rejected_count=rejected,
            unresolved_count=unresolved,
            verified_count=verified,
            rai_event_count=len(rai_events),
            rule_error_count=int(rule_errors),
            counts_by_concept=_buckets(row.concept_tag for row in cases),
            counts_by_severity=_buckets(row.severity for row in cases),
            review_verdicts=_buckets(row.verdict for row in reviews),
            rai_failure_classes=_buckets(row.failure_class for row in rai_events),
            ai_human_agreement=RateMetric(
                sample_size=len(reviews),
                value=(accepted / len(reviews)) if reviews else None,
            ),
            ai_expected_match=RateMetric(
                sample_size=len(diagnoses),
                value=(expected_true / len(diagnoses)) if diagnoses else None,
            ),
            verification_success=RateMetric(
                sample_size=verifiable,
                value=(verified / verifiable) if verifiable else None,
            ),
        )


def _buckets(values) -> list[CoverageBucket]:
    return [
        CoverageBucket(key=key, count=count)
        for key, count in sorted(Counter(values).items())
    ]
