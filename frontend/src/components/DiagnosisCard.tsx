import type { DiagnosisDetail, DiagnosisRead, ReviewRead } from "../api/types";
import { ConceptBadge, SeverityBadge, StatusBadge } from "./Badge";
import { ErrorState } from "./EmptyState";
import { Notice } from "./Notice";
import { Card } from "./ui/Card";

export function DiagnosisCard({ diagnosis }: { diagnosis: DiagnosisRead | DiagnosisDetail }) {
  const ungrounded = "ungrounded_quotes" in diagnosis ? diagnosis.ungrounded_quotes : [];
  const nextCommand =
    "next_command" in diagnosis && diagnosis.next_command
      ? diagnosis.next_command
      : diagnosis.next_commands_json[0];

  return (
    <Card title={`AI diagnosis · ${diagnosis.status.replaceAll("_", " ")}`}>
      <div className="space-y-4">
        {diagnosis.status === "pending_review" && (
          <Notice tone="warning">
            Pending human review. This answer is not accepted and no fix is considered applied.
          </Notice>
        )}
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <ConceptBadge value={diagnosis.concept_tag} />
          <SeverityBadge value={diagnosis.severity} />
          <StatusBadge
            value={diagnosis.grounded ? "grounded" : "ungrounded"}
            tone={diagnosis.grounded ? "ok" : "danger"}
          />
          <span className="text-mist">
            {diagnosis.osi_layer} · {diagnosis.confidence_label} · {diagnosis.confidence}
          </span>
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-[0.14em] text-mist">Root cause</p>
          <p className="mt-1 text-sm leading-6 text-snow">{diagnosis.root_cause}</p>
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-[0.14em] text-mist">Evidence</p>
          <div className="mt-2 space-y-3">
            {diagnosis.evidence_json.map((item) => (
              <div key={`${item.command}-${item.quote}`} className="rounded-lg border border-line bg-ink/40 p-3">
                <p className="font-mono text-xs text-mist">{item.command}</p>
                <pre className="evidence mt-1 text-xs text-snow/85">{item.quote}</pre>
                <p className="mt-1 text-sm text-mist">{item.why}</p>
              </div>
            ))}
          </div>
        </div>
        {ungrounded.length > 0 && (
          <ErrorState message={`Quotes not found in show-command evidence: ${ungrounded.join(" · ")}`} />
        )}
        <div>
          <p className="text-[11px] uppercase tracking-[0.14em] text-mist">Fix steps</p>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm leading-6 text-snow">
            {diagnosis.fix_steps_json.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-lg border border-line bg-ink/40 p-3">
            <p className="text-[11px] uppercase tracking-[0.14em] text-mist">Next command</p>
            <pre className="evidence mt-1 text-xs">{nextCommand}</pre>
          </div>
          <div className="rounded-lg border border-line bg-ink/40 p-3">
            <p className="text-[11px] uppercase tracking-[0.14em] text-mist">Verification command</p>
            <pre className="evidence mt-1 text-xs">{diagnosis.verification_command}</pre>
          </div>
        </div>
        {diagnosis.raw_response && (
          <details>
            <summary className="cursor-pointer text-[11px] uppercase tracking-[0.14em] text-mist">
              Original AI JSON
            </summary>
            <pre className="evidence mt-2 text-xs text-snow/80">{diagnosis.raw_response}</pre>
          </details>
        )}
      </div>
    </Card>
  );
}

export function ReviewDecision({ review }: { review: ReviewRead }) {
  return (
    <Card title={`Human decision · ${review.verdict}`}>
      <div className="space-y-3 text-sm">
        <p className="leading-6 text-mist">{review.correction_reason || "No reviewer notes."}</p>
        {review.verdict === "edited" && (
          <>
            <div>
              <p className="text-[11px] uppercase tracking-[0.14em] text-mist">Corrected root cause</p>
              <p className="mt-1 leading-6 text-snow">{review.corrected_root_cause}</p>
            </div>
            <p className="text-mist">
              {review.corrected_osi_layer} · {review.corrected_concept_tag}
            </p>
            {review.corrected_fix_steps_json && (
              <ol className="list-decimal space-y-1 pl-5 leading-6">
                {review.corrected_fix_steps_json.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
            )}
          </>
        )}
        {review.override_ungrounded && (
          <p className="text-warn">Reviewer overrode ungrounded evidence.</p>
        )}
        {review.fix_applied && (
          <p className="text-accent">
            Fix marked applied{review.fix_applied_by ? ` by ${review.fix_applied_by}` : ""}.
          </p>
        )}
      </div>
    </Card>
  );
}
