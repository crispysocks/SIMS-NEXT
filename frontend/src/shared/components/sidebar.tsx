import type { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';

export interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
}

export function Sidebar({ logo, items, footer }: { logo: ReactNode; items: NavItem[]; footer?: ReactNode }) {
  return (
    <aside className="w-64 h-screen sticky top-0 flex flex-col bg-[var(--surface)] border-r border-[var(--border)]">
      <div className="h-16 flex items-center px-6 border-b border-[var(--border)]">{logo}</div>
      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-[var(--primary-soft)] text-[var(--primary)]'
                  : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)]'
              )
            }
          >
            <span className="w-4 h-4 flex items-center justify-center">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      {footer && <div className="p-3 border-t border-[var(--border)]">{footer}</div>}
    </aside>
  );
}
