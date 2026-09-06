import { Activity, Brain, CheckCircle2, FolderOpen, Scale, ShieldCheck, TriangleAlert } from "lucide-react";
import { Link } from "react-router-dom";
import { fetchCases, fetchCoverage, fetchHealth } from "../api/cases";
import { fetchAnalytics, fetchReviewQueue } from "../api/ops";
import { ConceptBadge, SeverityBadge, StatusBadge } from "../components/Badge";
import { EmptyState, ErrorState } from "../components/EmptyState";
import { KpiCard } from "../components/KpiCard";
import { PageSkeleton } from "../components/Skeleton";
import { StatusDot } from "../components/StatusDot";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { useApi } from "../hooks/useApi";
import { formatRate, formatWhen, lifecycleTone } from "../lib/status";

export function CommandCenterPage() {
  const health = useApi(fetchHealth);
  const analytics = useApi(fetchAnalytics);
  const queue = useApi(fetchReviewQueue);
  const coverage = useApi(fetchCoverage);
  const cases = useApi(() => fetchCases({ limit: "8" }));

  const error = health.error || analytics.error || queue.error || coverage.error || cases.error;
  const loading = health.loading || analytics.loading;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Operations"
        title="Command Center"
        description="Live posture of the lab catalog, AI diagnoses, and the human-review gate. Every figure is read from the API."
      />

      {error && <ErrorState message={error} />}
      {health.data && !health.data.llm_configured && (
        <ErrorState message="LLM is not configured. Diagnosis stays fail-closed until LLM_API_KEY is set in backend/.env." />
      )}
      {loading && <PageSkeleton />}

      {analytics.data && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <KpiCard
            label="Catalog"
            value={analytics.data.case_count}
            hint={health.data ? `${health.data.database} database` : "Cases in SQLite"}
            icon={FolderOpen}
          />
          <KpiCard
            label="Diagnoses"
            value={analytics.data.diagnosed_count}
            hint={`${analytics.data.pending_review_count} waiting for review`}
            icon={Brain}
          />
          <KpiCard
            label="Human reviews"
            value={analytics.data.reviewed_count}
            hint={`Agreement ${formatRate(analytics.data.ai_human_agreement.value)}`}
            icon={ShieldCheck}
          />
          <KpiCard
            label="Verified fixes"
            value={analytics.data.verified_count}
            hint="Human attestation after review"
            icon={CheckCircle2}
          />
          <KpiCard
            label="RAI events"
            value={analytics.data.rai_event_count}
            hint="Created only on edit or reject"
            icon={Scale}
          />
          <KpiCard
            label="Rule failures"
            value={analytics.data.rule_error_count}
            hint="Sum of persisted rule-run errors"
            icon={TriangleAlert}
          />
          <KpiCard
            label="Expected-fault match"
            value={formatRate(analytics.data.ai_expected_match.value)}
            hint={
              analytics.data.ai_expected_match.sample_size
                ? `Sample ${analytics.data.ai_expected_match.sample_size}`
                : "No diagnoses yet"
            }
            icon={Activity}
          />
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        <Card
          title="Review queue"
          description="Diagnoses that cannot proceed until a reviewer acts."
          actions={
            <Link to="/review" className="text-sm text-accent">
              Open review
            </Link>
          }
        >
          {queue.loading && <p className="text-sm text-mist">Loading queue…</p>}
          {queue.data && queue.data.total === 0 && (
            <EmptyState
              title="Nothing pending review"
              body="Run a diagnosis from Troubleshooting or Diagnosis. The queue stays empty until a real AI result is saved."
            />
          )}
          {queue.data && queue.data.total > 0 && (
            <div className="space-y-2">
              {queue.data.items.slice(0, 6).map((item) => (
                <Link
                  key={item.diagnosis_id}
                  to={`/review/${item.case_code}`}
                  className="flex items-center justify-between rounded-lg border border-line bg-ink/40 px-3 py-2.5 transition hover:border-accent/40"
                >
                  <div>
                    <p className="font-mono text-sm text-accent">{item.case_code}</p>
                    <p className="text-xs text-mist">{item.title}</p>
                  </div>
                  <StatusBadge value={item.status} tone="warn" />
                </Link>
              ))}
            </div>
          )}
        </Card>

        <Card
          title="Coverage gate"
          description="Catalog coverage across the eight required Packet Tracer fault types."
          actions={
            <>
              <Link to="/cases/VLAN-001" className="text-sm text-accent">
                Demo case VLAN-001
              </Link>
              {coverage.data ? (
                <div className="flex items-center gap-2 text-xs text-mist">
                  <StatusDot tone={coverage.data.meets_coverage_gate ? "ok" : "warn"} />
                  {coverage.data.meets_coverage_gate ? "Gate met" : "Gate not met"}
                </div>
              ) : null}
            </>
          }
        >
          {coverage.loading && <p className="text-sm text-mist">Loading coverage…</p>}
          {coverage.data && (
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {coverage.data.concepts.map((bucket) => (
                <div key={bucket.key} className="rounded-lg border border-line bg-ink/40 px-3 py-2">
                  <p className="text-[11px] uppercase tracking-wide text-mist">{bucket.key}</p>
                  <p className="text-lg font-medium">{bucket.count}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card
        title="Recent catalog"
        description="Latest cases returned by the cases API."
        actions={
          <Link to="/cases" className="text-sm text-accent">
            Browse cases
          </Link>
        }
      >
        {cases.loading && <p className="text-sm text-mist">Loading cases…</p>}
        {cases.data && cases.data.items.length === 0 && (
          <EmptyState title="No cases in the catalog" body="Seed the dataset from the backend CLI." />
        )}
        {cases.data && cases.data.items.length > 0 && (
          <div className="space-y-2">
            {cases.data.items.map((item) => (
              <Link
                key={item.id}
                to={`/cases/${item.case_code}`}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line bg-ink/40 px-3 py-2.5 transition hover:border-accent/40"
              >
                <div>
                  <p className="font-mono text-sm text-accent">{item.case_code}</p>
                  <p className="text-sm text-snow">{item.title}</p>
                  <p className="text-xs text-mist">{formatWhen(item.updated_at)}</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <ConceptBadge value={item.concept_tag} />
                  <SeverityBadge value={item.severity} />
                  <StatusBadge value={item.lifecycle_status} tone={lifecycleTone(item.lifecycle_status)} />
                </div>
              </Link>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
