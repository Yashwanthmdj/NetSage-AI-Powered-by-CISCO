import { useState } from "react";
import { Link } from "react-router-dom";
import { fetchCaseByCode, fetchCases } from "../api/cases";
import { fetchReviewQueue } from "../api/ops";
import { CasePicker } from "../components/CasePicker";
import { DiagnosisCard } from "../components/DiagnosisCard";
import { EmptyState, ErrorState } from "../components/EmptyState";
import { Notice } from "../components/Notice";
import { StatusBadge } from "../components/Badge";
import { PageSkeleton } from "../components/Skeleton";
import { DiagnoseButton } from "../components/DiagnoseButton";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { useApi } from "../hooks/useApi";
import { useCaseActions } from "../hooks/useCaseActions";
import { formatWhen } from "../lib/status";

export function DiagnosisPage() {
  const catalog = useApi(() => fetchCases({ limit: "100" }));
  const queue = useApi(fetchReviewQueue);
  const [caseCode, setCaseCode] = useState("");
  const selected = useApi(() => (caseCode ? fetchCaseByCode(caseCode) : Promise.resolve(null)), [caseCode]);
  const actions = useCaseActions();
  const verified = selected.data?.lifecycle_status === "verified";
  const shown = verified
    ? selected.data?.latest_diagnosis ?? null
    : actions.diagnosis ?? selected.data?.latest_diagnosis ?? null;
  const pending = !verified && shown?.status === "pending_review";

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="AI"
        title="Diagnosis"
        description="Request a structured diagnosis from the model. Results stay pending until a reviewer accepts, edits, or rejects them. Nothing is invented if the LLM is down."
        actions={
          <CasePicker
            cases={catalog.data?.items ?? []}
            value={caseCode}
            onChange={(value) => {
              setCaseCode(value);
              actions.setDiagnosis(null);
            }}
          />
        }
      />

      {catalog.error && <ErrorState message={catalog.error} />}
      {queue.error && <ErrorState message={queue.error} />}
      {queue.loading && <PageSkeleton />}

      <Card
        title="Pending diagnoses"
        description="Live review-queue items from the API."
        actions={
          <Link to="/review" className="text-sm text-accent">
            Review workspace
          </Link>
        }
      >
        {queue.data && queue.data.total === 0 && (
          <EmptyState
            title="No pending diagnoses"
            body="Select a case and run Diagnose with AI. The model output is only stored after schema validation."
          />
        )}
        {queue.data && queue.data.total > 0 && (
          <div className="space-y-2">
            {queue.data.items.map((item) => (
              <Link
                key={item.diagnosis_id}
                to={`/review/${item.case_code}`}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line bg-ink/40 px-3 py-2.5 transition hover:border-accent/40"
              >
                <div>
                  <p className="font-mono text-sm text-accent">{item.case_code}</p>
                  <p className="text-sm text-snow">{item.title}</p>
                  <p className="text-xs text-mist">{formatWhen(item.created_at)}</p>
                </div>
                <StatusBadge value={item.status} tone="warn" />
              </Link>
            ))}
          </div>
        )}
      </Card>

      {selected.error && <ErrorState message={selected.error} />}
      {caseCode && selected.loading && <p className="text-sm text-mist">Loading case…</p>}

      {selected.data && (
        <Card
          title={selected.data.case_code}
          description={selected.data.title}
          actions={
            <DiagnoseButton
              verified={verified}
              pending={pending}
              diagnosing={actions.diagnosing}
              variant="primary"
              onDiagnose={() => actions.onDiagnose(selected.data!.id)}
            />
          }
        >
          {verified && (
            <p className="mb-3 text-sm leading-6 text-accent">
              This case is verified. The accepted diagnosis below is the official record.
            </p>
          )}
          <p className="text-sm leading-6 text-mist">{selected.data.symptom}</p>
        </Card>
      )}

      {actions.diagnoseError && <ErrorState message={actions.diagnoseError} />}
      {actions.diagnoseSuccess && <Notice tone="success">{actions.diagnoseSuccess}</Notice>}
      {shown && <DiagnosisCard diagnosis={shown} />}
    </div>
  );
}
