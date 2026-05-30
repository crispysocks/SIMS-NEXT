import { useEffect, useState } from 'react';
import { useTutorStore } from '@/stores/tutorStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  BookOpen,
  CheckCircle,
  XCircle,
  Lightbulb,
  ArrowRight,
  RotateCcw,
  Target,
  Flame,
  Trophy,
  Calculator,
  Languages,
} from 'lucide-react';

const SUBJECT_CONFIG: Record<string, { label: string; icon: typeof Calculator; color: string }> = {
  math: { label: '数学', icon: Calculator, color: 'bg-blue-100 text-blue-800' },
  english: { label: '英语', icon: Languages, color: 'bg-purple-100 text-purple-800' },
};

export function TutorPage() {
  const {
    currentQuestion,
    answerResult,
    hint,
    progress,
    subjectInfo,
    loading,
    submitting,
    error,
    fetchQuestion,
    submitAnswer,
    requestHint,
    fetchProgress,
    fetchSubject,
    switchSubject,
    resetSession,
    clearResult,
  } = useTutorStore();

  const [answer, setAnswer] = useState('');

  useEffect(() => {
    fetchSubject();
    fetchQuestion();
    fetchProgress();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (answer.trim()) {
      submitAnswer(answer.trim());
    }
  };

  const handleNextQuestion = () => {
    setAnswer('');
    clearResult();
    fetchQuestion();
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'easy':
      case '简单':
        return 'bg-green-100 text-green-800';
      case 'medium':
      case '中等':
        return 'bg-yellow-100 text-yellow-800';
      case 'hard':
      case '困难':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-slate-100 text-slate-800';
    }
  };

  const currentSubject = subjectInfo?.subject || 'math';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <BookOpen className="w-6 h-6" />
          AI 智能辅导
        </h1>
        <div className="flex items-center gap-2">
          {/* 学科选择 */}
          <div className="flex gap-1 bg-slate-100 p-1 rounded-lg">
            {Object.entries(SUBJECT_CONFIG).map(([key, config]) => {
              const Icon = config.icon;
              return (
                <Button
                  key={key}
                  variant={currentSubject === key ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => switchSubject(key)}
                  className="gap-1"
                >
                  <Icon className="w-4 h-4" />
                  {config.label}
                </Button>
              );
            })}
          </div>
          <Button variant="outline" onClick={resetSession}>
            <RotateCcw className="w-4 h-4 mr-2" />
            重新开始
          </Button>
        </div>
      </div>

      {/* 学习进度卡片 */}
      {progress && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-slate-500 text-sm">
                <Target className="w-4 h-4" />
                总题数
              </div>
              <div className="text-2xl font-bold mt-1">{progress.total_questions}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-slate-500 text-sm">
                <Trophy className="w-4 h-4" />
                正确率
              </div>
              <div className="text-2xl font-bold mt-1">
                {(progress.accuracy * 100).toFixed(1)}%
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-green-500 text-sm">
                <Flame className="w-4 h-4" />
                连续正确
              </div>
              <div className="text-2xl font-bold mt-1 text-green-600">
                {progress.correct_streak}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-red-500 text-sm">
                <XCircle className="w-4 h-4" />
                连续错误
              </div>
              <div className="text-2xl font-bold mt-1 text-red-600">
                {progress.wrong_streak}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg">{error}</div>
      )}

      {/* 题目区域 */}
      {loading ? (
        <Card>
          <CardContent className="p-8 text-center text-slate-500">
            加载中...
          </CardContent>
        </Card>
      ) : currentQuestion ? (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">题目</CardTitle>
              <div className="flex gap-2">
                <Badge variant="outline">{currentQuestion.subject}</Badge>
                <Badge variant="outline">{currentQuestion.topic}</Badge>
                <Badge className={getDifficultyColor(currentQuestion.difficulty)}>
                  {currentQuestion.difficulty}
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-lg leading-relaxed whitespace-pre-wrap">
              {currentQuestion.question_text}
            </div>
            {currentQuestion.knowledge_tags.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {currentQuestion.knowledge_tags.map((tag) => (
                  <Badge key={tag} variant="secondary">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-8 text-center text-slate-500">
            暂无题目
          </CardContent>
        </Card>
      )}

      {/* 答题区域 */}
      {currentQuestion && !answerResult && (
        <Card>
          <CardContent className="p-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-700 mb-2 block">
                  你的答案
                </label>
                <Input
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="输入你的答案..."
                  className="text-lg"
                  disabled={submitting}
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={!answer.trim() || submitting}>
                  {submitting ? '提交中...' : '提交答案'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={requestHint}
                  disabled={hint !== null && hint.remaining <= 0}
                >
                  <Lightbulb className="w-4 h-4 mr-2" />
                  获取提示 {hint ? `(${hint.remaining}次)` : ''}
                </Button>
              </div>
            </form>

            {/* 提示区域 */}
            {hint && (
              <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <div className="flex items-center gap-2 text-yellow-800 font-medium mb-2">
                  <Lightbulb className="w-4 h-4" />
                  提示 (级别 {hint.level}，剩余 {hint.remaining} 次)
                </div>
                <div className="text-yellow-700">{hint.hint}</div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 答题结果 */}
      {answerResult && (
        <div className="space-y-4">
          {/* 正误提示 */}
          <Card
            className={
              answerResult.is_correct
                ? 'border-green-200 bg-green-50'
                : 'border-red-200 bg-red-50'
            }
          >
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                {answerResult.is_correct ? (
                  <CheckCircle className="w-8 h-8 text-green-600" />
                ) : (
                  <XCircle className="w-8 h-8 text-red-600" />
                )}
                <div>
                  <div
                    className={`text-lg font-bold ${
                      answerResult.is_correct ? 'text-green-800' : 'text-red-800'
                    }`}
                  >
                    {answerResult.is_correct ? '回答正确！' : '回答错误'}
                  </div>
                  {answerResult.tutor_response && (
                    <div className="text-slate-600 mt-1">
                      {answerResult.tutor_response.encouragement}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 答案对比 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">答案对比</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">你的答案</div>
                  <div className="p-3 bg-slate-100 rounded-lg font-mono">
                    {answerResult.student_answer}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">正确答案</div>
                  <div className="p-3 bg-green-100 rounded-lg font-mono">
                    {answerResult.correct_answer}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* AI 解析 */}
          {answerResult.explanation && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">AI 解析</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {answerResult.explanation.what_is_wrong && (
                  <div>
                    <div className="font-medium text-slate-700 mb-1">错误分析</div>
                    <div className="text-slate-600">
                      {answerResult.explanation.what_is_wrong}
                    </div>
                  </div>
                )}
                {answerResult.explanation.why_it_is_wrong && (
                  <div>
                    <div className="font-medium text-slate-700 mb-1">错误原因</div>
                    <div className="text-slate-600">
                      {answerResult.explanation.why_it_is_wrong}
                    </div>
                  </div>
                )}
                {answerResult.explanation.how_to_fix && (
                  <div>
                    <div className="font-medium text-slate-700 mb-1">修正方法</div>
                    <div className="text-slate-600">
                      {answerResult.explanation.how_to_fix}
                    </div>
                  </div>
                )}
                {answerResult.explanation.similar_examples.length > 0 && (
                  <div>
                    <div className="font-medium text-slate-700 mb-1">类似例题</div>
                    <ul className="list-disc list-inside text-slate-600 space-y-1">
                      {answerResult.explanation.similar_examples.map((ex, i) => (
                        <li key={i}>{ex}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 学习建议 */}
          {(answerResult.tutor_response?.hint || (answerResult.remediation && answerResult.remediation.recommended_topics.length > 0)) && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">学习建议</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {answerResult.tutor_response?.hint && (
                    <div>
                      <div className="flex items-center gap-2 font-medium text-slate-700 mb-1">
                        <Lightbulb className="w-4 h-4 text-yellow-500" />
                        AI 建议
                      </div>
                      <div className="text-slate-600 pl-6">
                        {answerResult.tutor_response.hint}
                      </div>
                    </div>
                  )}
                  {answerResult.remediation && answerResult.remediation.recommended_topics.length > 0 && (
                    <div>
                      <div className="font-medium text-slate-700 mb-1">推荐复习主题</div>
                      <div className="flex flex-wrap gap-2">
                        {answerResult.remediation.recommended_topics.map((topic) => (
                          <Badge key={topic} variant="outline">
                            {topic}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 下一题按钮 */}
          <div className="flex justify-center">
            <Button onClick={handleNextQuestion} size="lg">
              下一题
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
