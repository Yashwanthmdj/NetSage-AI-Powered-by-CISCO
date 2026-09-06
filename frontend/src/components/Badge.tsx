import type { ConceptTag, Severity } from "../api/types";
import { cn } from "../lib/cn";

const severityClass: Record<Severity, string> = {
  low: "bg-snow/5 text-mist",
  medium: "bg-warn/10 text-warn",
  high: "bg-orange-400/10 text-orange-200",
  critical: "bg-danger/12 text-danger",
};

export function SeverityBadge({ value }: { value: Severity | string }) {
  const key = (value in severityClass ? value : "medium") as Severity;
  return (
    <span className={cn("rounded-md px-2 py-0.5 text-[11px] font-medium capitalize", severityClass[key])}>
      {value}
    </span>
  );
}

export function ConceptBadge({ value }: { value: ConceptTag | string }) {
  return (
    <span className="rounded-md bg-accent/10 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-accent">
      {value}
    </span>
  );
}

export function StatusBadge({
  value,
  tone = "neutral",
}: {
  value: string;
  tone?: "ok" | "warn" | "danger" | "neutral";
}) {
  const tones = {
    ok: "bg-accent/10 text-accent",
    warn: "bg-warn/10 text-warn",
    danger: "bg-danger/12 text-danger",
    neutral: "bg-snow/5 text-mist",
  };
  return (
    <span className={cn("rounded-md px-2 py-0.5 text-[11px] font-medium capitalize", tones[tone])}>
      {value.replaceAll("_", " ")}
    </span>
  );
}
