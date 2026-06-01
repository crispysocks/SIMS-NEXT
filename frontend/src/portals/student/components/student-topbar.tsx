import { NavLink } from 'react-router-dom';
import { GraduationCap, BookOpen, TrendingUp, Sparkles, MessageCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/shared/stores/auth-store';
import { UserMenu } from '@/shared/components/user-menu';

const NAV_ITEMS = [
  { to: '/student/dashboard', label: '首页', icon: GraduationCap },
  { to: '/student/tutor', label: '智能辅导', icon: BookOpen },
  { to: '/student/prediction', label: '升学预测', icon: TrendingUp },
  { to: '/student/novels', label: '四大名著', icon: Sparkles },
  { to: '/student/chat', label: 'AI 助教', icon: MessageCircle },
];

export function StudentTopbar() {
  const user = useAuthStore((s) => s.user);

  return (
    <header className="sticky top-0 z-30 h-16 bg-[var(--surface)]/80 backdrop-blur border-b border-[var(--border)]">
      <div className="h-full max-w-7xl mx-auto px-6 flex items-center gap-8">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] flex items-center justify-center text-white">
            <GraduationCap className="w-5 h-5" />
          </div>
          <strong className="text-sm font-semibold text-[var(--text)]">SIMS·NEXT</strong>
        </div>

        <nav className="flex items-center gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-1.5 px-3 h-9 rounded-md text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-[var(--primary-soft)] text-[var(--primary)]'
                    : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)]'
                )
              }
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto">
          <UserMenu name={user?.name ?? '学生'} />
        </div>
      </div>
    </header>
  );
}
