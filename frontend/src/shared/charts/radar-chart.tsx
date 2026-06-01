import {
  Radar,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts';

export interface RadarChartProps {
  data: Array<Record<string, string | number>>;
  angleKey: string;
  dataKey: string;
  color?: string;
  height?: number;
  max?: number;
}

export function RadarChart({ data, angleKey, dataKey, color = 'var(--chart-1)', height = 260, max = 100 }: RadarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsRadarChart data={data}>
        <PolarGrid stroke="var(--border)" />
        <PolarAngleAxis dataKey={angleKey} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
        <PolarRadiusAxis domain={[0, max]} tick={{ fill: 'var(--text-subtle)', fontSize: 9 }} stroke="var(--border)" />
        <Radar dataKey={dataKey} stroke={color} fill={color} fillOpacity={0.25} />
      </RechartsRadarChart>
    </ResponsiveContainer>
  );
}