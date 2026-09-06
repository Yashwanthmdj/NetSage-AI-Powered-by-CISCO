import { useState } from "react";
import { evaluateRules, fetchCaseByCode, fetchCases } from "../api/cases";
import { CasePicker } from "../components/CasePicker";
import { EmptyState, ErrorState } from "../components/EmptyState";
import { Notice } from "../components/Notice";
import { RuleResults } from "../components/RuleResults";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { FieldLabel, TextArea } from "../components/ui/Field";
import { PageHeader } from "../components/ui/PageHeader";
import { useApi } from "../hooks/useApi";
import { useCaseActions } from "../hooks/useCaseActions";
import type { RuleEvaluateResponse } from "../api/types";

export function RuleEnginePage() {
  const catalog = useApi(() => fetchCases({ limit: "100" }));
  const [caseCode, setCaseCode] = useState("");
  const selected = useApi(() => (caseCode ? fetchCaseByCode(caseCode) : Promise.resolve(null)), [caseCode]);
  const persisted = useCaseActions();
  const [showOutputs, setShowOutputs] = useState("");
  const [topology, setTopology] = useState("");
  const [stateless, setStateless] = useState<RuleEvaluateResponse | null>(null);
  const [statelessError, setStatelessError] = useState<string | null>(null);
  const [statelessSuccess, setStatelessSuccess] = useState<string | null>(null);
  const [evaluating, setEvaluating] = useState(false);

  async function loadFromCase() {
    if (!selected.data) return;
    setShowOutputs(selected.data.show_outputs);
    setTopology(selected.data.topology_note);
  }

  async function onEvaluate() {
    setEvaluating(true);
    setStatelessError(null);
    setStatelessSuccess(null);
    try {
      const result = await evaluateRules(showOutputs, topology);
      setStateless(result);
      setStatelessSuccess(
        `Stateless evaluation finished: ${result.fail_count} failed, ${result.pass_count} passed.`,
      );
    } catch (err) {
      setStatelessError(err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      setEvaluating(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Deterministic"
        title="Rule Engine"
        description="Independent of the LLM. Evaluate show-command output here, or persist a run against a catalog case."
        actions={
          <CasePicker
            cases={catalog.data?.items ?? []}
            value={caseCode}
            onChange={setCaseCode}
          />
        }
      />

      {catalog.error && <ErrorState message={catalog.error} />}
      {selected.error && <ErrorState message={selected.error} />}

      <Card
        title="Evidence input"
        description="Paste Packet Tracer show output, or load it from a selected case."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={loadFromCase} disabled={!selected.data}>
              Load selected case
            </Button>
            <Button onClick={onEvaluate} disabled={evaluating || !showOutputs.trim()}>
              {evaluating ? "Evaluating…" : "Evaluate (stateless)"}
            </Button>
            <Button
              variant="secondary"
              onClick={() => selected.data && persisted.onRunRules(selected.data.id)}
              disabled={!selected.data || persisted.running}
            >
              {persisted.running ? "Persisting…" : "Run on case"}
            </Button>
          </div>
        }
      >
        <div className="grid gap-4 lg:grid-cols-2">
          <label className="block">
            <FieldLabel>Show-command evidence</FieldLabel>
            <TextArea
              className="mt-0 min-h-[280px] w-full"
              value={showOutputs}
              onChange={(event) => setShowOutputs(event.target.value)}
              placeholder="S1# show vlan brief"
            />
          </label>
          <label className="block">
            <FieldLabel>Topology notes</FieldLabel>
            <TextArea
              className="mt-0 min-h-[280px] w-full"
              value={topology}
              onChange={(event) => setTopology(event.target.value)}
              placeholder="Optional topology context used by mask and gateway checks"
            />
          </label>
        </div>
      </Card>

      {!showOutputs && !stateless && !persisted.report && (
        <EmptyState
          title="No evidence loaded"
          body="Paste show-command output or load a case. Results come only from the rule engine API."
        />
      )}

      {statelessError && <ErrorState message={statelessError} />}
      {statelessSuccess && <Notice tone="success">{statelessSuccess}</Notice>}
      {persisted.ruleError && <ErrorState message={persisted.ruleError} />}
      {persisted.ruleSuccess && <Notice tone="success">{persisted.ruleSuccess}</Notice>}

      {stateless && <RuleResults report={stateless} title="Stateless evaluation" />}
      {persisted.report && <RuleResults report={persisted.report} title="Persisted case run" />}
    </div>
  );
}
