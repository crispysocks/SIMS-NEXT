import { GraduationCap } from 'lucide-react';

export function BrandPanel() {
  return (
    <div
      className="flex flex-col justify-between h-full p-12 text-white"
      style={{
        background: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)',
      }}
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center">
          <GraduationCap className="w-6 h-6" />
        </div>
        <strong className="text-lg font-semibold tracking-tight">SIMS·NEXT</strong>
      </div>

      <div className="space-y-4 max-w-md">
        <h1 className="text-4xl font-bold leading-tight">智能教学，因材施教</h1>
        <p className="text-base text-white/80 leading-relaxed">
          AI 驱动的 K12 教学平台，覆盖教务、教学、辅导、升学全流程。
        </p>
        <ul className="space-y-2 text-sm text-white/70">
          <li>• AI 教学分析，学情一目了然</li>
          <li>• 自适应辅导，掌握度智能追踪</li>
          <li>• 升学预测与个性化建议</li>
        </ul>
      </div>

      <p className="text-xs text-white/50">© 2026 SIMS·NEXT</p>
    </div>
  );
}