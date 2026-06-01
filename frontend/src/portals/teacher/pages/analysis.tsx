import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingDown, AlertTriangle, Sparkles, Loader2 } from 'lucide-react';
import { PageHeader } from '@/shared/components/page-header';
import { ChartCard } from '@/shared/components/chart-card';
import { LineChart } from '@/shared/charts/line-chart';
import { Heatmap, type HeatmapPoint } from '@/shared/charts/heatmap';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { SectionErrorBoundary } from '@/shared/components/error-boundary';
import { analysisApi, type AnalysisInsight, type AnalysisTrendPoint } from '@/shared/api/analysis';
import { cn } from '@/lib/utils';

// Placeholder until T4 wires the real class context (teacher's currently
// selected class). The backend keys analysis by class_id (int), so we need
// *some* concrete value to query against.
const CLASS_ID = 1;

// Deterministic fallback data used when the backend has no exams / KPs for
// the class yet. Replaces the prior `Math.random()` heatmap.
const FALLBACK_TRENDS: AnalysisTrendPoint[] = [
  { exam: '月1', avg: 72, top: 92 },
  { exam: '月2', avg: 75, top: 94 },
  { exam: '月3', avg: 78, top: 95 },
  { exam: '期中', avg: 76, top: 96 },
  { exam: '月4', avg: 81, top: 98 },
];

const FALLBACK_HEATMAP_X = ['代数', '几何', '函数', '概率', '统计', '应用', '推理', '建模'];
const FALLBACK_HEATMAP_Y = ['班1', '班2', '班3', '班4', '班5', '班6', '班7', '班8'];

// 8×8 grid of deterministic mastery values so the visualization is stable
// across renders. Values picked to span the full visualMap range (0-100).
const FALLBACK_HEATMAP_POINTS: HeatmapPoint[] = (() => {
  const out: HeatmapPoint[] = [];
  for (let y = 0; y < FALLBACK_HEATMAP_Y.length; y++) {
    for (let x = 0; x < FALLBACK_HEATMAP_X.length; x++) {
      // Deterministic blend that varies along both axes — no Math.random.
      const value = ((x * 13 + y * 23) % 100);
      out.push({ x, y, value });
    }
  }
  return out;
})();

function levelClasses(level: AnalysisInsight['level']): { wrap: string; icon: string } {
  if (level === 'danger') {
    return {
      wrap: 'bg-[var(--danger-soft)] text-[var(--danger)]',
      icon: 'text-[var(--danger)]',
    };
  }
  if (level === 'warning') {
    return {
      wrap: 'bg-[var(--accent-soft)] text-[var(--accent)]',
      icon: 'text-[var(--accent)]',
    };
  }
  return {
    wrap: 'bg-[var(--surface-2)] text-[var(--text-muted)]',
    icon: 'text-[var(--text-muted)]',
  };
}

export function Analysis() {
  const [examName, setExamName] = useState<string | undefined>(undefined);

  // Pull the exam list separately so the picker keeps working even when the
  // main analysis query is loading / has errored.
  const { data: exams } = useQuery({
    queryKey: ['analysis', 'exams', CLASS_ID],
    queryFn: () => analysisApi.listExams(CLASS_ID),
  });

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['analysis', CLASS_ID, examName ?? '__all__'],
    queryFn: () => analysisApi.analyze({ class_id: CLASS_ID, exam_name: examName }),
  });

  // Trends: prefer backend data when present; fall back to the placeholder
  // 5-exam series so the chart never renders empty.
  const trendData = useMemo(() => {
    if (data?.trends && data.trends.length > 0) return data.trends;
    return FALLBACK_TRENDS;
  }, [data?.trends]);

  // Heatmap: same idea — backend data wins, otherwise show the deterministic
  // 8×8 placeholder. Replaces the prior `Math.random()` placeholder.
  const heatmap = useMemo(() => {
    if (data?.heatmap && data.heatmap.length > 0) {
      return {
        points: data.heatmap,
        xLabels: data.heatmapXLabels,
        yLabels: data.heatmapYLabels,
        description: `${data.heatmapYLabels.length} 个知识点 × ${data.heatmapXLabels.length} 场考试`,
        footer: '颜色越深，掌握度越高（基于班级真实成绩）',
      };
    }
    return {
      points: FALLBACK_HEATMAP_POINTS,
      xLabels: FALLBACK_HEATMAP_X,
      yLabels: FALLBACK_HEATMAP_Y,
      description: `${FALLBACK_HEATMAP_Y.length} 个班级 × ${FALLBACK_HEATMAP_X.length} 个知识点 (示例数据)`,
      footer: '颜色越深，掌握度越高',
    };
  }, [data?.heatmap, data?.heatmapXLabels, data?.heatmapYLabels]);

  const insights = data?.insights ?? [];
  const risks = useMemo(
    () => insights.filter((i) => i.level === 'warning' || i.level === 'danger'),
    [insights],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="教学分析"
        description="学情诊断 · 趋势分析 · 风险预警"
        actions={
          <div className="flex items-center gap-2 flex-wrap">
            <Button
              variant={examName === undefined ? 'default' : 'outline'}
              size="sm"
              onClick={() => setExamName(undefined)}
            >
              全部
            </Button>
            {(exams ?? []).slice(0, 5).map((e) => (
              <Button
                key={e.id}
                variant={examName === e.name ? 'default' : 'outline'}
                size="sm"
                onClick={() => setExamName(e.name)}
              >
                {e.name}
              </Button>
            ))}
            {isFetching && (
              <Loader2 className="w-4 h-4 animate-spin text-[var(--text-muted)]" />
            )}
          </div>
        }
      />

      {isError && (
        <Card className="p-4 border border-[var(--danger)]/30 bg-[var(--danger-soft)]/30">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-[var(--danger)]">
              分析数据加载失败：{(error as Error)?.message ?? String(error)}
            </p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              重试
            </Button>
          </div>
        </Card>
      )}

      {data?.summary && (
        <Card className="p-4 flex items-start gap-3 bg-[var(--primary-soft)]/30">
          <Sparkles className="w-5 h-5 text-[var(--primary)] shrink-0 mt-0.5" />
          <p className="text-sm text-[var(--text)]">{data.summary}</p>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SectionErrorBoundary>
          <ChartCard
            title="班级成绩趋势"
            description={
              data?.trends && data.trends.length > 0
                ? `最近 ${data.trends.length} 次考试`
                : '示例数据（暂无班级成绩）'
            }
          >
            <LineChart
              xKey="exam"
              data={trendData as unknown as Array<Record<string, string | number>>}
              series={[
                { dataKey: 'avg', name: '班级平均', color: 'var(--chart-1)' },
                ...(trendData.some((t) => t.top !== undefined)
                  ? [{ dataKey: 'top', name: '最高分', color: 'var(--chart-4)' }]
                  : []),
              ]}
            />
          </ChartCard>
        </SectionErrorBoundary>

        <SectionErrorBoundary>
          <ChartCard
            title="知识点掌握度热力图"
            description={heatmap.description}
            footer={heatmap.footer}
          >
            <Heatmap
              xLabels={heatmap.xLabels}
              yLabels={heatmap.yLabels}
              points={heatmap.points}
            />
          </ChartCard>
        </SectionErrorBoundary>
      </div>

      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-4 h-4 text-[var(--primary)]" />
          <h3 className="text-sm font-semibold text-[var(--text)]">AI 洞察</h3>
          {insights.length > 0 && (
            <Badge variant="secondary" className="ml-auto">
              {insights.length} 项
            </Badge>
          )}
        </div>
        {isLoading ? (
          <p className="text-xs text-[var(--text-muted)] py-4">加载中...</p>
        ) : insights.length === 0 ? (
          <p className="text-xs text-[var(--text-muted)] py-4 text-center">
            暂无 AI 洞察 — 等后端有班级成绩数据后会自动出现
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {insights.map((insight, i) => {
              const cls = levelClasses(insight.level);
              return (
                <div
                  key={i}
                  className="flex items-start gap-3 p-3 rounded-md hover:bg-[var(--surface-2)] transition-colors"
                >
                  <div
                    className={cn(
                      'w-8 h-8 rounded-full flex items-center justify-center shrink-0',
                      cls.wrap,
                    )}
                  >
                    <AlertTriangle className={cn('w-4 h-4', cls.icon)} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[var(--text)] truncate">
                      {insight.title}
                    </p>
                    <p className="text-xs text-[var(--text-muted)] mt-0.5">
                      {insight.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-4 h-4 text-[var(--warning)]" />
          <h3 className="text-sm font-semibold text-[var(--text)]">风险预警</h3>
          <Badge variant="secondary" className="ml-auto">
            {risks.length} 项
          </Badge>
        </div>
        {risks.length === 0 ? (
          <p className="text-xs text-[var(--text-muted)] py-4 text-center">
            暂无风险预警
          </p>
        ) : (
          <div className="space-y-2">
            {risks.map((r, i) => (
              <div
                key={i}
                className="flex items-center gap-3 p-3 rounded-md hover:bg-[var(--surface-2)]"
              >
                <div className="w-8 h-8 rounded-full bg-[var(--danger-soft)] flex items-center justify-center text-[var(--danger)]">
                  <TrendingDown className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[var(--text)] truncate">
                    {r.title}
                  </p>
                  <p className="text-xs text-[var(--text-muted)]">{r.description}</p>
                </div>
                <button className="text-xs text-[var(--primary)] font-medium shrink-0">
                  查看详情
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
