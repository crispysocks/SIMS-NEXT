import { useState, useRef, useEffect } from 'react';
import { useJourneyStore } from '@/stores/journeyStore';
import type { ChoiceItem, KnowledgeCard, Achievement } from '@/stores/journeyStore';
import { useAuthStore } from '@/stores/authStore';
import { api } from '@/lib/api';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Award, BookOpen } from 'lucide-react';

interface ChatMessage {
  role: 'user' | 'assistant' | 'tool';
  content: string;
  toolName?: string;
}

function generateSessionId(): string {
  return crypto.randomUUID();
}

function JourneyProgressBar({ progress, karma, chapterName }: { progress: number; karma: number; chapterName: string }) {
  return (
    <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-amber-700 dark:text-amber-300 font-medium">{chapterName}</span>
        <span className="text-muted-foreground">Karma: {karma}</span>
      </div>
      <Progress value={progress} className="h-2" />
    </div>
  );
}

function ChoiceButtons({ choices, onSelect }: { choices: ChoiceItem[]; onSelect: (text: string) => void }) {
  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground font-medium">Make your choice:</p>
      {choices.map((c, i) => (
        <Button
          key={i}
          variant="outline"
          size="sm"
          className="w-full justify-start text-left h-auto py-2 px-3"
          onClick={() => onSelect(c.text)}
        >
          <span className="text-xs">{c.text}</span>
          <Badge variant="secondary" className="ml-auto text-[10px]">
            {c.karma > 0 ? `+${c.karma}` : c.karma} karma
          </Badge>
        </Button>
      ))}
    </div>
  );
}

function KnowledgeCardPopup({ card }: { card: KnowledgeCard }) {
  return (
    <Card className="border-amber-200 bg-amber-50/50 dark:bg-amber-950/20 dark:border-amber-800">
      <CardContent className="p-3">
        <div className="flex items-center gap-2 mb-1">
          <BookOpen className="w-4 h-4 text-amber-600" />
          <span className="font-semibold text-sm text-amber-700 dark:text-amber-300">{card.title}</span>
          <Badge variant="outline" className="ml-auto text-[10px]">Knowledge Card</Badge>
        </div>
        <p className="text-xs text-muted-foreground">{card.content}</p>
      </CardContent>
    </Card>
  );
}

function AchievementBadges({ achievements }: { achievements: Achievement[] }) {
  return (
    <div className="flex flex-wrap gap-1">
      {achievements.map((a) => (
        <div
          key={a.id}
          className={`flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] ${
            a.unlocked
              ? 'bg-amber-100 border-amber-300 text-amber-700'
              : 'bg-muted border-border text-muted-foreground opacity-50'
          }`}
        >
          <Award className="w-3 h-3" />
          {a.name}
        </div>
      ))}
    </div>
  );
}

export function NovelsChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => generateSessionId());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const token = useAuthStore((s) => s.token);
  const journey = useJourneyStore();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const message = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: message }]);
    setLoading(true);

    try {
      const stream = await api.postStream('/novels/chat', {
        session_id: sessionId,
        message,
      }, token || undefined);

      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let assistantContent = '';
      let hasAssistantMsg = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const lines = decoder.decode(value).split('\n');
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));

            if (data.type === 'text') {
              assistantContent += data.content;
              if (!hasAssistantMsg) {
                setMessages((prev) => [...prev, { role: 'assistant', content: data.content }]);
                hasAssistantMsg = true;
              } else {
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1] = { role: 'assistant', content: assistantContent };
                  return updated;
                });
              }
            } else if (data.type === 'tool_call') {
              // 工具调用仅记录到内部状态，不展示
              setMessages((prev) => [...prev, { role: 'tool', content: `Calling: ${data.tool}`, toolName: data.tool }]);
            } else if (data.type === 'tool_result') {
              const resultPreview = typeof data.result === 'string'
                ? data.result.slice(0, 200)
                : JSON.stringify(data.result).slice(0, 200);
              setMessages((prev) => [...prev, { role: 'tool', content: resultPreview, toolName: data.tool }]);

              // detect game events from tool results
              if (['start_journey', 'make_choice', 'get_journey_status'].includes(data.tool)) {
                try {
                  const parsed = typeof data.result === 'string' ? JSON.parse(data.result) : data.result;
                  if (parsed.choices || parsed.progress !== undefined) {
                    journey.applyGameEvent(parsed);
                  }
                } catch (e) { console.error("Failed to parse game event:", e); }
              }
            } else if (data.type === 'done') {
              break;
            } else if (data.type === 'error') {
              setMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${data.content}` }]);
            }
          } catch (e) { console.error("SSE parse error:", e); }
        }
      }
    } catch (e) {
      console.error("Stream error:", e);
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, an error occurred. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleChoiceSelect = (text: string) => {
    setInput(text);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8 space-y-2">
            <BookOpen className="w-12 h-12 mx-auto text-amber-400" />
            <p className="text-lg font-medium">Four Great Novels Assistant</p>
            <p className="text-sm">Ask questions about the novels or start a Journey to the West adventure game.</p>
          </div>
        )}

        {messages
          .filter((msg) => msg.role !== 'tool')
          .map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[70%] rounded-lg px-4 py-2 ${
                msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100 dark:bg-gray-800 text-foreground'
              }`}>
                <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
              </div>
            </div>
          ))}

        {journey.gameActive && (
          <div className="space-y-3 mx-4">
            <JourneyProgressBar progress={journey.progress} karma={journey.karma} chapterName={journey.chapterName} />
            {journey.achievements.length > 0 && <AchievementBadges achievements={journey.achievements} />}
            {journey.choices.length > 0 && (
              <ChoiceButtons choices={journey.choices} onSelect={handleChoiceSelect} />
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t p-4 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={journey.gameActive ? 'Make your choice...' : 'Ask about the four great novels...'}
          className="flex-1 border rounded-lg px-4 py-2 text-sm bg-background"
          disabled={loading}
        />
        <Button type="submit" disabled={loading || !input.trim()} size="sm">
          {loading ? 'Thinking...' : 'Send'}
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={() => {
          setMessages([]);
          journey.reset();
        }}>
          Clear
        </Button>
      </form>
    </div>
  );
}
