import type { ReactNode } from 'react';
import { Inbox } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 px-6 text-center', className)}>
      <div className="w-12 h-12 rounded-full bg-[var(--surface-2)] flex items-center justify-center text-[var(--text-subtle)] mb-3">
        {icon ?? <Inbox className="w-6 h-6" />}
      </div>
      <h3 className="text-sm font-medium text-[var(--text)] mb-1">{title}</h3>
      {description && <p className="text-xs text-[var(--text-muted)] max-w-sm mb-4">{description}</p>}
      {action}
    </div>
  );
}
