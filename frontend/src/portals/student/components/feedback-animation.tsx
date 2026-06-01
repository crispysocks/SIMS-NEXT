import { Check, X, Lightbulb } from 'lucide-react';
import { cn } from '@/lib/utils';

export function FeedbackAnimation({ kind, message }: { kind: 'correct' | 'wrong' | 'hint'; message: string }) {
  const config = {
    correct: { Icon: Check, bg: 'bg-[var(--success-soft)]', color: 'text-[var(--success)]' },
    wrong: { Icon: X, bg: 'bg-[var(--danger-soft)]', color: 'text-[var(--danger)]' },
    hint: { Icon: Lightbulb, bg: 'bg-[var(--warning-soft)]', color: 'text-[var(--warning)]' },
  }[kind];

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border',
        config.bg,
        'border-[var(--border)]',
        'animate-in fade-in slide-in-from-bottom-2 duration-300'
      )}
    >
      <div className={cn('w-8 h-8 rounded-full bg-white flex items-center justify-center flex-shrink-0', config.color)}>
        <config.Icon className="w-5 h-5" />
      </div>
      <p className="text-sm text-[var(--text)] leading-relaxed flex-1">{message}</p>
    </div>
  );
}
