import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchCases, fetchCoverage, seedCatalog } from "../api/cases";
import type { CaseListResponse, ConceptTag, DatasetCoverage, Severity } from "../api/types";
import { ConceptBadge, SeverityBadge, StatusBadge } from "../components/Badge";
import { CaseCreateForm } from "../components/CaseCreateForm";
import { EmptyState, ErrorState } from "../components/EmptyState";
import { Notice } from "../components/Notice";
import { PageSkeleton } from "../components/Skeleton";
import { Button } from "../components/ui/Button";
import { Select, TextInput } from "../components/ui/Field";
import { PageHeader } from "../components/ui/PageHeader";
import { Table } from "../components/ui/Table";
import { useApi } from "../hooks/useApi";
import { lifecycleTone } from "../lib/status";

const CONCEPTS: Array<ConceptTag | ""> = [
  "",
  "vlan",
  "gateway",
  "dhcp",
  "dns",
  "routing",
  "acl",
  "nat",
  "wireless",
];

export function CasesPage() {
  const [concept, setConcept] = useState<ConceptTag | "">("");
  const [severity, setSeverity] = useState<Severity | "">("");
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(query), 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  const cases = useApi<CaseListResponse>(
    () =>
      fetchCases({
        concept_tag: concept || undefined,
        severity: severity || undefined,
        q: debounced || undefined,
        limit: "100",
      }),
    [concept, severity, debounced],
  );
  const coverage = useApi<DatasetCoverage>(fetchCoverage);
  const [seedError, setSeedError] = useState<string | null>(null);
  const [seedSuccess, setSeedSuccess] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);

  async function onSeed() {
    setSeeding(true);
    setSeedError(null);
    setSeedSuccess(null);
    try {
      const result = await seedCatalog();
      setSeedSuccess(`Catalog seed: ${result.created} created, ${result.updated} updated.`);
      cases.reload({ silent: true });
      coverage.reload({ silent: true });
    } catch (err) {
      setSeedError(err instanceof Error ? err.message : "Seed failed");
    } finally {
      setSeeding(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Catalog"
        title="Cases"
        description={
          coverage.data
            ? `${coverage.data.case_count} Packet Tracer cases across ${coverage.data.concepts.length} fault types. Coverage gate ${coverage.data.meets_coverage_gate ? "is met" : "is not met"}.`
            : "Loading coverage from the database"
        }
        actions={
          <>
            <Select
              value={concept}
              onChange={(event) => setConcept(event.target.value as ConceptTag | "")}
            >
              {CONCEPTS.map((item) => (
                <option key={item || "all"} value={item}>
                  {item || "All concepts"}
                </option>
              ))}
            </Select>
            <Select
              value={severity}
              onChange={(event) => setSeverity(event.target.value as Severity | "")}
            >
              <option value="">All severities</option>
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
              <option value="critical">critical</option>
            </Select>
            <TextInput
              className="w-64"
              placeholder="Search code, title, symptom"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <Button variant="secondary" onClick={onSeed} disabled={seeding}>
              {seeding ? "Seeding…" : "Seed catalog"}
            </Button>
          </>
        }
      />

      {seedError && <ErrorState message={seedError} />}
      {seedSuccess && <Notice tone="success">{seedSuccess}</Notice>}
      <CaseCreateForm
        onCreated={() => {
          cases.reload({ silent: true });
          coverage.reload({ silent: true });
        }}
      />

      {coverage.data && (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-8">
          {coverage.data.concepts.map((bucket) => (
            <button
              key={bucket.key}
              type="button"
              onClick={() => setConcept(bucket.key as ConceptTag)}
              className="rounded-xl border border-line bg-panel px-3 py-2 text-left transition hover:border-accent/40"
            >
              <p className="text-[11px] uppercase tracking-wide text-mist">{bucket.key}</p>
              <p className="text-lg font-medium">{bucket.count}</p>
            </button>
          ))}
        </div>
      )}

      {cases.error && <ErrorState message={cases.error} />}
      {cases.loading && <PageSkeleton />}

      {cases.data && cases.data.items.length === 0 && (
        <EmptyState
          title="No cases match these filters"
          body="Clear the search or seed the catalog from the backend."
        />
      )}

      {cases.data && cases.data.items.length > 0 && (
        <Table
          headers={["Code", "Title", "Concept", "Layer", "Severity", "Lifecycle"]}
          rows={cases.data.items.map((item) => [
            <Link key={item.id} className="font-mono text-accent" to={`/cases/${item.case_code}`}>
              {item.case_code}
            </Link>,
            <span key={`${item.id}-t`} className="text-snow">
              {item.title}
            </span>,
            <ConceptBadge key={`${item.id}-c`} value={item.concept_tag} />,
            item.osi_layer,
            <SeverityBadge key={`${item.id}-s`} value={item.severity} />,
            <StatusBadge
              key={`${item.id}-l`}
              value={item.lifecycle_status}
              tone={lifecycleTone(item.lifecycle_status)}
            />,
          ])}
        />
      )}
    </div>
  );
}
