import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts';

export interface RadialGaugeProps {
  value: number;       // 0-100
  label?: string;
  color?: string;
  height?: number;
}

export function RadialGauge({ value, label, color = 'var(--chart-1)', height = 200 }: RadialGaugeProps) {
  const data = [{ name: label ?? 'value', value: Math.min(100, Math.max(0, value)), fill: color }];
  return (
    <div className="relative" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart
          innerRadius="70%"
          outerRadius="100%"
          data={data}
          startAngle={210}
          endAngle={-30}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
          <RadialBar background={{ fill: 'var(--surface-2)' }} dataKey="value" cornerRadius={6} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div className="text-3xl font-semibold text-[var(--text)] tabular-nums">{value}</div>
        {label && <div className="text-xs text-[var(--text-muted)] mt-1">{label}</div>}
      </div>
    </div>
  );
}