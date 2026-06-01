import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface PageHeaderProps {
  title: string;
  description?: string;
  breadcrumbs?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function PageHeader({ title, description, breadcrumbs, actions, className }: PageHeaderProps) {
  return (
    <div className={cn('flex items-start justify-between gap-4 mb-6', className)}>
      <div className="space-y-1">
        {breadcrumbs && <div className="text-xs text-[var(--text-muted)] mb-1">{breadcrumbs}</div>}
        <h1 className="text-2xl font-semibold text-[var(--text)] tracking-tight">{title}</h1>
        {description && <p className="text-sm text-[var(--text-muted)] max-w-2xl">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2 flex-shrink-0">{actions}</div>}
    </div>
  );
}
