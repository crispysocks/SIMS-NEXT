import { useLocation } from 'react-router-dom';

type Role = 'student' | 'teacher';

export interface UseRoleGuardArgs {
  expectedRole: Role;
  currentRole: Role | null;
}

export interface RoleGuardResult {
  allowed: boolean;
  redirectPath: string | null;
}

const ROLE_HOME: Record<Role, string> = {
  student: '/student/dashboard',
  teacher: '/teacher/dashboard',
};

export function useRoleGuard({ expectedRole, currentRole }: UseRoleGuardArgs): RoleGuardResult {
  useLocation(); // Trigger route subscription (useful for HMR)

  if (!currentRole) {
    return { allowed: false, redirectPath: '/login' };
  }

  if (currentRole === expectedRole) {
    return { allowed: true, redirectPath: null };
  }

  // Mismatch → redirect to current user's role home (NOT the visited path's home)
  return { allowed: false, redirectPath: ROLE_HOME[currentRole] };
}