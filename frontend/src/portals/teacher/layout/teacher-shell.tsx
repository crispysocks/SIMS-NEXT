import { Outlet } from 'react-router-dom';

export function TeacherShell() {
  return (
    <div className="min-h-screen bg-[var(--background)]">
      <Outlet />
    </div>
  );
}
