import type { ReactNode } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';

type Trend = 'up' | 'down' | 'flat';

export interface StatCardProps {
  label: string;
  value: string | number;
  delta?: string;
  trend?: Trend;
  icon?: ReactNode;
  helpText?: string;
  className?: string;
}

const trendStyles: Record<Trend, { color: string; Icon: typeof TrendingUp }> = {
  up: { color: 'text-[var(--success)]', Icon: TrendingUp },
  down: { color: 'text-[var(--danger)]', Icon: TrendingDown },
  flat: { color: 'text-[var(--text-muted)]', Icon: Minus },
};

export function StatCard({ label, value, delta, trend, icon, helpText, className }: StatCardProps) {
  const TrendInfo = trend ? trendStyles[trend] : null;
  return (
    <Card className={cn('p-6', className)}>
      <div className="flex items-start justify-between">
        <div className="space-y-1.5">
          <p className="text-xs text-[var(--text-muted)] font-medium uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-semibold text-[var(--text)] tabular-nums">{value}</p>
          {helpText && <p className="text-xs text-[var(--text-subtle)]">{helpText}</p>}
        </div>
        {icon && (
          <div className="w-10 h-10 rounded-lg bg-[var(--primary-soft)] flex items-center justify-center text-[var(--primary)]">
            {icon}
          </div>
        )}
      </div>
      {delta && TrendInfo && (
        <div className={cn('flex items-center gap-1 mt-3 text-xs font-medium', TrendInfo.color)}>
          <TrendInfo.Icon className="w-3 h-3" />
          <span>{delta}</span>
        </div>
      )}
    </Card>
  );
}
