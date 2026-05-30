import { create } from 'zustand';
import { api } from '@/lib/api';

// ── Types ────────────────────────────────────

export interface AgentSession {
  id: string;
  title: string;
  class_id: number;
  status: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content_json: {
    type: string;
    text: string;
    data_card_ids?: string[];
    tool_call_ids?: number[];
  };
  created_at: string;
}

export interface SSEEvent {
  type: string;
  text?: string;
  tool?: string;
  args_summary?: string;
  summary?: string;
  ok?: boolean;
  card_type?: string;
  title?: string;
  data_id?: string;
  inline_data?: Record<string, unknown>;
  session_id?: string;
  message_id?: number;
  message?: string;
}

// ── Store ────────────────────────────────────

interface ChatState {
  sessions: AgentSession[];
  currentSessionId: string | null;
  messages: ChatMessage[];
  streaming: boolean;
  streamEvents: SSEEvent[];
  streamText: string;
  thinking: boolean;
  loading: boolean;
  error: string | null;

  fetchSessions: () => Promise<void>;
  createSession: (classId: number, className: string, title?: string) => Promise<string>;
  selectSession: (id: string) => void;
  fetchMessages: (sessionId: string) => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  clearStream: () => void;
}

export const useChatStore = create<ChatState>()((set, get) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  streaming: false,
  streamEvents: [],
  streamText: '',
  thinking: false,
  loading: false,
  error: null,

  fetchSessions: async () => {
    set({ loading: true, error: null });
    try {
      const sessions = await api.get<AgentSession[]>('/agent/chat/sessions?user_id=1');
      set({ sessions, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  createSession: async (classId, className, title) => {
    set({ error: null });
    const result = await api.post<{ session_id: string }>('/agent/chat/sessions', {
      user_id: 1,
      class_id: classId,
      class_name: className,
      title: title || '新对话',
    });
    await get().fetchSessions();
    return result.session_id;
  },

  selectSession: (id) => {
    set({ currentSessionId: id, messages: [], streamEvents: [], streamText: '' });
    get().fetchMessages(id);
  },

  fetchMessages: async (sessionId) => {
    try {
      const msgs = await api.get<ChatMessage[]>(`/agent/chat/sessions/${sessionId}/messages`);
      set({ messages: msgs });
    } catch {
      // session not found
    }
  },

  sendMessage: async (text) => {
    const { currentSessionId } = get();
    if (!currentSessionId) return;

    set({
      streaming: true,
      streamEvents: [],
      streamText: '',
      thinking: true,
      error: null,
    });

    const userMsg: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content_json: { type: 'text', text },
      created_at: new Date().toISOString(),
    };
    set((s) => ({ messages: [...s.messages, userMsg] }));

    try {
      const response = await fetch('/api/v1/agent/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId, text }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: '请求失败' }));
        throw new Error(err.detail || `HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';
      const events: SSEEvent[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const chunk of lines) {
          if (!chunk.trim()) continue;

          let eventType = '';
          let eventData = '';

          for (const line of chunk.split('\n')) {
            if (line.startsWith('event: ')) eventType = line.slice(7);
            if (line.startsWith('data: ')) eventData = line.slice(6);
          }

          if (!eventType || !eventData) continue;

          try {
            const parsed = JSON.parse(eventData);
            const evt: SSEEvent = { type: eventType, ...parsed };

            set((s) => {
              const updates: Partial<ChatState> = { streamEvents: [...s.streamEvents, evt] };
              if (evt.type === 'thinking') updates.thinking = true;
              if (evt.type === 'text_delta') {
                updates.streamText = s.streamText + (evt.text || '');
                updates.thinking = false;
              }
              if (evt.type === 'done') updates.thinking = false;
              return updates;
            });

            events.push(evt);
          } catch {
            // skip malformed events
          }
        }
      }

      // streaming done - add assistant message
      const finalText = events
        .filter((e) => e.type === 'text_delta')
        .map((e) => e.text)
        .join('');

      const assistantMsg: ChatMessage = {
        id: events.find((e) => e.message_id)?.message_id || Date.now(),
        role: 'assistant',
        content_json: { type: 'mixed', text: finalText },
        created_at: new Date().toISOString(),
      };

      set((s) => ({
        streaming: false,
        thinking: false,
        messages: [...s.messages, assistantMsg],
      }));
    } catch (e) {
      set({
        streaming: false,
        thinking: false,
        error: (e as Error).message,
      });
    }
  },

  clearStream: () => {
    set({ streamEvents: [], streamText: '', thinking: false });
  },
}));
