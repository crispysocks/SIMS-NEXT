import { Outlet } from 'react-router-dom';
import { TeacherNav } from '../components/teacher-nav';
import { TopBar } from '@/shared/components/top-bar';
import { useAuthStore } from '@/shared/stores/auth-store';

export function TeacherShell() {
  const user = useAuthStore((s) => s.user);
  return (
    <div className="flex min-h-screen bg-[var(--background)]">
      <TeacherNav />
      <div className="flex-1 min-w-0 flex flex-col">
        <TopBar userName={user?.name ?? '老师'} />
        <main className="flex-1 px-8 py-6 overflow-x-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
