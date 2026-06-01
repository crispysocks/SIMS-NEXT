import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

// 1. TopLoader — Top progress bar (bound to route events; static component shown here)
export function TopLoader({ progress = 0, visible = false }: { progress?: number; visible?: boolean }) {
  if (!visible) return null;
  return (
    <div className="fixed top-0 left-0 right-0 z-50 h-[3px] bg-transparent pointer-events-none">
      <div
        className="h-full bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] transition-all duration-200"
        style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
      />
    </div>
  );
}

// 2. RouteLoader — Page-level skeleton
export function RouteLoader({ message = '加载中...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
      <Loader2 className="w-8 h-8 animate-spin text-[var(--primary)]" />
      <p className="text-sm text-[var(--text-muted)]">{message}</p>
    </div>
  );
}

// 3. Skeleton — Block-level skeleton with shimmer
export function Skeleton({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <div
      className={cn(
        'rounded-md bg-[var(--skeleton)] relative overflow-hidden',
        'before:absolute before:inset-0 before:-translate-x-full',
        'before:bg-gradient-to-r before:from-transparent before:via-[var(--skeleton-shimmer)] before:to-transparent',
        'before:animate-[shimmer_1.5s_infinite]',
        className
      )}
      style={style}
    />
  );
}

// 4. ButtonSpinner — In-button spinner
export function ButtonSpinner({ className }: { className?: string }) {
  return <Loader2 className={cn('w-4 h-4 animate-spin', className)} />;
}

// 5. TableSkeleton — Table skeleton
export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-3">
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton key={c} className="h-8 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}