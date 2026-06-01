import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { School2 } from 'lucide-react';
import { BrandPanel } from '../components/brand-panel';
import { RoleCard } from '../components/role-card';
import { LoginForm } from '../components/login-form';
import { useAuthStore } from '@/shared/stores/auth-store';
import { authApi } from '@/shared/api/auth';
import type { Role } from '@/shared/stores/auth-store';

export function LoginPage() {
  const [role, setRole] = useState<Role>('student');
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);

  const handleSubmit = async (values: { account: string; password: string; remember: boolean }) => {
    const user = await authApi.login({ ...values, role });
    login(user);
    navigate(user.role === 'student' ? '/student/dashboard' : '/teacher/dashboard');
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 min-h-screen bg-[var(--background)]">
      <BrandPanel />
      <div className="flex flex-col items-center justify-center p-8 lg:p-12">
        <div className="w-full max-w-sm space-y-8">
          <div className="space-y-2">
            <h2 className="text-2xl font-semibold text-[var(--text)]">欢迎回来</h2>
            <p className="text-sm text-[var(--text-muted)]">请选择你的身份开始</p>
          </div>

          <div className="space-y-3">
            <RoleCard
              icon="🎓"
              title="我是学生"
              description="学习中心 · 智能辅导 · 升学预测"
              selected={role === 'student'}
              onClick={() => setRole('student')}
            />
            <RoleCard
              icon={<School2 className="w-6 h-6" />}
              title="我是老师"
              description="工作台 · 教务管理 · 教学分析"
              selected={role === 'teacher'}
              onClick={() => setRole('teacher')}
            />
          </div>

          <LoginForm role={role} onSubmit={handleSubmit} />

          <p className="text-center text-xs text-[var(--text-muted)]">
            没有账号？<a href="/register" className="text-[var(--primary)] font-medium">学校注册</a>
          </p>
        </div>
      </div>
    </div>
  );
}
