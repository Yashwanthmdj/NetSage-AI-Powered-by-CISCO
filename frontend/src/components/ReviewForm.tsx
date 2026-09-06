import { useState, type FormEvent } from "react";
import { submitReview } from "../api/ops";
import type {
  ConceptTag,
  DiagnosisRead,
  OsiLayer,
  RaiFailureClass,
  ReviewCreate,
  ReviewDetail,
  ReviewVerdict,
} from "../api/types";
import { ErrorState } from "./EmptyState";
import { Button } from "./ui/Button";
import { Card } from "./ui/Card";
import { Select, TextArea, TextInput } from "./ui/Field";

const OSI_LAYERS: OsiLayer[] = ["L1", "L2", "L3", "L4", "L5", "L6", "L7"];
const CONCEPTS: ConceptTag[] = ["vlan", "gateway", "dhcp", "dns", "routing", "acl", "nat", "wireless"];
const FAILURES: RaiFailureClass[] = [
  "hallucinated_evidence",
  "wrong_layer",
  "wrong_concept",
  "missed_rule_finding",
  "incomplete_fix",
  "overconfident",
];

function buildPayload(form: {
  verdict: ReviewVerdict;
  reviewerName: string;
  notes: string;
  rootCause: string;
  osiLayer: OsiLayer;
  conceptTag: ConceptTag;
  fixSteps: string;
  override: boolean;
  failureClass: RaiFailureClass;
}): ReviewCreate {
  const payload: ReviewCreate = {
    verdict: form.verdict,
    reviewer_name: form.reviewerName.trim() || "Lab Reviewer",
  };
  if (form.notes.trim()) payload.correction_reason = form.notes.trim();
  if (form.verdict === "accepted" && form.override) {
    payload.override_ungrounded = true;
  }
  if (form.verdict === "edited") {
    payload.corrected_root_cause = form.rootCause.trim();
    payload.corrected_osi_layer = form.osiLayer;
    payload.corrected_concept_tag = form.conceptTag;
    payload.corrected_fix_steps = form.fixSteps
      .split("\n")
      .map((step) => step.trim())
      .filter(Boolean);
    payload.failure_class = form.failureClass;
  }
  if (form.verdict === "rejected") {
    payload.failure_class = form.failureClass;
  }
  return payload;
}

export function ReviewForm({
  diagnosis,
  onSubmitted,
}: {
  diagnosis: DiagnosisRead;
  onSubmitted: (review: ReviewDetail) => void;
}) {
  const [verdict, setVerdict] = useState<ReviewVerdict>("accepted");
  const [reviewerName, setReviewerName] = useState("Lab Reviewer");
  const [notes, setNotes] = useState("");
  const [rootCause, setRootCause] = useState(diagnosis.root_cause);
  const [osiLayer, setOsiLayer] = useState<OsiLayer>(
    OSI_LAYERS.includes(diagnosis.osi_layer as OsiLayer) ? (diagnosis.osi_layer as OsiLayer) : "L2",
  );
  const [conceptTag, setConceptTag] = useState<ConceptTag>(
    CONCEPTS.includes(diagnosis.concept_tag as ConceptTag)
      ? (diagnosis.concept_tag as ConceptTag)
      : "vlan",
  );
  const [fixSteps, setFixSteps] = useState(diagnosis.fix_steps_json.join("\n"));
  const [override, setOverride] = useState(false);
  const [failureClass, setFailureClass] = useState<RaiFailureClass>("wrong_concept");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      onSubmitted(
        await submitReview(
          diagnosis.id,
          buildPayload({
            verdict,
            reviewerName,
            notes,
            rootCause,
            osiLayer,
            conceptTag,
            fixSteps,
            override,
            failureClass,
          }),
        ),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card title="Human review">
      <form className="space-y-4" onSubmit={onSubmit}>
        <p className="text-sm text-mist">
          Every diagnosis stays pending until you accept, edit, or reject it. The original AI
          answer is kept even if you correct it.
        </p>
        <div className="flex flex-wrap gap-2">
          {(["accepted", "edited", "rejected"] as ReviewVerdict[]).map((value) => (
            <Button
              key={value}
              type="button"
              variant={verdict === value ? "primary" : "secondary"}
              onClick={() => setVerdict(value)}
            >
              {value}
            </Button>
          ))}
        </div>
        <label className="block text-sm">
          <span className="text-xs uppercase tracking-wide text-mist">Reviewer</span>
          <TextInput
            className="mt-1 w-full"
            value={reviewerName}
            onChange={(event) => setReviewerName(event.target.value)}
          />
        </label>
        <label className="block text-sm">
          <span className="text-xs uppercase tracking-wide text-mist">Reviewer notes</span>
          <TextArea
            className="mt-1 w-full"
            rows={3}
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder={
              verdict === "accepted"
                ? "Optional unless you override ungrounded evidence"
                : "Required: why the AI was wrong or incomplete"
            }
          />
        </label>
        {verdict === "accepted" && !diagnosis.grounded && (
          <label className="flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              className="mt-1"
              checked={override}
              onChange={(event) => setOverride(event.target.checked)}
            />
            <span>Override ungrounded quotes and accept anyway (notes required)</span>
          </label>
        )}
        {verdict === "edited" && (
          <div className="grid gap-3 md:grid-cols-2">
            <label className="block text-sm md:col-span-2">
              <span className="text-xs uppercase tracking-wide text-mist">Corrected root cause</span>
              <TextArea
                className="mt-1 w-full"
                rows={3}
                value={rootCause}
                onChange={(event) => setRootCause(event.target.value)}
              />
            </label>
            <label className="block text-sm">
              <span className="text-xs uppercase tracking-wide text-mist">Corrected OSI layer</span>
              <Select
                className="mt-1 w-full"
                value={osiLayer}
                onChange={(event) => setOsiLayer(event.target.value as OsiLayer)}
              >
                {OSI_LAYERS.map((layer) => (
                  <option key={layer} value={layer}>
                    {layer}
                  </option>
                ))}
              </Select>
            </label>
            <label className="block text-sm">
              <span className="text-xs uppercase tracking-wide text-mist">Corrected concept</span>
              <Select
                className="mt-1 w-full"
                value={conceptTag}
                onChange={(event) => setConceptTag(event.target.value as ConceptTag)}
              >
                {CONCEPTS.map((tag) => (
                  <option key={tag} value={tag}>
                    {tag}
                  </option>
                ))}
              </Select>
            </label>
            <label className="block text-sm md:col-span-2">
              <span className="text-xs uppercase tracking-wide text-mist">Corrected fix steps</span>
              <TextArea
                className="mt-1 w-full"
                rows={4}
                value={fixSteps}
                onChange={(event) => setFixSteps(event.target.value)}
              />
            </label>
          </div>
        )}
        {(verdict === "edited" || verdict === "rejected") && (
          <label className="block text-sm">
            <span className="text-xs uppercase tracking-wide text-mist">RAI failure class</span>
            <Select
              className="mt-1 w-full"
              value={failureClass}
              onChange={(event) => setFailureClass(event.target.value as RaiFailureClass)}
            >
              {FAILURES.map((item) => (
                <option key={item} value={item}>
                  {item.replaceAll("_", " ")}
                </option>
              ))}
            </Select>
          </label>
        )}
        {error && <ErrorState message={error} />}
        <Button type="submit" disabled={saving}>
          {saving ? "Saving…" : "Submit review"}
        </Button>
      </form>
    </Card>
  );
}
