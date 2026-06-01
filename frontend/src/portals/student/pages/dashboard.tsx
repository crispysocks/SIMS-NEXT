import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/shared/stores/auth-store';
import { tutorApi, type Progress } from '@/shared/api/tutor';
import { predictionApi, type RiskWarning } from '@/shared/api/prediction';
import { StudyTodayCard, type StudyTask } from '../components/study-today-card';
import { MasteryRing } from '../components/mastery-ring';
import { ProgressBanner } from '../components/progress-banner';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/shared/components/loading';
import { SectionErrorBoundary } from '@/shared/components/error-boundary';
import { PageHeader } from '@/shared/components/page-header';

// Build placeholder study tasks from progress data so the right side of the
// dashboard always has *something* to show. Picks the 3 weakest mastery
// states; if the backend has nothing yet, returns an empty list and the card
// renders the empty-state copy.
function pickStudyTasks(progress: Progress | undefined): StudyTask[] {
  if (!progress) return [];
  return [...progress.mastery_states]
    .sort((a, b) => a.mastery - b.mastery)
    .slice(0, 3)
    .map((m, i) => ({
      subject: `主题${i + 1}`,
      topic: m.topic_id,
      estimatedMinutes: 20 + (i + 1) * 5,
    }));
}

function riskLabel(risk: RiskWarning | undefined): { text: string; tone: 'good' | 'warn' | 'bad' } {
  if (!risk) return { text: '暂无风险', tone: 'good' };
  const lvl = risk.risk_level;
  if (lvl === 'high' || lvl === 'danger') return { text: '风险偏高', tone: 'bad' };
  if (lvl === 'medium' || lvl === 'warning') return { text: '需关注', tone: 'warn' };
  return { text: '状态良好', tone: 'good' };
}

export function StudentDashboard() {
  const userId = useAuthStore((s) => s.user?.userId ?? 0);
  const name = useAuthStore((s) => s.user?.name ?? '同学');

  const { data: progress, isLoading: progressLoading } = useQuery({
    queryKey: ['tutor', 'progress'],
    queryFn: () => tutorApi.getProgress(),
  });

  const { data: risk } = useQuery({
    queryKey: ['predict', userId, 'risk'],
    queryFn: () => predictionApi.getRisk(userId),
    enabled: userId > 0,
  });

  const accuracy = progress ? Math.round(progress.accuracy * 100) : 0;
  const tasks = useMemo(() => pickStudyTasks(progress), [progress]);
  const riskInfo = riskLabel(risk);

  return (
    <div className="space-y-6">
      <PageHeader
        title={`欢迎回来，${name} 👋`}
        description="这是你的学习中心，今天也一起加油吧。"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <SectionErrorBoundary>
            {progressLoading ? (
              <Skeleton className="h-44" />
            ) : (
              <ProgressBanner
                daysLeft={127}
                school="市重点高中"
                probability={Math.max(0, Math.min(100, accuracy))}
                topSubject={riskInfo.text}
              />
            )}
          </SectionErrorBoundary>
          <StudyTodayCard tasks={tasks} loading={progressLoading} />
        </div>
        <Card className="p-6 flex flex-col items-center justify-center">
          <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide mb-4">综合掌握度</p>
          {progressLoading ? (
            <Skeleton className="h-40 w-40 rounded-full" />
          ) : (
            <MasteryRing value={accuracy} size={160} strokeWidth={10} />
          )}
          <p className="text-xs text-[var(--text-muted)] mt-4 text-center">
            最近 7 天提升 <span className="text-[var(--success)] font-semibold">+0%</span>
          </p>
        </Card>
      </div>
    </div>
  );
}
