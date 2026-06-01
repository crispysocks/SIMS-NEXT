import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Send, Square, Bot, User as UserIcon, Sparkles } from 'lucide-react';
import { agentApi, type Session } from '@/shared/api/agent';
import { useStreamingChat } from '@/shared/hooks/use-streaming-chat';
import { PageHeader } from '@/shared/components/page-header';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton, ButtonSpinner } from '@/shared/components/loading';
import { useAuthStore } from '@/shared/stores/auth-store';
import { cn } from '@/lib/utils';

// Placeholder until T4 wires real class/user picking. The agent backend
// scopes sessions per (user_id, class_id), so we need *some* concrete pair
// to talk to it.
const FALLBACK_USER_ID = 1;
const FALLBACK_CLASS_ID = 1;

export function Agent() {
  const qc = useQueryClient();
  const authUser = useAuthStore((s) => s.user);
  const [input, setInput] = useState('');
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // The store keeps user.id as a string; coerce here and fall back if the
  // backend hasn't been wired to real auth yet.
  const userId = useMemo(() => {
    const n = Number(authUser?.id);
    return Number.isFinite(n) && n > 0 ? n : FALLBACK_USER_ID;
  }, [authUser?.id]);

  const {
    data: sessions,
    isLoading: sessionsLoading,
    isError: sessionsError,
  } = useQuery({
    queryKey: ['agent', 'sessions', userId],
    queryFn: () => agentApi.listSessions(userId),
  });

  // Auto-select the most recent session on first load. Only runs when we
  // don't already have one selected so it doesn't fight the user's clicks.
  useEffect(() => {
    if (!activeSessionId && sessions && sessions.length > 0) {
      setActiveSessionId(sessions[0].id);
    }
  }, [sessions, activeSessionId]);

  const { messages, isStreaming, send, abort, reset } = useStreamingChat();

  const createSession = useMutation({
    mutationFn: () =>
      agentApi.createSession({
        user_id: userId,
        class_id: FALLBACK_CLASS_ID,
        class_name: '默认班级',
        title: '新会话',
      }),
    onSuccess: (s: Session) => {
      setActiveSessionId(s.id);
      // Local message state isn't keyed by session — wipe it so a fresh
      // chat starts empty instead of inheriting the previous session's text.
      reset();
      qc.invalidateQueries({ queryKey: ['agent', 'sessions', userId] });
    },
  });

  // Auto-scroll on every assistant token tick so streaming feels live.
  // Reading the last message's content (not just length) ensures we update
  // mid-stream, not only when a new message is appended.
  const lastContent = messages[messages.length - 1]?.content ?? '';
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messages.length, lastContent]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isStreaming) return;

    // Auto-create a session on the very first message if none is active yet,
    // so the user doesn't have to click "新建会话" before typing.
    let sid = activeSessionId;
    if (!sid) {
      const s = await agentApi.createSession({
        user_id: userId,
        class_id: FALLBACK_CLASS_ID,
        class_name: '默认班级',
        title: text.slice(0, 20),
      });
      sid = s.id;
      setActiveSessionId(sid);
      qc.invalidateQueries({ queryKey: ['agent', 'sessions', userId] });
    }
    setInput('');
    await send(sid, text);
  };

  const handleSwitchSession = (id: string) => {
    if (id === activeSessionId) return;
    setActiveSessionId(id);
    // Clear in-memory chat since useStreamingChat isn't keyed by session.
    // The persisted backend messages stay on the server; we just don't
    // hydrate them client-side in this iteration.
    reset();
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI 助手"
        description="教学分析对话 · 学情诊断 · 教学建议"
        actions={
          <Button
            onClick={() => createSession.mutate()}
            disabled={createSession.isPending}
          >
            {createSession.isPending ? (
              <ButtonSpinner className="mr-2" />
            ) : (
              <Sparkles className="w-4 h-4 mr-2" />
            )}
            新建会话
          </Button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-6">
        <Card className="p-4 space-y-2 self-start max-h-[70vh] overflow-y-auto">
          <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide mb-2">
            历史会话
          </p>
          {sessionsLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-8" />
              <Skeleton className="h-8" />
              <Skeleton className="h-8" />
            </div>
          ) : sessionsError ? (
            <p className="text-xs text-[var(--danger)] py-4 text-center">加载失败</p>
          ) : (sessions ?? []).length === 0 ? (
            <p className="text-xs text-[var(--text-muted)] py-4 text-center">
              暂无会话，点上方按钮新建
            </p>
          ) : (
            (sessions ?? []).map((s) => (
              <button
                key={s.id}
                onClick={() => handleSwitchSession(s.id)}
                className={cn(
                  'w-full text-left text-xs px-3 py-2 rounded-md truncate transition-colors',
                  s.id === activeSessionId
                    ? 'bg-[var(--primary-soft)] text-[var(--primary)] font-medium'
                    : 'hover:bg-[var(--surface-2)] text-[var(--text)]'
                )}
              >
                {s.title || s.id.slice(0, 8)}
              </button>
            ))
          )}
        </Card>

        <Card className="p-0 flex flex-col h-[70vh] overflow-hidden">
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-6 space-y-4"
          >
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center text-[var(--text-muted)]">
                <Bot className="w-12 h-12 mb-3 opacity-40" />
                <p className="text-sm">
                  开始一次对话 — 问学生情况、班级表现、教学建议
                </p>
                <p className="text-xs mt-1">直接输入问题即可，回车发送</p>
              </div>
            ) : (
              messages.map((m, i) => {
                const isLast = i === messages.length - 1;
                const isUser = m.role === 'user';
                return (
                  <div
                    key={i}
                    className={cn(
                      'flex gap-3',
                      isUser ? 'justify-end' : 'justify-start'
                    )}
                  >
                    {!isUser && (
                      <div className="w-8 h-8 rounded-full bg-[var(--primary-soft)] flex items-center justify-center shrink-0">
                        <Bot className="w-4 h-4 text-[var(--primary)]" />
                      </div>
                    )}
                    <div
                      className={cn(
                        'max-w-[80%] rounded-lg px-4 py-2.5 text-sm whitespace-pre-wrap break-words',
                        isUser
                          ? 'bg-[var(--primary)] text-white'
                          : 'bg-[var(--surface-2)] text-[var(--text)]'
                      )}
                    >
                      {m.content || (isStreaming && isLast ? (
                        <span className="inline-block animate-pulse">▍</span>
                      ) : (
                        ''
                      ))}
                    </div>
                    {isUser && (
                      <div className="w-8 h-8 rounded-full bg-[var(--accent-soft)] flex items-center justify-center shrink-0">
                        <UserIcon className="w-4 h-4 text-[var(--accent)]" />
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>

          <div className="border-t border-[var(--border)] p-4 flex gap-2 items-center">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="问点什么..."
              className="flex-1 h-10 px-3 rounded-md bg-[var(--surface)] border border-[var(--border)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent"
              disabled={isStreaming}
            />
            {isStreaming ? (
              <Button variant="destructive" size="icon" onClick={abort}>
                <Square className="w-4 h-4" />
              </Button>
            ) : (
              <Button
                size="icon"
                onClick={handleSend}
                disabled={!input.trim()}
              >
                <Send className="w-4 h-4" />
              </Button>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
