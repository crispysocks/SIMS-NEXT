import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface RoleCardProps {
  icon: ReactNode;
  title: string;
  description: string;
  selected: boolean;
  onClick: () => void;
}

export function RoleCard({ icon, title, description, selected, onClick }: RoleCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full flex items-center gap-4 p-4 rounded-lg border-2 transition-all text-left',
        'hover:border-[var(--primary)] hover:bg-[var(--primary-soft)]/30',
        selected
          ? 'border-[var(--primary)] bg-[var(--primary-soft)]/50 shadow-sm'
          : 'border-[var(--border)] bg-[var(--surface)]'
      )}
    >
      <div
        className={cn(
          'w-12 h-12 rounded-lg flex items-center justify-center text-2xl flex-shrink-0',
          selected ? 'bg-[var(--primary)] text-white' : 'bg-[var(--surface-2)] text-[var(--text-muted)]'
        )}
      >
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold text-[var(--text)]">{title}</div>
        <div className="text-xs text-[var(--text-muted)] mt-0.5">{description}</div>
      </div>
      <div className={cn('text-lg', selected ? 'text-[var(--primary)]' : 'text-[var(--text-subtle)]')}>→</div>
    </button>
  );
}