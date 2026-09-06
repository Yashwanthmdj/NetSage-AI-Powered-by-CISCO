import { Link } from "react-router-dom";
import { fetchAnalytics, fetchRaiEvents } from "../api/ops";
import { StatusBadge } from "../components/Badge";
import { EmptyState, ErrorState } from "../components/EmptyState";
import { KpiCard } from "../components/KpiCard";
import { PageSkeleton } from "../components/Skeleton";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { useApi } from "../hooks/useApi";
import { formatWhen } from "../lib/status";

export function RaiLogPage() {
  const events = useApi(fetchRaiEvents);
  const analytics = useApi(fetchAnalytics);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Accountability"
        title="Responsible AI"
        description="Accepted, edited, and rejected counts are read from the reviews table. Correction rows below are created only when a reviewer edits or rejects a real diagnosis."
      />
      {events.error && <ErrorState message={events.error} />}
      {analytics.error && <ErrorState message={analytics.error} />}
      {events.loading && <PageSkeleton />}

      {analytics.data && (
        <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-6">
          <KpiCard label="Accepted" value={analytics.data.accepted_count} hint="From reviews in SQLite" />
          <KpiCard label="Edited" value={analytics.data.edited_count} hint="From reviews in SQLite" />
          <KpiCard label="Rejected" value={analytics.data.rejected_count} hint="From reviews in SQLite" />
          <KpiCard label="RAI events" value={analytics.data.rai_event_count} hint="Edit and reject only" />
          <KpiCard label="Failure classes" value={analytics.data.rai_failure_classes.length} />
          <KpiCard label="Reviewed" value={analytics.data.reviewed_count} />
        </div>
      )}

      {events.data && events.data.total === 0 && (
        <EmptyState
          title="No human corrections logged"
          body="The VIP requirement of five corrections will be produced by using the review workflow, not by seeding fake notes."
        />
      )}
      {events.data && events.data.total > 0 && (
        <div className="space-y-4">
          {events.data.items.map((item) => (
            <Card
              key={item.id}
              title={`${item.failure_class.replaceAll("_", " ")}`}
              description={formatWhen(item.created_at)}
              actions={item.verdict ? <StatusBadge value={item.verdict} tone={item.verdict === "rejected" ? "danger" : "warn"} /> : null}
            >
              <div className="space-y-3 text-sm">
                <p>
                  {item.case_code ? (
                    <Link className="font-mono text-accent" to={`/cases/${item.case_code}`}>
                      {item.case_code}
                    </Link>
                  ) : (
                    <span className="font-mono">case {item.case_id}</span>
                  )}
                  <span className="text-mist">
                    {" "}
                    · {item.record_kind === "reviewed_lab_case" ? "reviewed lab case" : "lab review"} · review {item.review_id}
                  </span>
                </p>
                <p className="leading-6 text-snow">{item.explanation}</p>
                <details>
                  <summary className="cursor-pointer text-[11px] uppercase tracking-[0.14em] text-mist">
                    Original AI snapshot
                  </summary>
                  <pre className="evidence mt-2 text-xs text-snow/80">
                    {JSON.stringify(item.ai_snapshot_json ?? {}, null, 2)}
                  </pre>
                </details>
                <details>
                  <summary className="cursor-pointer text-[11px] uppercase tracking-[0.14em] text-mist">
                    Human correction
                  </summary>
                  <pre className="evidence mt-2 text-xs text-snow/80">
                    {JSON.stringify(item.human_correction_json ?? {}, null, 2)}
                  </pre>
                </details>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
