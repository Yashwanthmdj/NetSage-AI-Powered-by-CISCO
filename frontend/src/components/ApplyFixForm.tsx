import { useState, type FormEvent } from "react";
import { applyReviewFix } from "../api/ops";
import type { ReviewDetail } from "../api/types";
import { ErrorState } from "./EmptyState";
import { Button } from "./ui/Button";
import { Card } from "./ui/Card";
import { FieldLabel, TextInput } from "./ui/Field";

export function ApplyFixForm({
  reviewId,
  command,
  onApplied,
}: {
  reviewId: number;
  command?: string | null;
  onApplied: (row: ReviewDetail) => void;
}) {
  const [appliedBy, setAppliedBy] = useState("Lab Reviewer");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      onApplied(await applyReviewFix(reviewId, appliedBy));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not mark the fix as applied");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card
      title="Mark fix as applied"
      description="Human attestation that the recommended Packet Tracer change was applied. NetSage AI does not execute Cisco commands."
    >
      <form className="space-y-3" onSubmit={onSubmit}>
        {command ? (
          <p className="rounded-lg border border-line bg-ink/40 px-3 py-2 font-mono text-xs text-mist">
            Recommended check after apply: {command}
          </p>
        ) : null}
        <label className="block">
          <FieldLabel>Applied by</FieldLabel>
          <TextInput className="w-full" value={appliedBy} onChange={(event) => setAppliedBy(event.target.value)} required />
        </label>
        {error && <ErrorState message={error} />}
        <Button type="submit" disabled={saving}>
          {saving ? "Saving…" : "Mark fix applied"}
        </Button>
      </form>
    </Card>
  );
}
