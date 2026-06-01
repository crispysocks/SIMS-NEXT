import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuthStore, type Role } from '@/shared/stores/auth-store';
import { useRoleGuard } from '@/shared/hooks/use-role-guard';

export function RoleGuard({ expectedRole, children }: { expectedRole: Role; children: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const currentRole = user?.role ?? null;
  const { allowed, redirectPath } = useRoleGuard({ expectedRole, currentRole });

  if (!allowed && redirectPath) {
    return <Navigate to={redirectPath} replace />;
  }

  return <>{children}</>;
}