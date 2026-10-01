export function SkeletonLine({ width = "100%" }: { width?: string }) {
  return <div className="skeleton h-4" style={{ width }} />;
}

export function SkeletonCard() {
  return (
    <div className="card p-5 space-y-3">
      <SkeletonLine width="40%" />
      <SkeletonLine width="90%" />
      <SkeletonLine width="70%" />
    </div>
  );
}

export function SkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
