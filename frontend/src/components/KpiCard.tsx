import type { LucideIcon } from "lucide-react";
import { Card } from "./ui/Card";

export function KpiCard({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  hint?: string;
  icon?: LucideIcon;
}) {
  return (
    <Card className="animate-enter">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-mist">{label}</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-snow">{value}</p>
          {hint ? <p className="mt-1 text-xs text-mist">{hint}</p> : null}
        </div>
        {Icon ? (
          <span className="rounded-lg border border-line bg-raised p-2 text-accent">
            <Icon size={16} />
          </span>
        ) : null}
      </div>
    </Card>
  );
}
