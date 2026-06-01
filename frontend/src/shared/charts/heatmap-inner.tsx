import { useEffect, useRef } from 'react';
import * as echarts from 'echarts/core';
import { HeatmapChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import type { HeatmapPoint } from './heatmap';

// Register on-demand
echarts.use([HeatmapChart, CanvasRenderer]);

export interface HeatmapChartInnerProps {
  points: HeatmapPoint[];
  xLabels: string[];
  yLabels: string[];
  height?: number;
  min?: number;
  max?: number;
}

export function HeatmapChartInner({ points, xLabels, yLabels, height = 320, min = 0, max = 100 }: HeatmapChartInnerProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);

    const data = points.map((p) => [p.x, p.y, p.value]);

    chart.setOption({
      tooltip: {
        position: 'top',
        backgroundColor: 'var(--surface)',
        borderColor: 'var(--border)',
        textStyle: { color: 'var(--text)', fontSize: 12 },
      },
      grid: { top: 10, left: 60, right: 20, bottom: 60 },
      xAxis: {
        type: 'category',
        data: xLabels,
        splitArea: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: 'var(--text-muted)', fontSize: 10, rotate: 30 },
      },
      yAxis: {
        type: 'category',
        data: yLabels,
        splitArea: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: 'var(--text-muted)', fontSize: 10 },
      },
      visualMap: {
        min,
        max,
        calculable: false,
        orient: 'horizontal',
        left: 'center',
        bottom: 0,
        textStyle: { color: 'var(--text-muted)', fontSize: 10 },
        inRange: { color: ['#FEE2E2', '#FEF3C7', '#E0E7FF', '#A5B4FC', '#4F46E5'] },
      },
      series: [{
        name: '掌握度',
        type: 'heatmap',
        data,
        label: { show: false },
        itemStyle: { borderRadius: 2, borderColor: 'var(--surface)', borderWidth: 2 },
      }],
    });

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [points, xLabels, yLabels, min, max]);

  return <div ref={ref} style={{ width: '100%', height }} />;
}
