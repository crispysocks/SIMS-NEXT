import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, LogOut, User as UserIcon } from 'lucide-react';
import { useAuthStore } from '@/shared/stores/auth-store';

export function UserMenu({ name }: { name: string }) {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 h-9 px-2 rounded-md hover:bg-[var(--surface-2)]"
      >
        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] flex items-center justify-center text-white text-xs font-semibold">
          {name[0]}
        </div>
        <span className="text-sm text-[var(--text)]">{name}</span>
        <ChevronDown className="w-3 h-3 text-[var(--text-muted)]" />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-1 z-50 w-40 rounded-lg border border-[var(--border)] bg-[var(--surface)] shadow-md p-1">
            <button className="w-full flex items-center gap-2 px-3 py-1.5 text-sm rounded-md hover:bg-[var(--surface-2)] text-[var(--text)]">
              <UserIcon className="w-3.5 h-3.5" />个人资料
            </button>
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-3 py-1.5 text-sm rounded-md hover:bg-[var(--surface-2)] text-[var(--danger)]"
            >
              <LogOut className="w-3.5 h-3.5" />退出登录
            </button>
          </div>
        </>
      )}
    </div>
  );
}
