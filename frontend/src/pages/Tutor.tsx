import { useEffect, useState, useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
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
  Loader2,
} from 'lucide-react';

const SUBJECT_CONFIG: Record<string, { label: string; icon: typeof Calculator; color: string }> = {
  math: { label: '数学', icon: Calculator, color: 'bg-blue-100 text-blue-800' },
  english: { label: '英语', icon: Languages, color: 'bg-purple-100 text-purple-800' },
};

/** Render math text with LaTeX support. Text between $...$ is rendered as LaTeX. */
function MathText({ text, subject }: { text: string; subject: string }) {
  if (subject !== 'math') {
    return <span className="text-lg leading-relaxed whitespace-pre-wrap">{text}</span>;
  }

  const parts = useMemo(() => {
    const segments: Array<{ type: 'text' | 'latex'; content: string }> = [];
    const regex = /\$([^$]+)\$/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        segments.push({ type: 'text', content: text.slice(lastIndex, match.index) });
      }
      segments.push({ type: 'latex', content: match[1] });
      lastIndex = regex.lastIndex;
    }
    if (lastIndex < text.length) {
      segments.push({ type: 'text', content: text.slice(lastIndex) });
    }
    return segments;
  }, [text]);

  return (
    <span className="text-lg leading-relaxed">
      {parts.map((part, i) =>
        part.type === 'latex' ? (
          <span
            key={i}
            className="mx-1"
            dangerouslySetInnerHTML={{
              __html: katex.renderToString(part.content, { throwOnError: false, displayMode: false }),
            }}
          />
        ) : (
          <span key={i}>{part.content}</span>
        )
      )}
    </span>
  );
}

export function TutorPage() {
  const {
    currentQuestion,
    answerResult,
    hint,
    progress,
    subjectInfo,
    topicInfo,
    loading,
    submitting,
    error,
    fetchQuestion,
    submitAnswer,
    requestHint,
    fetchProgress,
    fetchSubject,
    fetchTopics,
    switchSubject,
    resetSession,
    clearResult,
  } = useTutorStore();

  const [answer, setAnswer] = useState('');

  useEffect(() => {
    fetchSubject();
    fetchTopics();
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
        return 'bg-green-100 text-green-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'hard':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-slate-100 text-slate-800';
    }
  };

  const currentSubject = subjectInfo?.subject || 'math';
  const topicNames = topicInfo?.topic_names || {};
  const difficultyLabels = topicInfo?.difficulty_labels || {};

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BookOpen className="w-6 h-6" />
            AI 智能辅导
          </h1>
          <div className="flex items-center gap-2">
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
      </div>

      <div className="max-w-5xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Stats cards */}
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

            {/* Question area */}
            {loading ? (
              <Card>
                <CardContent className="p-8 text-center text-slate-500 flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  加载中...
                </CardContent>
              </Card>
            ) : currentQuestion ? (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">
                      {topicNames[currentQuestion.topic] || currentQuestion.topic}
                    </CardTitle>
                    <div className="flex gap-2">
                      <Badge className={getDifficultyColor(currentQuestion.difficulty)}>
                        {difficultyLabels[currentQuestion.difficulty] || currentQuestion.difficulty}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <MathText text={currentQuestion.question_text} subject={currentSubject} />
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

            {/* Answer area */}
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
                        {submitting ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            提交中...
                          </>
                        ) : (
                          '提交答案'
                        )}
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

                  {/* Hint area */}
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

            {/* Answer result */}
            {answerResult && (
              <div className="space-y-4">
                {/* Correct/incorrect banner */}
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

                {/* Answer comparison */}
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

                {/* AI explanation */}
                {answerResult.explanation && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">
                        AI 解析
                        {answerResult.explanation.generation_source && (
                          <Badge variant="outline" className="ml-2 text-xs">
                            {answerResult.explanation.generation_source === 'rag_llm' && 'RAG 生成'}
                            {answerResult.explanation.generation_source === 'template_fallback' && '模板降级'}
                            {answerResult.explanation.generation_source === 'deterministic_fallback' && '确定性降级'}
                          </Badge>
                        )}
                      </CardTitle>
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

                {/* Learning suggestions */}
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
                                  {topicNames[topic] || topic}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Knowledge snippets (English) */}
                {answerResult.retrieved_snippets.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">相关知识点</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {answerResult.retrieved_snippets.map((snippet) => (
                          <div key={snippet.id} className="p-3 bg-slate-50 rounded-lg">
                            <div className="font-medium text-slate-700">{snippet.title}</div>
                            {snippet.score !== undefined && (
                              <div className="text-xs text-slate-400 mt-1">
                                相关性: {snippet.score.toFixed(3)}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Next question button */}
                <div className="flex justify-center">
                  <Button onClick={handleNextQuestion} size="lg">
                    下一题
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar — mastery progress */}
          <div className="space-y-6">
            {progress && progress.mastery_states.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">掌握度</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {progress.mastery_states.map((state) => {
                    const m = state.mastery;
                    const color = m < 0.4 ? '#ef4444' : m <= 0.7 ? '#f59e0b' : '#22c55e';
                    return (
                      <div key={state.topic_id}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">
                            {topicNames[state.topic_id] || state.topic_id}
                          </span>
                          <span
                            className="text-sm font-bold"
                            style={{ color }}
                          >
                            {m.toFixed(2)}
                          </span>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-2">
                          <div
                            className="h-2 rounded-full transition-all"
                            style={{
                              width: `${Math.min(m * 100, 100)}%`,
                              backgroundColor: color,
                            }}
                          />
                        </div>
                        <div className="text-xs text-slate-400 mt-1">
                          不确定度: {state.variance.toFixed(4)} | 答题: {state.total_attempts}
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t mt-8 py-4 text-center text-sm text-slate-400">
        AI Tutor MVP | Mastery: Beta-Binomial | Recommender: 3-tier deterministic
      </div>
    </div>
  );
}
