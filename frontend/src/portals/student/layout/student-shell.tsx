import { Outlet } from 'react-router-dom';
import { StudentTopbar } from '../components/student-topbar';

export function StudentShell() {
  return (
    <div className="min-h-screen bg-[var(--background)]">
      <StudentTopbar />
      <main className="max-w-7xl mx-auto px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
