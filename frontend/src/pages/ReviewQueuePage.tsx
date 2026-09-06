import { Link } from "react-router-dom";
import { fetchReviewQueue } from "../api/ops";
import { StatusBadge } from "../components/Badge";
import { EmptyState, ErrorState } from "../components/EmptyState";
import { PageSkeleton } from "../components/Skeleton";
import { PageHeader } from "../components/ui/PageHeader";
import { Table } from "../components/ui/Table";
import { useApi } from "../hooks/useApi";
import { formatWhen } from "../lib/status";

export function ReviewQueuePage() {
  const { data, error, loading } = useApi(fetchReviewQueue);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Governance"
        title="Human Review"
        description="Every AI diagnosis requires Accepted, Edited, or Rejected. Nothing is applied until a reviewer records a verdict."
      />
      {error && <ErrorState message={error} />}
      {loading && <PageSkeleton />}
      {data && data.total === 0 && (
        <EmptyState
          title="No diagnoses waiting for review"
          body="The queue is computed from diagnoses with status pending_review. Run a diagnosis first."
        />
      )}
      {data && data.total > 0 && (
        <Table
          headers={["Case", "Title", "Concept", "Status", "Opened", "Action"]}
          rows={data.items.map((item) => [
            <Link key={item.diagnosis_id} className="font-mono text-accent" to={`/review/${item.case_code}`}>
              {item.case_code}
            </Link>,
            item.title,
            item.concept_tag,
            <StatusBadge key={`${item.diagnosis_id}-s`} value={item.status} tone="warn" />,
            formatWhen(item.created_at),
            <Link key={`${item.diagnosis_id}-a`} className="text-accent" to={`/review/${item.case_code}`}>
              Review
            </Link>,
          ])}
        />
      )}
    </div>
  );
}
