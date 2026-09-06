import { Brain, CheckCircle2, FolderOpen, Scale, ShieldCheck, TriangleAlert, Users } from "lucide-react";
import { fetchAnalytics } from "../api/ops";
import { EmptyState, ErrorState } from "../components/EmptyState";
import { KpiCard } from "../components/KpiCard";
import { PageSkeleton } from "../components/Skeleton";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { useApi } from "../hooks/useApi";
import { formatRate } from "../lib/status";

function BucketGrid({ items }: { items: { key: string; count: number }[] }) {
  const max = Math.max(...items.map((item) => item.count), 1);
  return (
    <div className="space-y-3">
      {items.map((bucket) => (
        <div key={bucket.key}>
          <div className="mb-1 flex items-center justify-between text-sm">
            <span className="capitalize text-mist">{bucket.key.replaceAll("_", " ")}</span>
            <span className="font-medium text-snow">{bucket.count}</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-raised">
            <div
              className="h-full rounded-full bg-accent/80 transition-all"
              style={{ width: `${(bucket.count / max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export function AnalyticsPage() {
  const { data, error, loading } = useApi(fetchAnalytics);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Telemetry"
        title="Analytics"
        description="Every figure is computed from the database. Rates stay blank until diagnoses and reviews exist."
      />
      {error && <ErrorState message={error} />}
      {loading && <PageSkeleton />}
      {data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <KpiCard label="Cases" value={data.case_count} icon={FolderOpen} />
            <KpiCard label="Diagnoses" value={data.diagnosed_count} hint={`${data.pending_review_count} pending`} icon={Brain} />
            <KpiCard label="Accepted" value={data.accepted_count} icon={ShieldCheck} />
            <KpiCard label="Edited" value={data.edited_count} icon={Scale} />
            <KpiCard label="Rejected" value={data.rejected_count} icon={TriangleAlert} />
            <KpiCard label="Unresolved" value={data.unresolved_count} hint="Cases not yet verified" icon={FolderOpen} />
            <KpiCard label="Verified fixes" value={data.verified_count} icon={CheckCircle2} />
            <KpiCard
              label="Human agreement"
              value={formatRate(data.ai_human_agreement.value)}
              hint={
                data.ai_human_agreement.sample_size
                  ? `Accepted / ${data.ai_human_agreement.sample_size} reviews`
                  : "No reviews yet"
              }
              icon={Users}
            />
            <KpiCard
              label="Verification success"
              value={formatRate(data.verification_success.value)}
              hint={
                data.verification_success.sample_size
                  ? `Verified / ${data.verification_success.sample_size} accepted or edited`
                  : "No verifiable reviews yet"
              }
              icon={CheckCircle2}
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="Cases by issue type">
              {data.counts_by_concept.length ? (
                <BucketGrid items={data.counts_by_concept} />
              ) : (
                <EmptyState title="No concept buckets" body="Seed the catalog first." />
              )}
            </Card>
            <Card title="Cases by severity">
              {data.counts_by_severity.length ? (
                <BucketGrid items={data.counts_by_severity} />
              ) : (
                <EmptyState title="No severity buckets" body="Seed the catalog first." />
              )}
            </Card>
            <Card title="Reviewer verdicts">
              {data.review_verdicts.length ? (
                <BucketGrid items={data.review_verdicts} />
              ) : (
                <EmptyState
                  title="No reviewer verdicts yet"
                  body="Accepted, edited, and rejected counts appear after a human decision is saved."
                />
              )}
            </Card>
            <Card title="Responsible AI failure classes">
              {data.rai_failure_classes.length ? (
                <BucketGrid items={data.rai_failure_classes} />
              ) : (
                <EmptyState
                  title="No RAI classes"
                  body="Edited and rejected reviews write failure classes here."
                />
              )}
            </Card>
          </div>

          <Card title="AI vs expected fault">
            {data.ai_expected_match.sample_size === 0 ? (
              <EmptyState
                title="AI vs expected-fault match is not available"
                body="This rate needs persisted diagnoses. Sample size is 0."
              />
            ) : (
              <div>
                <p className="text-3xl font-semibold">{formatRate(data.ai_expected_match.value)}</p>
                <p className="mt-1 text-xs text-mist">Sample size {data.ai_expected_match.sample_size}</p>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
