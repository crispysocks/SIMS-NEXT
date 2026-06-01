import { Users, School, TrendingUp, AlertTriangle, Sparkles, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { PageHeader } from '@/shared/components/page-header';
import { StatCard } from '@/shared/components/stat-card';
import { ChartCard, ChartLegend } from '@/shared/components/chart-card';
import { BarChart } from '@/shared/charts/bar-chart';
import { Card } from '@/components/ui/card';
import { SectionErrorBoundary } from '@/shared/components/error-boundary';

export function TeacherDashboard() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="工作台"
        description="高一(3)班 · 今日 2026-06-01"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="学生总数" value={45} icon={<Users className="w-5 h-5" />} helpText="本学期" />
        <StatCard label="班级平均" value="78.3" delta="+5.2" trend="up" icon={<TrendingUp className="w-5 h-5" />} />
        <StatCard label="及格率" value="91%" delta="+3%" trend="up" icon={<School className="w-5 h-5" />} />
        <StatCard label="待关注" value={3} delta="-1" trend="up" icon={<AlertTriangle className="w-5 h-5" />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <SectionErrorBoundary>
            <ChartCard
              title="月考成绩分布"
              description="最近一次月考，45 人"
              legend={
                <>
                  <ChartLegend color="var(--chart-1)" label="数学" />
                  <ChartLegend color="var(--chart-2)" label="语文" />
                  <ChartLegend color="var(--chart-4)" label="英语" />
                </>
              }
            >
              <BarChart
                xKey="range"
                data={[
                  { range: '<60', 数学: 3, 语文: 2, 英语: 4 },
                  { range: '60-69', 数学: 5, 语文: 6, 英语: 7 },
                  { range: '70-79', 数学: 12, 语文: 14, 英语: 13 },
                  { range: '80-89', 数学: 18, 语文: 16, 英语: 15 },
                  { range: '90+', 数学: 7, 语文: 7, 英语: 6 },
                ]}
                series={[
                  { dataKey: '数学', name: '数学', color: 'var(--chart-1)' },
                  { dataKey: '语文', name: '语文', color: 'var(--chart-2)' },
                  { dataKey: '英语', name: '英语', color: 'var(--chart-4)' },
                ]}
              />
            </ChartCard>
          </SectionErrorBoundary>
        </div>

        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4 text-[var(--accent)]" />
            <h3 className="text-sm font-semibold text-[var(--text)]">AI 洞察</h3>
          </div>
          <div className="space-y-3">
            {[
              { title: '3 名学生成绩下滑', desc: '张同学数学较上次下降 12 分' },
              { title: '建议组织几何复习', desc: '12 名学生在几何证明题失分率 > 40%' },
              { title: '5 名学生表现优异', desc: '可推荐参与数学竞赛选拔' },
            ].map((item, i) => (
              <div key={i} className="p-3 rounded-md bg-[var(--surface-2)] hover:bg-[var(--primary-soft)]/30 transition-colors">
                <p className="text-xs font-medium text-[var(--text)]">{item.title}</p>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">{item.desc}</p>
              </div>
            ))}
          </div>
          <Link to="/teacher/agent" className="flex items-center gap-1 text-xs text-[var(--primary)] font-medium mt-4">
            打开 AI 助手 <ArrowRight className="w-3 h-3" />
          </Link>
        </Card>
      </div>
    </div>
  );
}
