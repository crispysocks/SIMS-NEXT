import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function QuestionCard({ question, onSubmit, disabled, placeholder }: {
  question: string;
  onSubmit: (answer: string) => void;
  disabled?: boolean;
  placeholder?: string;
}) {
  const [text, setText] = useState('');

  const trimmed = text.trim();
  const canSubmit = !disabled && trimmed.length > 0;

  const handleSubmit = () => {
    if (!canSubmit) return;
    onSubmit(trimmed);
    setText('');
  };

  return (
    <Card className="p-8">
      <p className="text-base text-[var(--text)] leading-relaxed mb-6 whitespace-pre-line">{question}</p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit();
        }}
        className="space-y-2"
      >
        <label
          htmlFor="tutor-answer"
          className="text-xs text-[var(--text-muted)] block"
        >
          输入你的答案，如 (-1, 0) 或 y = 2x + 1
        </label>
        <div className="flex items-center gap-2">
          <Input
            id="tutor-answer"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            disabled={disabled}
            placeholder={placeholder ?? '在此输入你的答案...'}
            className="flex-1 h-10 px-3 text-base"
            autoComplete="off"
            autoFocus
          />
          <Button
            type="submit"
            disabled={!canSubmit}
            className="h-10"
          >
            提交答案
          </Button>
        </div>
      </form>
    </Card>
  );
}
