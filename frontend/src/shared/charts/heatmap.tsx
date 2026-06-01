import { lazy, Suspense } from 'react';
import { Skeleton } from '@/shared/components/loading';

// Lazy load ECharts (only downloaded when user enters page, ~150kB)
const HeatmapChartInner = lazy(() => import('./heatmap-inner').then((m) => ({ default: m.HeatmapChartInner })));

export interface HeatmapPoint {
  x: number;
  y: number;
  value: number;
}

export interface HeatmapProps {
  points: HeatmapPoint[];
  xLabels: string[];
  yLabels: string[];
  height?: number;
  min?: number;
  max?: number;
}

export function Heatmap(props: HeatmapProps) {
  return (
    <Suspense fallback={<Skeleton className="w-full" style={{ height: props.height ?? 320 }} />}>
      <HeatmapChartInner {...props} />
    </Suspense>
  );
}
