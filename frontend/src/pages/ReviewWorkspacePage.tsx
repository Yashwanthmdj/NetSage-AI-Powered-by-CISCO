import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchCaseByCode } from "../api/cases";
import type { ReviewDetail, VerificationRead } from "../api/types";
import { DiagnosisCard, ReviewDecision } from "../components/DiagnosisCard";
import { EmptyState, ErrorState } from "../components/EmptyState";
import { Notice } from "../components/Notice";
import { ReviewForm } from "../components/ReviewForm";
import { PageSkeleton } from "../components/Skeleton";
import { PageHeader } from "../components/ui/PageHeader";
import { ApplyFixForm } from "../components/ApplyFixForm";
import { VerificationCard, VerifyForm } from "../components/VerifyForm";
import { useApi } from "../hooks/useApi";

export function ReviewWorkspacePage() {
  const { caseCode } = useParams();
  const { data, error, loading, reload } = useApi(() => fetchCaseByCode(caseCode ?? ""), [caseCode]);
  const [review, setReview] = useState<ReviewDetail | null>(null);
  const [verification, setVerification] = useState<VerificationRead | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  if (error) return <ErrorState message={error} />;
  if (loading || !data) return <PageSkeleton />;

  const diagnosis = data.latest_diagnosis;
  const shownReview = review ?? data.latest_review;
  const shownVerification = verification ?? data.latest_verification;
  const pending = diagnosis?.status === "pending_review" && !review;
  const canApplyFix = Boolean(
    shownReview && ["accepted", "edited"].includes(shownReview.verdict) && !shownReview.fix_applied && !shownVerification,
  );
  const canVerify = Boolean(shownReview?.fix_applied && !shownVerification);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Human review"
        title={data.case_code}
        description={data.title}
        actions={
          <Link to="/review" className="text-sm text-accent">
            Back to queue
          </Link>
        }
      />

      {data.lifecycle_status === "verified" && (
        <Notice tone="success">
          This case is verified. The accepted diagnosis, human review, and verification below are the official record.
        </Notice>
      )}
      {success && <Notice tone="success">{success}</Notice>}

      {!diagnosis && (
        <EmptyState
          title="This case has no diagnosis"
          body="Open Diagnosis or Troubleshooting and run the model first."
        />
      )}

      {diagnosis && <DiagnosisCard diagnosis={diagnosis} />}
      {diagnosis && pending && (
        <ReviewForm
          diagnosis={diagnosis}
          onSubmitted={(result) => {
            setReview(result);
            setSuccess(`Review recorded as ${result.verdict}. Original AI output was preserved.`);
            reload({ silent: true });
          }}
        />
      )}
      {shownReview && <ReviewDecision review={shownReview} />}
      {canApplyFix && shownReview && (
        <ApplyFixForm
          reviewId={shownReview.id}
          command={diagnosis?.verification_command}
          onApplied={(result) => {
            setReview(result);
            setSuccess("Fix marked as applied. Verification is now available.");
            reload({ silent: true });
          }}
        />
      )}
      {canVerify && (
        <VerifyForm
          caseId={data.id}
          command={diagnosis?.verification_command}
          onVerified={(row) => {
            setVerification(row);
            setSuccess("Fix verification saved.");
            reload({ silent: true });
          }}
        />
      )}
      {shownVerification && <VerificationCard verification={shownVerification} />}
    </div>
  );
}
