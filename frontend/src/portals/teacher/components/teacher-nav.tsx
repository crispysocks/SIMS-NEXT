import { LayoutDashboard, Users, UserCog, School, ClipboardList, BarChart3, Bot } from 'lucide-react';
import { GraduationCap } from 'lucide-react';
import { Sidebar, type NavItem } from '@/shared/components/sidebar';

const ITEMS: NavItem[] = [
  { to: '/teacher/dashboard', label: '工作台', icon: <LayoutDashboard className="w-4 h-4" /> },
  { to: '/teacher/students', label: '学生', icon: <Users className="w-4 h-4" /> },
  { to: '/teacher/teachers', label: '教师', icon: <UserCog className="w-4 h-4" /> },
  { to: '/teacher/classes', label: '班级', icon: <School className="w-4 h-4" /> },
  { to: '/teacher/scores', label: '成绩', icon: <ClipboardList className="w-4 h-4" /> },
  { to: '/teacher/analysis', label: '教学分析', icon: <BarChart3 className="w-4 h-4" /> },
  { to: '/teacher/agent', label: 'AI 助手', icon: <Bot className="w-4 h-4" /> },
];

export function TeacherNav() {
  return (
    <Sidebar
      logo={
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] flex items-center justify-center text-white">
            <GraduationCap className="w-5 h-5" />
          </div>
          <strong className="text-sm font-semibold text-[var(--text)]">SIMS·NEXT</strong>
        </div>
      }
      items={ITEMS}
    />
  );
}
