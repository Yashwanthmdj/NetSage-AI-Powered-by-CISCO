import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

export function Card({
  title,
  description,
  actions,
  children,
  className,
}: {
  title?: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("rounded-xl border border-line bg-panel p-5 shadow-card", className)}>
      {(title || actions) && (
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            {title ? (
              <h3 className="text-[11px] font-medium uppercase tracking-[0.16em] text-mist">{title}</h3>
            ) : null}
            {description ? <p className="mt-1 text-sm text-mist">{description}</p> : null}
          </div>
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}
