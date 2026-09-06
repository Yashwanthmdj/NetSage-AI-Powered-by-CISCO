import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchCaseByCode } from "../api/cases";
import type { ReviewDetail, VerificationRead } from "../api/types";
import { ConceptBadge, SeverityBadge, StatusBadge } from "../components/Badge";
import { DiagnosisCard, ReviewDecision } from "../components/DiagnosisCard";
import { ErrorState } from "../components/EmptyState";
import { Notice } from "../components/Notice";
import { ReviewForm } from "../components/ReviewForm";
import { reportFromRun, RuleResults } from "../components/RuleResults";
import { PageSkeleton } from "../components/Skeleton";
import { ApplyFixForm } from "../components/ApplyFixForm";
import { VerificationCard, VerifyForm } from "../components/VerifyForm";
import { DiagnoseButton } from "../components/DiagnoseButton";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { useApi } from "../hooks/useApi";
import { useCaseActions } from "../hooks/useCaseActions";
import { lifecycleTone } from "../lib/status";

export function CaseDetailPage() {
  const { caseCode } = useParams();
  const { data, error, loading, reload } = useApi(() => fetchCaseByCode(caseCode ?? ""), [caseCode]);
  const actions = useCaseActions();
  const [review, setReview] = useState<ReviewDetail | null>(null);
  const [verification, setVerification] = useState<VerificationRead | null>(null);
  const [verifySuccess, setVerifySuccess] = useState<string | null>(null);

  if (error) return <ErrorState message={error} />;
  if (loading || !data) return <PageSkeleton />;

  const verified = data.lifecycle_status === "verified";
  const shownDiagnosis = verified ? data.latest_diagnosis : (actions.diagnosis ?? data.latest_diagnosis);
  const shownReview = review ?? data.latest_review;
  const shownVerification = verification ?? data.latest_verification;
  const pending = !verified && shownDiagnosis?.status === "pending_review" && !shownReview;
  const shownReport = actions.report ?? (data.latest_rule_run ? reportFromRun(data.latest_rule_run) : null);
  const canApplyFix = Boolean(
    shownReview && ["accepted", "edited"].includes(shownReview.verdict) && !shownReview.fix_applied && !shownVerification,
  );
  const canVerify = Boolean(shownReview?.fix_applied && !shownVerification);

  return (
    <div className="space-y-6">
      <div>
        <Link to="/cases" className="text-sm text-accent">
          Back to cases
        </Link>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <h2 className="font-mono text-2xl text-accent">{data.case_code}</h2>
          <ConceptBadge value={data.concept_tag} />
          <SeverityBadge value={data.severity} />
          <StatusBadge value={data.lifecycle_status} tone={lifecycleTone(data.lifecycle_status)} />
          <Button
            onClick={async () => {
              await actions.onRunRules(data.id);
              reload({ silent: true });
            }}
            disabled={actions.running}
          >
            {actions.running ? "Checking…" : "Run rule engine"}
          </Button>
          <DiagnoseButton
            verified={verified}
            pending={pending}
            diagnosing={actions.diagnosing}
            onDiagnose={async () => {
              await actions.onDiagnose(data.id);
              reload({ silent: true });
            }}
          />
          <Link to={`/troubleshoot?case=${data.case_code}`} className="text-sm text-mist hover:text-accent">
            Open workbench
          </Link>
        </div>
        <p className="mt-2 text-lg text-snow">{data.title}</p>
      </div>

      <section className="grid gap-4 md:grid-cols-2">
        <Card title="Symptom">
          <p className="text-sm leading-6">{data.symptom}</p>
        </Card>
        <Card title="Topology notes">
          <p className="text-sm leading-6">{data.topology_note}</p>
        </Card>
      </section>

      {verified && (
        <Notice tone="success">
          This case is verified. The accepted diagnosis, human review, and verification below are the official record.
        </Notice>
      )}

      <Card title="Expected fault">
        <p className="text-sm leading-6">{data.expected_fault}</p>
      </Card>

      {actions.ruleError && <ErrorState message={actions.ruleError} />}
      {actions.ruleSuccess && <Notice tone="success">{actions.ruleSuccess}</Notice>}
      {actions.diagnoseError && <ErrorState message={actions.diagnoseError} />}
      {actions.diagnoseSuccess && <Notice tone="success">{actions.diagnoseSuccess}</Notice>}

      {shownReport && <RuleResults report={shownReport} />}
      {shownDiagnosis && <DiagnosisCard diagnosis={shownDiagnosis} />}
      {shownDiagnosis && pending && (
        <ReviewForm
          diagnosis={shownDiagnosis}
          onSubmitted={(result) => {
            setReview(result);
            if (actions.diagnosis) {
              actions.setDiagnosis({ ...actions.diagnosis, status: result.verdict });
            }
            reload({ silent: true });
          }}
        />
      )}
      {shownReview && <ReviewDecision review={shownReview} />}
      {verifySuccess && <Notice tone="success">{verifySuccess}</Notice>}
      {canApplyFix && shownReview && (
        <ApplyFixForm
          reviewId={shownReview.id}
          command={shownDiagnosis?.verification_command}
          onApplied={(result) => {
            setReview(result);
            setVerifySuccess("Fix marked as applied. Verification is now available.");
            reload({ silent: true });
          }}
        />
      )}
      {canVerify && (
        <VerifyForm
          caseId={data.id}
          command={shownDiagnosis?.verification_command}
          onVerified={(row) => {
            setVerification(row);
            setVerifySuccess("Fix verification saved. Case lifecycle is now verified.");
            reload({ silent: true });
          }}
        />
      )}
      {shownVerification && <VerificationCard verification={shownVerification} />}

      <Card title="Show-command evidence" className="bg-ink/60">
        <pre className="evidence text-[13px] leading-6 text-snow/85">{data.show_outputs}</pre>
      </Card>
    </div>
  );
}
