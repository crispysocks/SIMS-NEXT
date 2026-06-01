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
const Prediction = lazy(() => import('@/portals/student/pages/prediction').then((m) => ({ default: m.Prediction })));
const TeacherDashboard = lazy(() => import('@/portals/teacher/pages/dashboard').then((m) => ({ default: m.TeacherDashboard })));
const Students = lazy(() => import('@/portals/teacher/pages/students').then((m) => ({ default: m.Students })));
const Classes = lazy(() => import('@/portals/teacher/pages/classes').then((m) => ({ default: m.Classes })));
const Teachers = lazy(() => import('@/portals/teacher/pages/teachers').then((m) => ({ default: m.Teachers })));
const Scores = lazy(() => import('@/portals/teacher/pages/scores').then((m) => ({ default: m.Scores })));
const Analysis = lazy(() => import('@/portals/teacher/pages/analysis').then((m) => ({ default: m.Analysis })));

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
      { path: 'prediction', element: withSuspense(<Prediction />) },
    ],
  },
  {
    path: '/teacher',
    element: <ProtectedRoute>{withSuspense(<RoleGuard expectedRole="teacher"><TeacherShell /></RoleGuard>)}</ProtectedRoute>,
    children: [
      { index: true, element: <Navigate to="/teacher/dashboard" replace /> },
      { path: 'dashboard', element: withSuspense(<TeacherDashboard />) },
      { path: 'students', element: withSuspense(<Students />) },
      { path: 'classes', element: withSuspense(<Classes />) },
      { path: 'teachers', element: withSuspense(<Teachers />) },
      { path: 'scores', element: withSuspense(<Scores />) },
      { path: 'analysis', element: withSuspense(<Analysis />) },
    ],
  },
  { path: '/', element: <Navigate to="/login" replace /> },
  { path: '*', element: <Navigate to="/login" replace /> },
]);
