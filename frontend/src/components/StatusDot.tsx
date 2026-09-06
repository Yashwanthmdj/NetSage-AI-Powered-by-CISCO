import { cn } from "../lib/cn";

export function StatusDot({
  tone,
  pulse = false,
}: {
  tone: "ok" | "warn" | "danger" | "neutral";
  pulse?: boolean;
}) {
  const colors = {
    ok: "bg-accent",
    warn: "bg-warn",
    danger: "bg-danger",
    neutral: "bg-mist",
  };
  return (
    <span
      className={cn("inline-block h-1.5 w-1.5 rounded-full", colors[tone], pulse && "animate-pulse-dot")}
    />
  );
}
