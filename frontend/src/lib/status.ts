export function lifecycleTone(status: string): "ok" | "warn" | "danger" | "neutral" {
  if (status === "accepted" || status === "verified" || status === "edited" || status === "fix_applied") return "ok";
  if (status === "pending_review" || status === "imported" || status === "rules_run") return "warn";
  if (status === "rejected" || status === "failed") return "danger";
  return "neutral";
}

export function formatRate(value: number | null | undefined) {
  if (value == null) return "—";
  return `${Math.round(value * 100)}%`;
}

export function formatWhen(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}
