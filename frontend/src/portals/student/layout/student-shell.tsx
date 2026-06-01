import { Outlet } from 'react-router-dom';

export function StudentShell() {
  return (
    <div className="min-h-screen bg-[var(--background)]">
      <Outlet />
    </div>
  );
}
