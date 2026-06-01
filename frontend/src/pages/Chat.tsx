import { useEffect, useRef, useState } from 'react';
import { useChatStore } from '@/stores/chatStore';
import type { SSEEvent } from '@/stores/chatStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

import { cn } from '@/lib/utils';
import {
  Plus,
  MessageSquare,
  Send,
  Loader2,
  AlertCircle,
  Bot,
  User,
  ChevronDown,
  ChevronUp,
  Database,
  Search,
  BarChart3,
} from 'lucide-react';

// ── Session Sidebar ────────────────────────────

function SessionSidebar() {
  const {
    sessions, currentSessionId, loading,
    fetchSessions, createSession, selectSession,
  } = useChatStore();
  const [className, setClassName] = useState('初三(1)班');
  const [classId, setClassId] = useState(1);
  const [showNew, setShowNew] = useState(false);

  useEffect(() => { fetchSessions(); }, []);

  const handleCreate = async () => {
    const id = await createSession(classId, className);
    if (id) { selectSession(id); setShowNew(false); }
  };

  return (
    <div className="w-64 border-r bg-slate-50 flex flex-col h-full">
      <div className="p-3 border-b flex items-center justify-between">
        <h2 className="font-semibold text-sm text-slate-700">对话列表</h2>
        <Button variant="ghost" size="icon" onClick={() => setShowNew(!showNew)} title="新建对话">
          <Plus className="w-4 h-4" />
        </Button>
      </div>
      {showNew && (
        <div className="p-3 border-b space-y-2 bg-white">
          <Input placeholder="班级名称" value={className} onChange={(e) => setClassName(e.target.value)} className="h-8 text-sm" />
          <Input placeholder="班级 ID" type="number" value={classId} onChange={(e) => setClassId(Number(e.target.value))} className="h-8 text-sm" />
          <Button size="sm" className="w-full" onClick={handleCreate}>创建对话</Button>
        </div>
      )}
      <div className="flex-1 overflow-auto">
        {loading && <div className="p-4 text-center text-sm text-slate-400"><Loader2 className="w-4 h-4 animate-spin inline mr-1" />加载中...</div>}
        {!loading && sessions.length === 0 && <div className="p-4 text-center text-sm text-slate-400">暂无对话</div>}
        <div className="p-2 space-y-0.5">
          {sessions.map((s) => (
            <button key={s.id} onClick={() => selectSession(s.id)}
              className={cn('w-full text-left px-3 py-2 rounded-lg text-sm transition-colors',
                s.id === currentSessionId ? 'bg-slate-200 text-slate-900' : 'hover:bg-slate-100 text-slate-600')}>
              <div className="flex items-center gap-2">
                <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{s.title}</span>
              </div>
              <div className="text-xs text-slate-400 mt-0.5 ml-5">{s.message_count} 条消息</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Data Card (clean) ─────────────────────────

function DataCard({ event }: { event: SSEEvent }) {
  const [expanded, setExpanded] = useState(false);
  if (!event.inline_data) return null;

  const data = event.inline_data as Record<string, unknown>;

  if (event.card_type === 'weak_kp' && data.knowledge_points) {
    const kps = data.knowledge_points as Array<Record<string, unknown>>;
    const weakKps = kps.filter((k) => k.is_weak).slice(0, 5);
    return (
      <div className="my-3 rounded-lg border border-amber-200 bg-amber-50/50 p-3">
        <div className="flex items-center gap-2 text-sm font-medium text-amber-800 mb-2">
          <BarChart3 className="w-4 h-4" />
          {event.title}
          <span className="text-xs text-amber-500">({kps.length} 个知识点)</span>
        </div>
        <div className="space-y-1">
          {weakKps.map((kp, i) => (
            <div key={i} className="flex items-center justify-between text-sm">
              <span className="text-slate-700">{kp.name}</span>
              <span className="text-amber-600 font-medium">{(Number(kp.mastery_rate) * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (event.card_type === 'tiered_students' && data.tiers) {
    const tiers = data.tiers as Record<string, Record<string, unknown>>;
    return (
      <div className="my-3 rounded-lg border border-blue-200 bg-blue-50/50 p-3">
        <div className="flex items-center gap-2 text-sm font-medium text-blue-700 mb-2">
          <BarChart3 className="w-4 h-4" />
          {event.title}
        </div>
        <div className="flex gap-3">
          {Object.entries(tiers).map(([key, t]) => (
            <div key={key} className="text-center">
              <div className="text-xs text-slate-500">{t.label}</div>
              <div className="text-lg font-bold text-blue-700">{t.headcount as number}人</div>
              <div className="text-xs text-slate-400">均分 {t.avg_score as number}</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // fallback: collapsible
  return (
    <div className="my-3 rounded-lg border p-3">
      <button onClick={() => setExpanded(!expanded)} className="flex items-center gap-2 text-sm font-medium text-slate-600">
        <Database className="w-4 h-4" />
        {event.title}
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>
      {expanded && (
        <pre className="text-xs text-slate-500 mt-2 max-h-40 overflow-auto">
          {JSON.stringify(data, null, 2).slice(0, 400)}
        </pre>
      )}
    </div>
  );
}

// ── Message Bubble ─────────────────────────────

function AssistantBubble({ text }: { text: string }) {
  if (!text) return null;
  // Split by numbered items and bullet points
  const lines = text.split('\n').filter(Boolean);
  return (
    <div className="flex gap-3 mb-4 justify-start">
      <div className="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center shrink-0 mt-0.5">
        <Bot className="w-3.5 h-3.5 text-indigo-600" />
      </div>
      <div className="max-w-[80%] rounded-lg px-4 py-2.5 bg-white border text-sm leading-7 text-slate-700">
        {lines.map((line, i) => (
          <p key={i} className={cn(line.match(/^\d+[\.\、]/) && 'font-medium')}>{line}</p>
        ))}
      </div>
    </div>
  );
}

function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex gap-3 mb-4 justify-end">
      <div className="max-w-[75%] rounded-lg px-4 py-2.5 bg-indigo-600 text-white text-sm leading-relaxed">
        {text}
      </div>
      <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center shrink-0 mt-0.5">
        <User className="w-3.5 h-3.5 text-slate-600" />
      </div>
    </div>
  );
}

// ── Chat Input ─────────────────────────────────

function ChatInput() {
  const [text, setText] = useState('');
  const { streaming, sendMessage, currentSessionId } = useChatStore();
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSend = async () => {
    if (!text.trim() || streaming) return;
    setText('');
    await sendMessage(text.trim());
    inputRef.current?.focus();
  };

  return (
    <div className="border-t p-4 bg-white">
      <div className="flex gap-2 max-w-3xl mx-auto">
        <Input
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
          placeholder={streaming ? 'Agent 正在回复...' : currentSessionId ? '输入问题...' : '请先创建或选择一个对话'}
          disabled={streaming || !currentSessionId}
          className="flex-1"
        />
        <Button onClick={handleSend} disabled={streaming || !text.trim()} size="icon">
          {streaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </Button>
      </div>
    </div>
  );
}

// ── Main Chat Area ─────────────────────────────

function ChatArea() {
  const { currentSessionId, messages, streamEvents, streamText, streaming, error } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamText, streamEvents.length]);

  if (!currentSessionId) {
    return (
      <div className="flex-1 flex items-center justify-center text-slate-400">
        <div className="text-center">
          <Bot className="w-12 h-12 mx-auto mb-3 text-slate-300" />
          <p className="text-sm">选择左侧对话，或点击 + 创建新对话</p>
        </div>
      </div>
    );
  }

  const dataCards = streamEvents.filter((e) => e.type === 'data_card');

  return (
    <div className="flex-1 flex flex-col">
      <div className="flex-1 overflow-auto px-4">
        <div className="max-w-3xl mx-auto py-4">

          {/* History messages */}
          {messages.map((msg) =>
            msg.role === 'user'
              ? <UserBubble key={msg.id} text={msg.content_json?.text || ''} />
              : <AssistantBubble key={msg.id} text={msg.content_json?.text || ''} />
          )}

          {/* Streaming */}
          {streaming && (
            <div className="mb-4">
              {!streamEvents.some((e) => e.type === 'done') && (
                <div className="flex items-center gap-2 text-sm text-slate-500 mb-3">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-500" />
                  <span>正在思考...</span>
                </div>
              )}

              {/* Data cards during stream */}
              {dataCards.map((evt, i) => (
                <DataCard key={i} event={evt} />
              ))}

              {/* Streaming text */}
              {streamText && <AssistantBubble text={streamText} />}
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 text-red-500 text-sm p-3 bg-red-50 rounded-lg mb-4">
              <AlertCircle className="w-4 h-4" />{error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>
      <ChatInput />
    </div>
  );
}

// ── Page Export ────────────────────────────────

export function ChatPage() {
  return (
    <div className="flex -m-6 h-[calc(100vh-4rem)]">
      <SessionSidebar />
      <ChatArea />
    </div>
  );
}
