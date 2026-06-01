import { Link } from 'react-router-dom';
import { ArrowRight, BookOpen } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/shared/components/loading';

export interface StudyTask {
  subject: string;
  topic: string;
  estimatedMinutes: number;
}

export function StudyTodayCard({ tasks, loading }: { tasks: StudyTask[]; loading?: boolean }) {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide">今日学习</p>
          <h3 className="text-lg font-semibold text-[var(--text)] mt-1">{tasks.length} 个任务待完成</h3>
        </div>
        <Button asChild>
          <Link to="/student/tutor">开始学习<ArrowRight className="w-4 h-4 ml-1" /></Link>
        </Button>
      </div>
      <div className="space-y-2">
        {loading ? (
          Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-12" />)
        ) : tasks.length === 0 ? (
          <p className="text-sm text-[var(--text-muted)] text-center py-6">今日学习任务已完成 🎉</p>
        ) : (
          tasks.map((t, i) => (
            <div key={i} className="flex items-center gap-3 p-3 rounded-md hover:bg-[var(--surface-2)]">
              <div className="w-9 h-9 rounded-md bg-[var(--primary-soft)] flex items-center justify-center text-[var(--primary)]">
                <BookOpen className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[var(--text)]">{t.subject} · {t.topic}</p>
                <p className="text-xs text-[var(--text-muted)]">预计 {t.estimatedMinutes} 分钟</p>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}
