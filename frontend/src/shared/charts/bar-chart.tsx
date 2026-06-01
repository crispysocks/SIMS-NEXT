import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export interface BarSeries {
  dataKey: string;
  name: string;
  color: string;
}

export interface BarChartProps {
  data: Array<Record<string, string | number>>;
  xKey: string;
  series: BarSeries[];
  height?: number;
  layout?: 'horizontal' | 'vertical';
}

export function BarChart({ data, xKey, series, height = 240, layout = 'horizontal' }: BarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart
        data={data}
        layout={layout === 'vertical' ? 'vertical' : 'horizontal'}
        margin={{ top: 5, right: 10, left: 0, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
        {layout === 'vertical' ? (
          <>
            <XAxis type="number" stroke="var(--text-subtle)" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis type="category" dataKey={xKey} stroke="var(--text-subtle)" fontSize={11} tickLine={false} axisLine={false} width={60} />
          </>
        ) : (
          <>
            <XAxis dataKey={xKey} stroke="var(--text-subtle)" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis stroke="var(--text-subtle)" fontSize={11} tickLine={false} axisLine={false} width={32} />
          </>
        )}
        <Tooltip
          cursor={{ fill: 'var(--surface-2)' }}
          contentStyle={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        {series.map((s) => (
          <Bar key={s.dataKey} dataKey={s.dataKey} name={s.name} fill={s.color} radius={[3, 3, 0, 0]} barSize={12} />
        ))}
      </RechartsBarChart>
    </ResponsiveContainer>
  );
}