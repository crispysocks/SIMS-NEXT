import { createBrowserRouter, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { useAuthStore } from '@/shared/stores/auth-store';
import { RouteLoader } from '@/shared/components/loading';
import { RoleGuard } from '@/portals/auth/components/role-guard';

// Lazy load pages
const LoginPage = lazy(() => import('@/portals/auth/pages/login-page').then((m) => ({ default: m.LoginPage })));
const StudentShell = lazy(() => import('@/portals/student/layout/student-shell').then((m) => ({ default: m.StudentShell })));
const TeacherShell = lazy(() => import('@/portals/teacher/layout/teacher-shell').then((m) => ({ default: m.TeacherShell })));
const StudentDashboard = lazy(() => import('@/portals/student/pages/dashboard').then((m) => ({ default: m.StudentDashboard })));
const TeacherDashboard = lazy(() => import('@/portals/teacher/pages/dashboard').then((m) => ({ default: m.TeacherDashboard })));

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthed = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthed) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function withSuspense(node: React.ReactNode) {
  return <Suspense fallback={<RouteLoader />}>{node}</Suspense>;
}

export const router = createBrowserRouter([
  { path: '/login', element: withSuspense(<LoginPage />) },
  {
    path: '/student',
    element: <ProtectedRoute>{withSuspense(<RoleGuard expectedRole="student"><StudentShell /></RoleGuard>)}</ProtectedRoute>,
    children: [
      { index: true, element: <Navigate to="/student/dashboard" replace /> },
      { path: 'dashboard', element: withSuspense(<StudentDashboard />) },
    ],
  },
  {
    path: '/teacher',
    element: <ProtectedRoute>{withSuspense(<RoleGuard expectedRole="teacher"><TeacherShell /></RoleGuard>)}</ProtectedRoute>,
    children: [
      { index: true, element: <Navigate to="/teacher/dashboard" replace /> },
      { path: 'dashboard', element: withSuspense(<TeacherDashboard />) },
    ],
  },
  { path: '/', element: <Navigate to="/login" replace /> },
  { path: '*', element: <Navigate to="/login" replace /> },
]);
