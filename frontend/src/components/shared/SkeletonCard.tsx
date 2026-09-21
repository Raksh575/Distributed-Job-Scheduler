import { cn } from "../../utils/cn";

interface SkeletonProps {
  className?: string;
}

export const Skeleton = ({ className }: SkeletonProps) => (
  <div className={cn("skeleton rounded", className)} />
);

export const SkeletonCard = ({ rows = 3 }: { rows?: number }) => (
  <div className="glass-card p-6 rounded-2xl space-y-4">
    <div className="flex items-center gap-3">
      <Skeleton className="h-10 w-10 rounded-xl" />
      <div className="space-y-2 flex-1">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-24" />
      </div>
    </div>
    {Array.from({ length: rows }).map((_, i) => (
      <Skeleton key={i} className={cn("h-3", i % 2 === 0 ? "w-full" : "w-4/5")} />
    ))}
  </div>
);

export const SkeletonTable = ({ rows = 5 }: { rows?: number }) => (
  <div className="glass-card rounded-2xl overflow-hidden">
    <div className="p-4 border-b border-white/5 flex gap-4">
      {[40, 30, 20].map((w, i) => (
        <Skeleton key={i} className={`h-3 w-${w}`} />
      ))}
    </div>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="flex items-center gap-4 px-4 py-3 border-b border-white/[0.03]">
        <Skeleton className="h-3 w-1/4" />
        <Skeleton className="h-3 w-1/5" />
        <Skeleton className="h-5 w-16 rounded-full" />
        <Skeleton className="h-3 w-1/6 ml-auto" />
      </div>
    ))}
  </div>
);

export const SkeletonMetrics = () => (
  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
    {Array.from({ length: 4 }).map((_, i) => (
      <div key={i} className="glass-card p-6 rounded-2xl">
        <div className="flex justify-between">
          <div className="space-y-3">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-3 w-14" />
          </div>
          <Skeleton className="h-12 w-12 rounded-xl" />
        </div>
      </div>
    ))}
  </div>
);
