import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export interface QuestionOption {
  id: string;
  label: string;
}

export function QuestionCard({ question, options, onSubmit, disabled }: {
  question: string;
  options: QuestionOption[];
  onSubmit: (optionId: string) => void;
  disabled?: boolean;
}) {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <Card className="p-8">
      <p className="text-base text-[var(--text)] leading-relaxed mb-6 whitespace-pre-line">{question}</p>
      <div className="space-y-2">
        {options.map((opt) => (
          <button
            key={opt.id}
            onClick={() => !disabled && setSelected(opt.id)}
            disabled={disabled}
            className={cn(
              'w-full text-left p-4 rounded-lg border-2 transition-all text-sm',
              selected === opt.id
                ? 'border-[var(--primary)] bg-[var(--primary-soft)]/40'
                : 'border-[var(--border)] hover:border-[var(--primary)]/50',
              disabled && 'opacity-60 cursor-not-allowed'
            )}
          >
            <span className="font-semibold mr-2 text-[var(--text-muted)]">{opt.id}.</span>
            {opt.label}
          </button>
        ))}
      </div>
      <div className="mt-6 flex justify-end">
        <Button onClick={() => selected && onSubmit(selected)} disabled={!selected || disabled}>
          提交答案
        </Button>
      </div>
    </Card>
  );
}
