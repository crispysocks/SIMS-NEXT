import { StudyTodayCard } from '../components/study-today-card';
import { MasteryRing } from '../components/mastery-ring';
import { ProgressBanner } from '../components/progress-banner';
import { Card } from '@/components/ui/card';
import { PageHeader } from '@/shared/components/page-header';

export function StudentDashboard() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="欢迎回来，小明 👋"
        description="这是你的学习中心，今天也一起加油吧。"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <ProgressBanner daysLeft={127} school="市重点高中" probability={82} topSubject="数学" />
          <StudyTodayCard
            tasks={[
              { subject: '数学', topic: '二次函数综合', estimatedMinutes: 25 },
              { subject: '英语', topic: '完形填空 - 时态', estimatedMinutes: 20 },
              { subject: '数学', topic: '几何证明', estimatedMinutes: 30 },
            ]}
          />
        </div>
        <Card className="p-6 flex flex-col items-center justify-center">
          <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide mb-4">综合掌握度</p>
          <MasteryRing value={76} size={160} strokeWidth={10} />
          <p className="text-xs text-[var(--text-muted)] mt-4 text-center">
            最近 7 天提升 <span className="text-[var(--success)] font-semibold">+8.2%</span>
          </p>
        </Card>
      </div>
    </div>
  );
}
