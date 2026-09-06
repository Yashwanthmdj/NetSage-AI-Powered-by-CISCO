import type { RuleCheckResult, RuleEvaluateResponse, RuleRunRead } from "../api/types";

export function reportFromRun(run: RuleRunRead): RuleEvaluateResponse {
  const results = run.findings_json ?? [];
  return {
    results,
    fail_count: results.filter((item) => item.status === "fail").length,
    pass_count: results.filter((item) => item.status === "pass").length,
    rule_run_id: run.id,
    case_id: run.case_id,
  };
}
import { StatusBadge } from "./Badge";
import { Card } from "./ui/Card";

export function RuleResults({
  report,
  title = "Rule engine",
}: {
  report: RuleEvaluateResponse;
  title?: string;
}) {
  return (
    <Card
      title={`${title} · ${report.fail_count} failed · ${report.pass_count} passed`}
      description={
        report.rule_run_id
          ? `Persisted run ${report.rule_run_id}${report.case_id ? ` on case ${report.case_id}` : ""}`
          : "Stateless evaluation — not written to the case record"
      }
    >
      <div className="space-y-3">
        {report.results.map((item) => (
          <RuleRow key={item.rule_name} item={item} />
        ))}
      </div>
    </Card>
  );
}

function RuleRow({ item }: { item: RuleCheckResult }) {
  return (
    <div className="rounded-lg border border-line bg-ink/40 px-4 py-3">
      <div className="flex flex-wrap items-center gap-2">
        <StatusBadge value={item.status} tone={item.status === "fail" ? "danger" : "ok"} />
        <p className="font-mono text-sm text-snow">{item.rule_name}</p>
        {item.severity ? <span className="text-xs capitalize text-mist">{item.severity}</span> : null}
      </div>
      <p className="mt-2 text-sm leading-6 text-mist">{item.explanation}</p>
      {item.devices.length > 0 && (
        <p className="mt-1 text-xs text-mist">Devices: {item.devices.join(", ")}</p>
      )}
      {item.evidence.length > 0 && (
        <pre className="evidence mt-2 text-xs text-snow/80">{item.evidence.join("\n")}</pre>
      )}
    </div>
  );
}
