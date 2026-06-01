import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export interface LineSeries {
  dataKey: string;
  name: string;
  color: string;
  type?: 'monotone' | 'linear' | 'step';
}

export interface LineChartProps {
  data: Array<Record<string, string | number>>;
  xKey: string;
  series: LineSeries[];
  height?: number;
  showGrid?: boolean;
}

const defaultColors = ['var(--chart-1)', 'var(--chart-2)', 'var(--chart-4)'];

export function LineChart({ data, xKey, series, height = 240, showGrid = true }: LineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsLineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />}
        <XAxis
          dataKey={xKey}
          stroke="var(--text-subtle)"
          fontSize={11}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="var(--text-subtle)"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          width={32}
        />
        <Tooltip
          contentStyle={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            fontSize: 12,
          }}
          labelStyle={{ color: 'var(--text)' }}
        />
        {series.map((s, i) => (
          <Line
            key={s.dataKey}
            type={s.type ?? 'monotone'}
            dataKey={s.dataKey}
            name={s.name}
            stroke={s.color || defaultColors[i]}
            strokeWidth={2}
            dot={{ r: 3, fill: s.color || defaultColors[i] }}
            activeDot={{ r: 5 }}
          />
        ))}
      </RechartsLineChart>
    </ResponsiveContainer>
  );
}