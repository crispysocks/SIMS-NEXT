import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import {
  Users,
  GraduationCap,
  BookOpen,
  BarChart3,
  Shield,
  MessageSquare,
  Brain,
} from 'lucide-react';

const menuItems = [
  { path: '/chat', label: 'AI 助教', icon: MessageSquare },
  { path: '/students', label: '学生管理', icon: GraduationCap },
  { path: '/teachers', label: '教师管理', icon: Users },
  { path: '/classes', label: '班级管理', icon: BookOpen },
  { path: '/scores', label: '成绩管理', icon: BarChart3 },
  { path: '/prediction', label: '升学预测', icon: Brain },
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-slate-900 text-white min-h-screen">
      <div className="p-4 border-b border-slate-800">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Shield className="w-6 h-6" />
          SIMS-NEXT
        </h1>
      </div>
      <nav className="p-4 space-y-1">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
                isActive
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              )
            }
          >
            <item.icon className="w-5 h-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}