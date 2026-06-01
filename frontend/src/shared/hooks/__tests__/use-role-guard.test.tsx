import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useRoleGuard } from '../use-role-guard';
import { MemoryRouter } from 'react-router-dom';

function wrapper({ children }: { children: React.ReactNode }) {
  return <MemoryRouter initialEntries={['/student/dashboard']}>{children}</MemoryRouter>;
}

describe('useRoleGuard', () => {
  it('returns allowed=true when role matches path', () => {
    const { result } = renderHook(
      () => useRoleGuard({ expectedRole: 'student', currentRole: 'student' }),
      { wrapper }
    );
    expect(result.current).toEqual({ allowed: true, redirectPath: null });
  });

  it('returns redirect when role does not match', () => {
    const { result } = renderHook(
      () => useRoleGuard({ expectedRole: 'student', currentRole: 'teacher' }),
      { wrapper }
    );
    expect(result.current.allowed).toBe(false);
    expect(result.current.redirectPath).toBe('/teacher/dashboard');
  });
});