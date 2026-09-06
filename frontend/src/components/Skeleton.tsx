export function Skeleton({ className = "h-24" }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl border border-line bg-raised/60 ${className}`} />;
}

export function PageSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-16" />
      <div className="grid gap-4 md:grid-cols-3">
        <Skeleton />
        <Skeleton />
        <Skeleton />
      </div>
      <Skeleton className="h-64" />
    </div>
  );
}
