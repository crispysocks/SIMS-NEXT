import type { Role } from '@/shared/stores/auth-store';

export interface LoginPayload {
  account: string;
  password: string;
  remember: boolean;
  role: Role;
}

export interface LoginResponse {
  id: string;
  userId: number;
  name: string;
  role: Role;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const authApi = {
  async login(payload: LoginPayload): Promise<LoginResponse> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: payload.account,
        password: payload.password,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: '登录失败' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    // Backend returns { access_token, user: { id, username, role } }
    return {
      id: String(data.user.id),
      userId: data.user.id,
      name: data.user.username, // No separate "name" field in DB; use username
      role: data.user.role as Role,
    };
  },
};
