import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";
import { cn } from "../lib/cn";

const styles = {
  success: "border-accent/30 bg-accent/10 text-accent",
  error: "border-danger/35 bg-danger/10 text-danger",
  warning: "border-warn/35 bg-warn/10 text-warn",
  info: "border-line bg-raised text-snow",
};

const icons = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

export function Notice({
  tone = "info",
  children,
}: {
  tone?: keyof typeof styles;
  children: string;
}) {
  const Icon = icons[tone];
  return (
    <div className={cn("flex items-start gap-2 rounded-xl border px-4 py-3 text-sm", styles[tone])}>
      <Icon size={16} className="mt-0.5 shrink-0" />
      <p>{children}</p>
    </div>
  );
}
