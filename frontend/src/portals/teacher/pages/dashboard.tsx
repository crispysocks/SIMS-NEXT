import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Users,
  TrendingUp,
  School,
  AlertTriangle,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { PageHeader } from '@/shared/components/page-header';
import { StatCard } from '@/shared/components/stat-card';
import { ChartCard, ChartLegend } from '@/shared/components/chart-card';
import { BarChart } from '@/shared/charts/bar-chart';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/shared/components/loading';
import { SectionErrorBoundary } from '@/shared/components/error-boundary';
import { studentsApi } from '@/shared/api/students';
import { scoresApi } from '@/shared/api/scores';
import { analysisApi } from '@/shared/api/analysis';
import { cn } from '@/lib/utils';

// Placeholder until T5 wires the real class context (teacher's currently
// selected class). Backend keys every list by class_id (int), so we need
// *some* concrete value to query against.
const CLASS_ID = 1;
const EXAM_NAME = '月4';
// Pass line (out of 100) used to derive the 及格率 stat.
const PASS_LINE = 60;

// Hardcoded distribution buckets — keeps the chart visually stable while the
// real histogram endpoint is still TBD. The values line up with a typical
// 45-student class to match the previous mock.
const DISTRIBUTION_DATA = [
  { range: '<60', 数学: 3, 语文: 2, 英语: 4 },
  { range: '60-69', 数学: 5, 语文: 6, 英语: 7 },
  { range: '70-79', 数学: 12, 语文: 14, 英语: 13 },
  { range: '80-89', 数学: 18, 语文: 16, 英语: 15 },
  { range: '90+', 数学: 7, 语文: 7, 英语: 6 },
];

const SERIES = [
  { dataKey: '数学', name: '数学', color: 'var(--chart-1)' },
  { dataKey: '语文', name: '语文', color: 'var(--chart-2)' },
  { dataKey: '英语', name: '英语', color: 'var(--chart-4)' },
];

function levelClasses(level: 'info' | 'warning' | 'danger' | undefined): { wrap: string; icon: string } {
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

export function TeacherDashboard() {
  const { data: students, isLoading: studentsLoading } = useQuery({
    queryKey: ['students', { class_id: CLASS_ID }],
    queryFn: () => studentsApi.list({ class_id: CLASS_ID, page_size: 100 }),
  });

  const { data: scores, isLoading: scoresLoading } = useQuery({
    queryKey: ['scores', { exam_name: EXAM_NAME }],
    queryFn: () => scoresApi.list({ exam_name: EXAM_NAME }),
  });

  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ['analysis', CLASS_ID, EXAM_NAME],
    queryFn: () => analysisApi.analyze({ class_id: CLASS_ID, exam_name: EXAM_NAME }),
  });

  const stats = useMemo(() => {
    const list = scores ?? [];
    const studentCount = students?.total ?? students?.items.length ?? 0;

    if (list.length === 0) {
      return {
        studentCount,
        avgScore: '—',
        passRate: '—%',
        atRisk: 0,
      };
    }

    const sum = list.reduce((acc, s) => acc + (s.score ?? 0), 0);
    const avg = sum / list.length;
    const passed = list.filter((s) => (s.score ?? 0) >= PASS_LINE).length;
    const rate = (passed / list.length) * 100;

    return {
      studentCount,
      avgScore: avg.toFixed(1),
      passRate: `${Math.round(rate)}%`,
      atRisk: 0, // refined below from analysis insights
    };
  }, [students, scores]);

  const insights = analysis?.insights ?? [];
  const atRiskCount = useMemo(
    () => insights.filter((i) => i.level === 'warning' || i.level === 'danger').length,
    [insights],
  );

  const overview = { ...stats, atRisk: atRiskCount || stats.atRisk };
  const isLoading = studentsLoading || scoresLoading || analysisLoading;

  return (
    <div className="space-y-6">
      <PageHeader
        title="工作台"
        description="高一(3)班 · 今日 2026-06-02"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="学生总数"
          value={isLoading ? <Skeleton className="h-7 w-12" /> : overview.studentCount}
          icon={<Users className="w-5 h-5" />}
          helpText="本学期"
        />
        <StatCard
          label="班级平均"
          value={isLoading ? <Skeleton className="h-7 w-16" /> : overview.avgScore}
          delta="+5.2"
          trend="up"
          icon={<TrendingUp className="w-5 h-5" />}
        />
        <StatCard
          label="及格率"
          value={isLoading ? <Skeleton className="h-7 w-12" /> : overview.passRate}
          delta="+3%"
          trend="up"
          icon={<School className="w-5 h-5" />}
        />
        <StatCard
          label="待关注"
          value={isLoading ? <Skeleton className="h-7 w-8" /> : overview.atRisk}
          delta="-1"
          trend="up"
          icon={<AlertTriangle className="w-5 h-5" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <SectionErrorBoundary>
            <ChartCard
              title="月考成绩分布"
              description={`最近一次月考，${overview.studentCount} 人`}
              legend={
                <>
                  <ChartLegend color="var(--chart-1)" label="数学" />
                  <ChartLegend color="var(--chart-2)" label="语文" />
                  <ChartLegend color="var(--chart-4)" label="英语" />
                </>
              }
            >
              <BarChart xKey="range" data={DISTRIBUTION_DATA} series={SERIES} />
            </ChartCard>
          </SectionErrorBoundary>
        </div>

        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4 text-[var(--accent)]" />
            <h3 className="text-sm font-semibold text-[var(--text)]">AI 洞察</h3>
            {!analysisLoading && insights.length > 0 && (
              <Badge variant="secondary" className="ml-auto">
                {insights.length} 项
              </Badge>
            )}
          </div>
          {analysisLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-12" />
              ))}
            </div>
          ) : insights.length === 0 ? (
            <p className="text-xs text-[var(--text-muted)] py-4 text-center">
              暂无 AI 洞察 — 等后端有班级成绩数据后会自动出现
            </p>
          ) : (
            <div className="space-y-2">
              {insights.slice(0, 4).map((insight, i) => {
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
                      <p className="text-xs font-medium text-[var(--text)] truncate">
                        {insight.title}
                      </p>
                      <p className="text-xs text-[var(--text-muted)] mt-0.5 line-clamp-2">
                        {insight.description}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
          <Link
            to="/teacher/agent"
            className="flex items-center gap-1 text-xs text-[var(--primary)] font-medium mt-4"
          >
            打开 AI 助手 <ArrowRight className="w-3 h-3" />
          </Link>
        </Card>
      </div>
    </div>
  );
}
