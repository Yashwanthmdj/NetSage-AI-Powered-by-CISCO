import { useState, type FormEvent } from "react";
import { verifyCase } from "../api/cases";
import type { VerificationRead } from "../api/types";
import { ErrorState } from "./EmptyState";
import { Button } from "./ui/Button";
import { Card } from "./ui/Card";
import { FieldLabel, TextArea, TextInput } from "./ui/Field";

export function VerifyForm({
  caseId,
  command,
  onVerified,
}: {
  caseId: number;
  command?: string | null;
  onVerified: (row: VerificationRead) => void;
}) {
  const [verifiedBy, setVerifiedBy] = useState("Lab Reviewer");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      onVerified(await verifyCase(caseId, { verified_by: verifiedBy, notes: notes || undefined }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card
      title="Verify fix"
      description="Human attestation after the Packet Tracer lab is repaired. This is not an automated Packet Tracer check."
    >
      <form className="space-y-3" onSubmit={onSubmit}>
        {command ? (
          <p className="rounded-lg border border-line bg-ink/40 px-3 py-2 font-mono text-xs text-mist">
            Suggested check: {command}
          </p>
        ) : null}
        <label className="block">
          <FieldLabel>Verified by</FieldLabel>
          <TextInput className="w-full" value={verifiedBy} onChange={(event) => setVerifiedBy(event.target.value)} required />
        </label>
        <label className="block">
          <FieldLabel>Notes</FieldLabel>
          <TextArea
            className="w-full"
            rows={3}
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="What command confirmed the fix?"
          />
        </label>
        {error && <ErrorState message={error} />}
        <Button type="submit" disabled={saving}>
          {saving ? "Saving…" : "Record verification"}
        </Button>
      </form>
    </Card>
  );
}

export function VerificationCard({
  verification,
}: {
  verification: VerificationRead;
}) {
  return (
    <Card title="Fix verified">
      <p className="text-sm text-snow">
        Attested by <span className="font-medium">{verification.verified_by}</span>
      </p>
      {verification.notes ? <p className="mt-2 text-sm leading-6 text-mist">{verification.notes}</p> : null}
    </Card>
  );
}
