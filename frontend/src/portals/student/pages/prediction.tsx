import { useState } from 'react';
import { PageHeader } from '@/shared/components/page-header';
import { ChartCard } from '@/shared/components/chart-card';
import { RadarChart } from '@/shared/charts/radar-chart';
import { RadialGauge } from '@/shared/charts/radial-gauge';
import { Card } from '@/components/ui/card';
import { WhatIfSlider } from '../components/what-if-slider';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';

export function Prediction() {
  const [boost, setBoost] = useState(0);
  const baseProb = 82;
  const currentProb = Math.min(99, baseProb + boost * 0.6);

  return (
    <div className="space-y-6">
      <PageHeader
        title="升学预测"
        description="基于 ML 模型的学生画像与概率预测"
      />

      <Tabs defaultValue="chase">
        <TabsList>
          <TabsTrigger value="chase">冲刺</TabsTrigger>
          <TabsTrigger value="stable">稳定</TabsTrigger>
          <TabsTrigger value="safe">保底</TabsTrigger>
        </TabsList>
        <TabsContent value="chase" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="p-6">
              <RadialGauge value={Math.round(currentProb)} label="市重点概率" color="var(--chart-1)" height={220} />
            </Card>
            <div className="lg:col-span-2">
              <ChartCard title="多维能力评估" description="基于最近 5 次考试">
                <RadarChart
                  angleKey="subject"
                  dataKey="score"
                  data={[
                    { subject: '代数', score: 85 },
                    { subject: '几何', score: 72 },
                    { subject: '函数', score: 90 },
                    { subject: '概率', score: 68 },
                    { subject: '应用', score: 78 },
                  ]}
                />
              </ChartCard>
            </div>
            <div className="lg:col-span-3">
              <WhatIfSlider baseScore={baseProb} onChange={setBoost} />
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
