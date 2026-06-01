import type { ReactNode } from 'react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export interface ChartCardProps {
  title: string;
  description?: string;
  badge?: ReactNode;
  legend?: ReactNode;
  footer?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function ChartCard({ title, description, badge, legend, footer, action, children, className }: ChartCardProps) {
  return (
    <Card className={cn('p-6', className)}>
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-[var(--text)]">{title}</h3>
            {badge}
          </div>
          {description && <p className="text-xs text-[var(--text-muted)]">{description}</p>}
        </div>
        {action}
      </div>
      <div className="w-full">{children}</div>
      {(legend || footer) && (
        <div className="mt-4 pt-4 border-t border-[var(--border)] space-y-2">
          {legend && <div className="flex flex-wrap items-center gap-4 text-xs">{legend}</div>}
          {footer && <p className="text-xs text-[var(--text-subtle)]">{footer}</p>}
        </div>
      )}
    </Card>
  );
}

export function ChartLegend({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="w-2.5 h-2.5 rounded-sm" style={{ background: color }} />
      <span className="text-[var(--text-muted)]">{label}</span>
    </div>
  );
}
