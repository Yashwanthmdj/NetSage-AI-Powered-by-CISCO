import type { ReactNode } from "react";

export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-dashed border-line px-6 py-12 text-center">
      <p className="text-sm font-medium text-snow">{title}</p>
      <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-mist">{body}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-danger/35 bg-danger/10 px-4 py-3 text-sm text-danger">
      {message}
    </div>
  );
}
