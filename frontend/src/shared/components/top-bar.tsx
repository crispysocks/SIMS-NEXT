import { Bell, Search, Sun, Moon } from 'lucide-react';
import { useTheme } from '@/shared/theme/ThemeProvider';
import { UserMenu } from './user-menu';

export function TopBar({ userName }: { userName: string }) {
  const { resolvedTheme, toggle } = useTheme();
  return (
    <header className="h-16 sticky top-0 z-30 bg-[var(--surface)]/80 backdrop-blur border-b border-[var(--border)]">
      <div className="h-full px-6 flex items-center gap-4">
        <div className="flex-1 max-w-md relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
          <input
            type="text"
            placeholder="搜索学生、班级、成绩..."
            className="w-full h-9 pl-9 pr-3 rounded-md bg-[var(--surface-2)] border-0 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
          />
        </div>
        <button className="w-9 h-9 rounded-md hover:bg-[var(--surface-2)] flex items-center justify-center text-[var(--text-muted)]">
          <Bell className="w-4 h-4" />
        </button>
        <button
          onClick={toggle}
          className="w-9 h-9 rounded-md hover:bg-[var(--surface-2)] flex items-center justify-center text-[var(--text-muted)]"
          title={resolvedTheme === 'dark' ? '切换到浅色' : '切换到深色'}
        >
          {resolvedTheme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
        <UserMenu name={userName} />
      </div>
    </header>
  );
}
