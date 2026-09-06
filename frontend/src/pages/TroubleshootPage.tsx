import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { fetchCaseByCode, fetchCases } from "../api/cases";
import { ConceptBadge, SeverityBadge, StatusBadge } from "../components/Badge";
import { CasePicker } from "../components/CasePicker";
import { DiagnosisCard } from "../components/DiagnosisCard";
import { EmptyState, ErrorState } from "../components/EmptyState";
import { Notice } from "../components/Notice";
import { RuleResults } from "../components/RuleResults";
import { PageSkeleton } from "../components/Skeleton";
import { DiagnoseButton } from "../components/DiagnoseButton";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { useApi } from "../hooks/useApi";
import { useCaseActions } from "../hooks/useCaseActions";
import { lifecycleTone } from "../lib/status";

export function TroubleshootPage() {
  const [searchParams] = useSearchParams();
  const catalog = useApi(() => fetchCases({ limit: "100" }));
  const [caseCode, setCaseCode] = useState(searchParams.get("case") ?? "");

  useEffect(() => {
    const fromQuery = searchParams.get("case");
    if (fromQuery && fromQuery !== caseCode) {
      setCaseCode(fromQuery);
    }
  }, [searchParams, caseCode]);
  const selected = useApi(() => (caseCode ? fetchCaseByCode(caseCode) : Promise.resolve(null)), [caseCode]);
  const actions = useCaseActions();

  const verified = selected.data?.lifecycle_status === "verified";
  const shownDiagnosis = verified
    ? selected.data?.latest_diagnosis ?? null
    : actions.diagnosis ?? selected.data?.latest_diagnosis ?? null;
  const pending = !verified && shownDiagnosis?.status === "pending_review";

  const cases = catalog.data?.items ?? [];
  const title = useMemo(
    () => (selected.data ? selected.data.title : "Select a case to inspect evidence and run checks"),
    [selected.data],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Workbench"
        title="Troubleshooting"
        description="Load a Packet Tracer case, inspect the symptom and show-command evidence, then run the deterministic rule engine or request an AI diagnosis."
        actions={
          <CasePicker
            cases={cases}
            value={caseCode}
            onChange={(value) => {
              setCaseCode(value);
              actions.setReport(null);
              actions.setDiagnosis(null);
            }}
          />
        }
      />

      {catalog.error && <ErrorState message={catalog.error} />}
      {selected.error && <ErrorState message={selected.error} />}
      {catalog.loading && !catalog.data && <PageSkeleton />}

      {!caseCode && (
        <EmptyState
          title="No case loaded"
          body="Choose a case from the catalog, or open the demo lab VLAN-001. The workbench only shows live API data."
        />
      )}
      {!caseCode && (
        <Link to="/troubleshoot?case=VLAN-001" className="inline-flex text-sm text-accent">
          Load demo case VLAN-001
        </Link>
      )}

      {caseCode && selected.loading && <PageSkeleton />}

      {selected.data && (
        <>
          <Card>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-mono text-lg text-accent">{selected.data.case_code}</p>
                <p className="mt-1 text-snow">{title}</p>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <ConceptBadge value={selected.data.concept_tag} />
                  <SeverityBadge value={selected.data.severity} />
                  <StatusBadge
                    value={selected.data.lifecycle_status}
                    tone={lifecycleTone(selected.data.lifecycle_status)}
                  />
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  onClick={() => actions.onRunRules(selected.data!.id)}
                  disabled={actions.running}
                >
                  {actions.running ? "Checking…" : "Run rule engine"}
                </Button>
                <DiagnoseButton
                  verified={verified}
                  pending={pending}
                  diagnosing={actions.diagnosing}
                  onDiagnose={() => actions.onDiagnose(selected.data!.id)}
                />
                <Link to={`/cases/${selected.data.case_code}`} className="text-sm text-accent self-center">
                  Open case file
                </Link>
              </div>
            </div>
          </Card>

          <section className="grid gap-4 lg:grid-cols-2">
            <Card title="Symptom">
              <p className="text-sm leading-6">{selected.data.symptom}</p>
            </Card>
            <Card title="Topology notes">
              <p className="text-sm leading-6">{selected.data.topology_note}</p>
            </Card>
          </section>

          {verified && (
            <Notice tone="success">
              This case is verified. The accepted diagnosis below is the official record.
            </Notice>
          )}

          {actions.ruleError && <ErrorState message={actions.ruleError} />}
          {actions.ruleSuccess && <Notice tone="success">{actions.ruleSuccess}</Notice>}
          {actions.diagnoseError && <ErrorState message={actions.diagnoseError} />}
          {actions.diagnoseSuccess && <Notice tone="success">{actions.diagnoseSuccess}</Notice>}

          {actions.report && <RuleResults report={actions.report} />}
          {shownDiagnosis && <DiagnosisCard diagnosis={shownDiagnosis} />}

          <Card title="Show-command evidence" className="bg-ink/60">
            <pre className="evidence max-h-[420px] overflow-auto text-[13px] leading-6 text-snow/85 scrollbar-thin">
              {selected.data.show_outputs}
            </pre>
          </Card>
        </>
      )}
    </div>
  );
}
