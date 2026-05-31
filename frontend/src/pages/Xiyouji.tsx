import { useState, useRef, useEffect } from 'react';
import { useXiyoujiJourneyStore } from '@/stores/xiyoujiJourneyStore';
import { useAuthStore } from '@/stores/authStore';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import {
  BookOpen,
  Award,
  Target,
  Sparkles,
  Sword,
  ChevronRight,
  RotateCcw,
  X,
} from 'lucide-react';

function StartScreen({ onStart }: { onStart: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-8 py-12">
      <div className="text-center space-y-4">
        <div className="flex justify-center">
          <div className="w-20 h-20 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
            <BookOpen className="w-10 h-10 text-amber-600" />
          </div>
        </div>
        <h2 className="text-2xl font-bold text-foreground">西游取经路</h2>
        <p className="text-muted-foreground max-w-sm mx-auto text-sm">
          加入唐僧西行取经的队伍，历经九九八十一难，在游戏中学习西游记的精彩故事。
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4 text-center max-w-md">
        <div className="flex flex-col items-center gap-1">
          <Target className="w-5 h-5 text-indigo-500" />
          <span className="text-xs text-muted-foreground">12个章节</span>
        </div>
        <div className="flex flex-col items-center gap-1">
          <Sword className="w-5 h-5 text-red-500" />
          <span className="text-xs text-muted-foreground">妖怪挑战</span>
        </div>
        <div className="flex flex-col items-center gap-1">
          <Award className="w-5 h-5 text-amber-500" />
          <span className="text-xs text-muted-foreground">知识卡片</span>
        </div>
      </div>

      <Button onClick={onStart} size="lg" className="gap-2">
        <Sparkles className="w-4 h-4" />
        开始取经
      </Button>
    </div>
  );
}

function AchievementBadge({ achievement }: { achievement: { name: string; description: string; unlocked: boolean } }) {
  return (
    <div
      className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs transition-colors ${
        achievement.unlocked
          ? 'bg-amber-100 border-amber-300 text-amber-700 dark:bg-amber-900/30 dark:border-amber-700 dark:text-amber-300'
          : 'bg-muted border-border text-muted-foreground opacity-50'
      }`}
    >
      <Award className="w-3 h-3" />
      {achievement.name}
    </div>
  );
}

function KnowledgeCardDisplay({ card }: { card: { title: string; content: string } }) {
  return (
    <Card className="border-amber-200 bg-amber-50/50 dark:bg-amber-950/20 dark:border-amber-800">
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <BookOpen className="w-4 h-4 text-amber-600" />
          <span className="font-semibold text-sm text-amber-700 dark:text-amber-300">
            {card.title}
          </span>
          <Badge variant="outline" className="ml-auto text-[10px] border-amber-300 text-amber-600">
            知识卡片
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground leading-relaxed">{card.content}</p>
      </CardContent>
    </Card>
  );
}

function JourneyGame() {
  const {
    chapterName,
    monsterName,
    monsterDescription,
    sceneDescription,
    choices,
    knowledgeCard,
    achievements,
    knowledgeCards,
    clearedChapters,
    karma,
    progress,
    levelId,
    messages,
    loading,
    makeChoice,
  } = useXiyoujiJourneyStore();

  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;
    makeChoice(inputValue.trim());
    setInputValue('');
  };

  return (
    <div className="flex h-full gap-4">
      {/* Left Panel - Game Info */}
      <div className="w-72 flex-shrink-0 flex flex-col gap-4 overflow-y-auto">
        {/* Chapter Card */}
        <Card>
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="font-normal">
                第 {levelId} 章
              </Badge>
              <span className="text-xs text-muted-foreground">
                {clearedChapters.length}/12 已通关
              </span>
            </div>
            <h3 className="font-semibold text-base">{chapterName}</h3>
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Sword className="w-3 h-3" />
                妖怪：
                <span className="text-foreground font-medium">{monsterName}</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {monsterDescription}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Progress */}
        <Card>
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">取经进度</span>
              <span className="font-medium">{progress}%</span>
            </div>
            <Progress value={progress} className="h-2" />
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">功德值</span>
              <span className="font-medium text-amber-600">{karma}</span>
            </div>
          </CardContent>
        </Card>

        {/* Achievements */}
        <Card>
          <CardContent className="p-4 space-y-2">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <Award className="w-3 h-3" />
              成就称号
            </div>
            <div className="flex flex-wrap gap-1.5">
              {achievements.map((ach) => (
                <AchievementBadge key={ach.id} achievement={ach} />
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Knowledge Cards */}
        {knowledgeCards.length > 0 && (
          <Card>
            <CardContent className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                <BookOpen className="w-3 h-3" />
                知识卡片 ({knowledgeCards.length})
              </div>
              <div className="space-y-2">
                {knowledgeCards.map((card, i) => (
                  <details key={i} className="group">
                    <summary className="text-xs cursor-pointer text-foreground hover:text-indigo-600 transition-colors">
                      {card.title}
                    </summary>
                    <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                      {card.content}
                    </p>
                  </details>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Right Panel - Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Scene Description */}
        <div className="px-4 py-3 border-b bg-muted/30">
          <p className="text-sm text-muted-foreground italic">"{sceneDescription}"</p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  msg.role === 'user'
                    ? 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30'
                    : 'bg-amber-100 text-amber-600 dark:bg-amber-900/30'
                }`}
              >
                {msg.role === 'user' ? (
                  <span className="text-xs font-bold">我</span>
                ) : (
                  <BookOpen className="w-4 h-4" />
                )}
              </div>
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white dark:bg-indigo-700'
                    : 'bg-muted text-foreground'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}

          {/* New Knowledge Card */}
          {knowledgeCard && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-amber-100 text-amber-600 dark:bg-amber-900/30 flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="max-w-[75%]">
                <KnowledgeCardDisplay card={knowledgeCard} />
              </div>
            </div>
          )}

          {/* New Achievements */}
          {achievements.some((a) => a.unlocked) && (
            <div ref={messagesEndRef} />
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Choices */}
        {choices.length > 0 && (
          <div className="px-4 py-3 border-t bg-muted/30">
            <p className="text-xs text-muted-foreground mb-2">请选择：</p>
            <div className="flex flex-col gap-2">
              {choices.map((choice, i) => (
                <button
                  key={i}
                  onClick={() => makeChoice(choice.text)}
                  disabled={loading}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border bg-background text-sm text-left hover:bg-muted hover:border-indigo-300 transition-colors disabled:opacity-50"
                >
                  <span className="text-muted-foreground text-xs">[{i + 1}]</span>
                  <span className="flex-1">{choice.text}</span>
                  <ChevronRight className="w-3 h-3 text-muted-foreground" />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <form onSubmit={handleSubmit} className="px-4 py-3 border-t flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="输入你的选择..."
            disabled={loading}
            className="flex-1"
          />
          <Button type="submit" disabled={loading || !inputValue.trim()}>
            发送
          </Button>
        </form>
      </div>
    </div>
  );
}

export function XiyoujiPage() {
  const [sessionId, setSessionId] = useState(
    () => localStorage.getItem('xiyouji_session_id') || crypto.randomUUID()
  );
  const { gameActive, startGame, resetGame, levelId } = useXiyoujiJourneyStore();

  const handleStart = async () => {
    const id = sessionId || crypto.randomUUID();
    if (!sessionId) setSessionId(id);
    await startGame(id);
  };

  useEffect(() => {
    if (sessionId && gameActive) {
      localStorage.setItem('xiyouji_session_id', sessionId);
    }
  }, [sessionId, gameActive]);

  const handleExit = () => {
    resetGame();
    localStorage.removeItem('xiyouji_session_id');
    setSessionId('');
  };

  if (!gameActive) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <Card className="w-full max-w-lg">
          <CardContent className="p-6">
            <StartScreen onStart={handleStart} />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-3 border-b flex items-center justify-between bg-muted/30">
        <div className="flex items-center gap-3">
          <BookOpen className="w-5 h-5 text-amber-600" />
          <span className="font-semibold">西游取经路</span>
          <Badge variant="outline" className="text-xs">
            第 {levelId} 章
          </Badge>
        </div>
        <Button variant="ghost" size="sm" onClick={handleExit} className="gap-1 text-muted-foreground">
          <X className="w-3 h-3" />
          退出游戏
        </Button>
      </div>

      {/* Game */}
      <div className="flex-1 overflow-hidden p-4">
        <JourneyGame />
      </div>
    </div>
  );
}