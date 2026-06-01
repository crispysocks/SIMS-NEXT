import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Lightbulb } from 'lucide-react';
import { tutorApi } from '@/shared/api/tutor';
import { PageHeader } from '@/shared/components/page-header';
import { SectionErrorBoundary } from '@/shared/components/error-boundary';
import { Skeleton } from '@/shared/components/loading';
import { QuestionCard } from '../components/question-card';
import { FeedbackAnimation } from '../components/feedback-animation';
import { MasteryRing } from '../components/mastery-ring';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type FeedbackKind = 'correct' | 'wrong' | 'hint';
interface Feedback {
  kind: FeedbackKind;
  message: string;
}

export function Tutor() {
  const qc = useQueryClient();
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [hintText, setHintText] = useState<string | null>(null);

  const {
    data: question,
    isLoading,
    refetch: refetchQuestion,
  } = useQuery({
    queryKey: ['tutor', 'next'],
    queryFn: () => tutorApi.getNextQuestion(),
  });

  const { data: progress } = useQuery({
    queryKey: ['tutor', 'progress'],
    queryFn: () => tutorApi.getProgress(),
  });

  const submit = useMutation({
    mutationFn: (answer: string) => tutorApi.submitAnswer({ student_answer: answer }),
    onSuccess: (result) => {
      const msg = result.tutor_response?.explanation?.trim()
        || `正确答案：${result.correct_answer}`;
      setFeedback({
        kind: result.is_correct ? 'correct' : 'wrong',
        message: result.is_correct
          ? `${msg}（${result.tutor_response?.encouragement ?? ''}）`
          : msg,
      });
      // Refresh progress in the sidebar after each submission.
      qc.invalidateQueries({ queryKey: ['tutor', 'progress'] });
    },
  });

  const hint = useMutation({
    mutationFn: () => tutorApi.requestHint(),
    onSuccess: (h) => {
      setHintText(h.hint);
      setFeedback({ kind: 'hint', message: h.hint });
    },
  });

  const accuracyPct = useMemo(() => {
    if (!progress) return 0;
    return Math.round(progress.accuracy * 100);
  }, [progress]);

  const goToNext = () => {
    setFeedback(null);
    setHintText(null);
    refetchQuestion();
  };

  return (
    <div className="space-y-6">
      <PageHeader title="智能辅导" description="基于贝叶斯掌握度追踪的自适应学习" />

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6">
        <SectionErrorBoundary>
          {isLoading || !question ? (
            <Skeleton className="h-96" />
          ) : (
            <div className="space-y-4">
              <QuestionCard
                question={question.question_text}
                onSubmit={submit.mutate}
                disabled={submit.isPending || feedback !== null}
              />

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
                  <span className="px-2 py-0.5 rounded bg-[var(--surface-2)]">{question.subject}</span>
                  <span className="px-2 py-0.5 rounded bg-[var(--surface-2)]">{question.topic}</span>
                  <span className="px-2 py-0.5 rounded bg-[var(--surface-2)]">{question.difficulty}</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => hint.mutate()}
                  disabled={hint.isPending || feedback !== null}
                  className="text-[var(--warning)]"
                >
                  <Lightbulb className="w-4 h-4 mr-1" />
                  {hintText ? `再来一提示（剩余 ${hint.data?.remaining ?? 0}）` : '需要提示'}
                </Button>
              </div>

              {feedback && (
                <FeedbackAnimation kind={feedback.kind} message={feedback.message} />
              )}

              {feedback && (
                <div className="flex justify-end">
                  <button
                    onClick={goToNext}
                    className="text-sm text-[var(--primary)] font-medium"
                  >
                    下一题 →
                  </button>
                </div>
              )}
            </div>
          )}
        </SectionErrorBoundary>

        <Card className={cn('p-6 space-y-4 self-start')}>
          <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide">本节进度</p>
          <div className="flex justify-center">
            <MasteryRing value={accuracyPct} size={120} />
          </div>
          <div className="space-y-2 pt-2 border-t border-[var(--border)]">
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-muted)]">已答题</span>
              <span className="font-semibold">
                {progress ? `${progress.correct_count} / ${progress.total_questions}` : '0 / 0'}
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-muted)]">正确率</span>
              <span className="font-semibold text-[var(--success)]">
                {progress ? `${accuracyPct}%` : '0%'}
              </span>
            </div>
            {progress && (
              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-muted)]">连胜 / 连败</span>
                <span className="font-semibold tabular-nums">
                  {progress.correct_streak} / {progress.wrong_streak}
                </span>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
