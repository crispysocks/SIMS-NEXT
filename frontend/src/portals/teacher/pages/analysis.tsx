import { TrendingDown, AlertTriangle } from 'lucide-react';
import { PageHeader } from '@/shared/components/page-header';
import { ChartCard } from '@/shared/components/chart-card';
import { LineChart } from '@/shared/charts/line-chart';
import { Heatmap } from '@/shared/charts/heatmap';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const HEATMAP_POINTS = Array.from({ length: 64 }).map((_, i) => ({
  x: i % 8,
  y: Math.floor(i / 8),
  value: Math.floor(Math.random() * 100),
}));

export function Analysis() {
  return (
    <div className="space-y-6">
      <PageHeader title="教学分析" description="学情诊断 · 趋势分析 · 风险预警" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="班级数学成绩趋势" description="最近 5 次考试">
          <LineChart
            xKey="exam"
            data={[
              { exam: '月1', avg: 72, top: 92 },
              { exam: '月2', avg: 75, top: 94 },
              { exam: '月3', avg: 78, top: 95 },
              { exam: '期中', avg: 76, top: 96 },
              { exam: '月4', avg: 81, top: 98 },
            ]}
            series={[
              { dataKey: 'avg', name: '班级平均', color: 'var(--chart-1)' },
              { dataKey: 'top', name: '最高分', color: 'var(--chart-4)' },
            ]}
          />
        </ChartCard>

        <ChartCard
          title="知识点掌握度热力图"
          description="8 个班级 × 8 个知识点"
          footer="颜色越深，掌握度越高"
        >
          <Heatmap
            xLabels={['代数', '几何', '函数', '概率', '统计', '应用', '推理', '建模']}
            yLabels={['班1', '班2', '班3', '班4', '班5', '班6', '班7', '班8']}
            points={HEATMAP_POINTS}
          />
        </ChartCard>
      </div>

      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-4 h-4 text-[var(--warning)]" />
          <h3 className="text-sm font-semibold text-[var(--text)]">风险预警</h3>
          <Badge variant="secondary" className="ml-auto">3 名学生</Badge>
        </div>
        <div className="space-y-2">
          {[
            { name: '张同学', issue: '数学较上次下降 12 分', trend: 'down' },
            { name: '李同学', issue: '连续 3 次英语低于 60 分', trend: 'down' },
            { name: '王同学', issue: '物理成绩波动较大（标准差 18）', trend: 'down' },
          ].map((r, i) => (
            <div key={i} className="flex items-center gap-3 p-3 rounded-md hover:bg-[var(--surface-2)]">
              <div className="w-8 h-8 rounded-full bg-[var(--danger-soft)] flex items-center justify-center text-[var(--danger)]">
                <TrendingDown className="w-4 h-4" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-[var(--text)]">{r.name}</p>
                <p className="text-xs text-[var(--text-muted)]">{r.issue}</p>
              </div>
              <button className="text-xs text-[var(--primary)] font-medium">查看详情</button>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
