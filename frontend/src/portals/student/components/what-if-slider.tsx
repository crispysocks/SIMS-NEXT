import { useState } from 'react';
import { Card } from '@/components/ui/card';

export function WhatIfSlider({ baseScore, onChange }: { baseScore: number; onChange: (delta: number) => void }) {
  const [delta, setDelta] = useState(0);
  return (
    <Card className="p-6 space-y-4">
      <div>
        <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide">What-if 模拟</p>
        <h3 className="text-sm font-semibold text-[var(--text)] mt-1">分数提升模拟</h3>
      </div>
      <div className="space-y-3">
        <div className="flex justify-between text-xs">
          <span className="text-[var(--text-muted)]">当前预测</span>
          <span className="font-semibold">{baseScore}%</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-[var(--text-muted)]">提升分数</span>
          <span className="font-semibold text-[var(--accent)]">+{delta} 分</span>
        </div>
        <input
          type="range"
          min={0}
          max={50}
          step={5}
          value={delta}
          onChange={(e) => { const v = Number(e.target.value); setDelta(v); onChange(v); }}
          className="w-full accent-[var(--primary)]"
        />
        <div className="text-xs text-[var(--text-muted)]">每提升 5 分，预测概率变化</div>
      </div>
    </Card>
  );
}
