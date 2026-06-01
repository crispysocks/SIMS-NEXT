import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { predictionApi } from '@/shared/api/prediction';
import type { PredictionItem, StudentPrediction } from '@/shared/api/prediction';
import { PageHeader } from '@/shared/components/page-header';
import { SectionErrorBoundary } from '@/shared/components/error-boundary';
import { ChartCard } from '@/shared/components/chart-card';
import { RadarChart } from '@/shared/charts/radar-chart';
import { RadialGauge } from '@/shared/charts/radial-gauge';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/shared/components/loading';
import { WhatIfSlider } from '../components/what-if-slider';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';

// TODO(T4): replace with useAuthStore().userId
const STUDENT_ID = 1;

// Backend returns per-tier `PredictionItem[]` (each item carries an
// `admission_probability`). We average the admission probabilities within
// each tier to get a single probability for the gauge. Falls back to 0
// when the tier is missing or the model is untrained.
function tierProbability(items: PredictionItem[] | undefined): number {
  if (!items || items.length === 0) return 0;
  const avg =
    items.reduce((sum, it) => sum + (it.admission_probability || 0), 0) /
    items.length;
  return Math.round(avg);
}

export function Prediction() {
  const [boost, setBoost] = useState(0);

  const {
    data: prediction,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['predict', STUDENT_ID],
    queryFn: () => predictionApi.get(STUDENT_ID),
    retry: 1,
  });

  // Portrait powers a small summary card. Failures here are non-blocking.
  const { data: portrait } = useQuery({
    queryKey: ['predict', STUDENT_ID, 'portrait'],
    queryFn: () => predictionApi.getPortrait(STUDENT_ID),
    retry: 0,
  });

  const chaseProb = useMemo(
    () => tierProbability(prediction?.predictions['冲刺']),
    [prediction],
  );
  const stableProb = useMemo(
    () => tierProbability(prediction?.predictions['稳定']),
    [prediction],
  );
  const safeProb = useMemo(
    () => tierProbability(prediction?.predictions['保底']),
    [prediction],
  );

  // Base probability for the chase gauge. The what-if slider adjusts this.
  const baseProb = chaseProb || stableProb || safeProb || 0;
  const currentProb = Math.min(99, baseProb + Math.round(boost * 0.6));

  return (
    <div className="space-y-6">
      <PageHeader
        title="升学预测"
        description="基于 ML 模型的学生画像与概率预测"
      />

      <SectionErrorBoundary>
        {isLoading ? (
          <Skeleton className="h-72" />
        ) : (
          <Card className="p-6">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <Stat label="当前总分" value={prediction ? `${prediction.current_score}` : '—'} />
              <Stat label="当前排名" value={prediction ? `${prediction.current_ranking}` : '—'} />
              <Stat label="预测排名" value={prediction ? `${prediction.predicted_ranking}` : '—'} />
              <Stat
                label="排名趋势"
                value={prediction?.ranking_trend ?? '—'}
                tone={prediction?.ranking_trend === '上升' ? 'success' : prediction?.ranking_trend === '下降' ? 'danger' : 'muted'}
              />
            </div>
            {error && (
              <p className="mt-3 text-xs text-[var(--text-muted)]">
                预测模型暂未训练，显示默认占位数据。
              </p>
            )}
          </Card>
        )}
      </SectionErrorBoundary>

      <Tabs defaultValue="chase">
        <TabsList>
          <TabsTrigger value="chase">冲刺</TabsTrigger>
          <TabsTrigger value="stable">稳定</TabsTrigger>
          <TabsTrigger value="safe">保底</TabsTrigger>
        </TabsList>
        <TabsContent value="chase" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="p-6">
              <RadialGauge value={currentProb} label="市重点概率" color="var(--chart-1)" height={220} />
            </Card>
            <div className="lg:col-span-2">
              <ChartCard title="多维能力评估" description="基于最近 5 次考试">
                <RadarChart
                  angleKey="subject"
                  dataKey="score"
                  data={[
                    { subject: '代数', score: 80 },
                    { subject: '几何', score: 70 },
                    { subject: '函数', score: 85 },
                    { subject: '概率', score: 65 },
                    { subject: '应用', score: 75 },
                  ]}
                />
              </ChartCard>
            </div>
            <div className="lg:col-span-3">
              <WhatIfSlider baseScore={baseProb} onChange={setBoost} />
            </div>
          </div>
        </TabsContent>
        <TabsContent value="stable" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="p-6">
              <RadialGauge value={stableProb} label="稳定校概率" color="var(--chart-2)" height={220} />
            </Card>
            <div className="lg:col-span-2">
              <ChartCard title="稳定校预测" description="根据当前分数与排名估算">
                <SchoolList items={prediction?.predictions['稳定'] ?? []} fallback="暂无数据" />
              </ChartCard>
            </div>
          </div>
        </TabsContent>
        <TabsContent value="safe" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="p-6">
              <RadialGauge value={safeProb} label="保底校概率" color="var(--chart-3)" height={220} />
            </Card>
            <div className="lg:col-span-2">
              <ChartCard title="保底校预测" description="录取概率 ≥ 80% 的学校">
                <SchoolList items={prediction?.predictions['保底'] ?? []} fallback="暂无数据" />
              </ChartCard>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {portrait && (
        <Card className="p-6">
          <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide mb-3">学生画像</p>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <Field label="学习类型" value={portrait.learning_type} />
            <Field label="理科能力" value={portrait.science_ability} />
            <Field label="英语能力" value={portrait.english_ability} />
            <Field label="提升潜力" value={portrait.improvement_potential} />
          </div>
        </Card>
      )}
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: 'success' | 'danger' | 'muted' }) {
  const toneClass =
    tone === 'success'
      ? 'text-[var(--success)]'
      : tone === 'danger'
        ? 'text-[var(--danger)]'
        : 'text-[var(--text)]';
  return (
    <div className="space-y-1">
      <p className="text-xs text-[var(--text-muted)]">{label}</p>
      <p className={`text-lg font-semibold tabular-nums ${toneClass}`}>{value}</p>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="space-y-1">
      <p className="text-xs text-[var(--text-muted)]">{label}</p>
      <p className="text-sm text-[var(--text)]">{value ?? '—'}</p>
    </div>
  );
}

function SchoolList({ items, fallback }: { items: PredictionItem[]; fallback: string }) {
  if (items.length === 0) {
    return <p className="text-sm text-[var(--text-muted)]">{fallback}</p>;
  }
  return (
    <ul className="space-y-2 text-sm">
      {items.map((it) => (
        <li
          key={`${it.school_name}-${it.admission_type}`}
          className="flex justify-between border-b border-[var(--border)] pb-2"
        >
          <span className="text-[var(--text)]">{it.school_name}</span>
          <span className="tabular-nums text-[var(--text-muted)]">
            预测 {it.predicted_score} · 录取概率 {it.admission_probability}%
          </span>
        </li>
      ))}
    </ul>
  );
}
