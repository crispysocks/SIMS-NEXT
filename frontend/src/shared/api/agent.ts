import { api } from '@/lib/api';

// 1:1 mirror of backend agent chat router (`app/agent/api/v1/chat_router.py`)
// mounted at `/api/v1/agent`. The chat router itself uses the `/chat` prefix,
// so all session / stream URLs live under `/agent/chat/...`.

// -- Domain types -------------------------------------------------------------

export interface Session {
  id: string;
  title: string | null;
  class_id: number;
  status?: string;
  message_count?: number;
  created_at?: string;
  updated_at?: string;
}

// Backend `POST /agent/chat/sessions` returns a flat object using `session_id`
// rather than `id`. We normalize that to `Session` in `createSession()` below.
interface CreateSessionResponse {
  session_id: string;
  title: string | null;
  class_id: number;
}

// Stored message returned by `GET /sessions/{id}/messages`. The backend keeps
// the full tool / response payload in `content_json`; we expose a flat
// `content` string for the chat UI alongside the raw payload.
export interface StoredMessage {
  id: number;
  role: 'user' | 'assistant' | 'system' | string;
  content_json: Record<string, unknown> | null;
  created_at: string;
}

// In-memory chat message shape used by `useStreamingChat`. Independent from
// the persisted `StoredMessage` because streaming tokens are accumulated
// client-side before any DB round-trip.
export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface StudentBrief {
  id?: number;
  student_no: string;
  name: string;
  class_id?: number;
  [key: string]: unknown;
}

interface ClassStudentsResponse {
  class_id: number;
  students: StudentBrief[];
  count: number;
}

// -- Request bodies -----------------------------------------------------------

export interface CreateSessionRequest {
  user_id: number;
  class_id: number;
  class_name?: string;
  title?: string;
}

export interface StreamChatRequest {
  session_id: string;
  text: string;
}

// -- API client ---------------------------------------------------------------

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const agentApi = {
  /** Create a new chat session. Backend requires `user_id` + `class_id`. */
  async createSession(data: CreateSessionRequest): Promise<Session> {
    const res = await api.post<CreateSessionResponse>('/agent/chat/sessions', data);
    return { id: res.session_id, title: res.title, class_id: res.class_id };
  },

  /** List a user's chat sessions. Backend requires `user_id` as a query arg. */
  listSessions: (userId: number) =>
    api.get<Session[]>(`/agent/chat/sessions?user_id=${userId}`),

  /** Persisted messages for a session (used when the user re-opens history). */
  getMessages: (sessionId: string) =>
    api.get<StoredMessage[]>(`/agent/chat/sessions/${sessionId}/messages`),

  /** Soft-archive a session. Returns 204 (no content). */
  archiveSession: (sessionId: string) =>
    api.post<void>(`/agent/chat/sessions/${sessionId}/archive`, {}),

  /**
   * Send a user message and return the raw SSE body stream for the assistant
   * reply. Uses plain `fetch` (not `api.postStream`) so we can attach a
   * `signal` from `useStreamingChat`'s `AbortController` and throw a
   * caller-friendly error message instead of the generic API one.
   *
   * Backend emits SSE events of form:
   *   event: text_delta
   *   data: {"text": "..."}
   *
   *   event: done
   *   data: {"session_id": "...", "message_id": N}
   *
   * The body field is `text` (matching backend `SendMessageRequest.text`).
   */
  async streamChat(
    req: StreamChatRequest,
    signal?: AbortSignal,
  ): Promise<ReadableStream<Uint8Array>> {
    const res = await fetch(`${API_BASE}/agent/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
      signal,
    });
    if (!res.ok || !res.body) {
      throw new Error(`流式连接失败: HTTP ${res.status}`);
    }
    return res.body;
  },

  /**
   * List students in a class. Backend route is
   * `GET /agent/students/class/{class_id}` (not a query arg).
   */
  async listStudents(classId: number): Promise<StudentBrief[]> {
    const res = await api.get<ClassStudentsResponse>(`/agent/students/class/${classId}`);
    return res.students;
  },
};
