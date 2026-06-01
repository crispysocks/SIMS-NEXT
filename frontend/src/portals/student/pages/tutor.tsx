import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { tutorApi } from '@/shared/api/tutor';
import { PageHeader } from '@/shared/components/page-header';
import { SectionErrorBoundary } from '@/shared/components/error-boundary';
import { Skeleton } from '@/shared/components/loading';
import { QuestionCard } from '../components/question-card';
import { FeedbackAnimation } from '../components/feedback-animation';
import { MasteryRing } from '../components/mastery-ring';
import { Card } from '@/components/ui/card';

export function Tutor() {
  const [feedback, setFeedback] = useState<{ kind: 'correct' | 'wrong' | 'hint'; message: string } | null>(null);

  const { data: question, isLoading, refetch } = useQuery({
    queryKey: ['tutor', 'next'],
    queryFn: () => tutorApi.getNextQuestion(),
  });

  const submit = useMutation({
    mutationFn: (optionId: string) => tutorApi.submitAnswer({ questionId: question!.id, optionId }),
    onSuccess: (result) => {
      setFeedback({
        kind: result.correct ? 'correct' : 'wrong',
        message: result.explanation,
      });
    },
  });

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
                question={question.text}
                options={question.options}
                onSubmit={submit.mutate}
                disabled={submit.isPending || feedback !== null}
              />
              {feedback && <FeedbackAnimation kind={feedback.kind} message={feedback.message} />}
              {feedback && (
                <div className="flex justify-end">
                  <button
                    onClick={() => { setFeedback(null); refetch(); }}
                    className="text-sm text-[var(--primary)] font-medium"
                  >
                    下一题 →
                  </button>
                </div>
              )}
            </div>
          )}
        </SectionErrorBoundary>

        <Card className="p-6 space-y-4 self-start">
          <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide">本节进度</p>
          <div className="flex justify-center">
            <MasteryRing value={68} size={120} />
          </div>
          <div className="space-y-2 pt-2 border-t border-[var(--border)]">
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-muted)]">已答题</span>
              <span className="font-semibold">12 / 20</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-muted)]">正确率</span>
              <span className="font-semibold text-[var(--success)]">83%</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
