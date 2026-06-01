import type { Role } from '@/shared/stores/auth-store';

export interface LoginPayload {
  account: string;
  password: string;
  remember: boolean;
  role: Role;
}

export const authApi = {
  async login(payload: LoginPayload) {
    // TODO: real auth endpoint. For now, mock.
    if (!payload.account || !payload.password) {
      throw new Error('请填写账号和密码');
    }
    return {
      id: '1',
      name: payload.role === 'student' ? '学生' : '老师',
      role: payload.role,
    };
  },
};
