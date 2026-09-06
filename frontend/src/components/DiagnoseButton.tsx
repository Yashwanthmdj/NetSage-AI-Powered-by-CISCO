import { useState } from "react";
import { Button } from "./ui/Button";

const REDIAGNOSE_WARNING =
  "A new diagnosis will be created. Historical diagnosis, review, verification, and original AI raw_response records stay unchanged.";

export function DiagnoseButton({
  verified,
  pending,
  diagnosing,
  onDiagnose,
  variant = "secondary",
}: {
  verified: boolean;
  pending: boolean;
  diagnosing: boolean;
  onDiagnose: () => void | Promise<void>;
  variant?: "primary" | "secondary";
}) {
  const [confirming, setConfirming] = useState(false);

  if (!verified) {
    return (
      <Button
        variant={variant}
        onClick={() => void onDiagnose()}
        disabled={diagnosing || pending}
      >
        {diagnosing ? "Diagnosing…" : pending ? "Pending review" : "Diagnose with AI"}
      </Button>
    );
  }

  if (!confirming) {
    return (
      <Button variant="ghost" type="button" onClick={() => setConfirming(true)} disabled={diagnosing}>
        Run new diagnosis…
      </Button>
    );
  }

  return (
    <div className="max-w-md space-y-2 rounded-lg border border-line bg-ink/40 px-3 py-2">
      <p className="text-xs leading-5 text-mist">{REDIAGNOSE_WARNING}</p>
      <div className="flex flex-wrap gap-2">
        <Button
          variant="secondary"
          type="button"
          onClick={async () => {
            await onDiagnose();
            setConfirming(false);
          }}
          disabled={diagnosing}
        >
          {diagnosing ? "Diagnosing…" : "Create new diagnosis"}
        </Button>
        <Button variant="ghost" type="button" onClick={() => setConfirming(false)} disabled={diagnosing}>
          Cancel
        </Button>
      </div>
    </div>
  );
}
