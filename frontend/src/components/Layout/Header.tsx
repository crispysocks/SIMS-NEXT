import { useAuthStore } from '@/shared/stores/auth-store';
import { LogOut } from 'lucide-react';

export function Header() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6">
      <div className="text-slate-600 text-sm">
        智能教育平台 - 学生信息管理系统
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm text-slate-600">{user?.name}</span>
        <button
          onClick={logout}
          className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
        >
          <LogOut className="w-4 h-4" />
          退出
        </button>
      </div>
    </header>
  );
}