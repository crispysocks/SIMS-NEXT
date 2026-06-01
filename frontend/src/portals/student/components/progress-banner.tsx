import { TrendingUp, Sparkles } from 'lucide-react';
import { Card } from '@/components/ui/card';

export function ProgressBanner({ daysLeft, school, probability, topSubject }: {
  daysLeft: number;
  school: string;
  probability: number;
  topSubject: string;
}) {
  return (
    <Card
      className="p-6 text-white relative overflow-hidden"
      style={{ background: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)' }}
    >
      <div className="absolute top-0 right-0 w-32 h-32 rounded-full bg-white/5 -translate-y-12 translate-x-12" />
      <div className="relative space-y-3">
        <div className="flex items-center gap-2 text-white/80">
          <Sparkles className="w-4 h-4" />
          <span className="text-xs">距 {school} 入学考试</span>
        </div>
        <div>
          <span className="text-4xl font-bold tabular-nums">{daysLeft}</span>
          <span className="text-lg ml-2">天</span>
        </div>
        <div className="flex items-center gap-4 pt-2 border-t border-white/20">
          <div>
            <p className="text-xs text-white/70">你的预测概率</p>
            <p className="text-xl font-semibold mt-0.5">{probability}%</p>
          </div>
          <div className="h-8 w-px bg-white/20" />
          <div>
            <p className="text-xs text-white/70">最强学科</p>
            <p className="text-xl font-semibold mt-0.5 flex items-center gap-1">
              {topSubject} <TrendingUp className="w-4 h-4" />
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}
