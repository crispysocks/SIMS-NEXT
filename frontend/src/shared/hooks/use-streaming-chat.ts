import { useCallback, useRef, useState } from 'react';
import { agentApi, type Message } from '@/shared/api/agent';

// SSE block separator. Spec says `\n\n`; some servers emit `\r\n\r\n`. We
// normalize on `\n` before splitting so both work.
const SSE_DELIMITER = '\n\n';

/**
 * Pull the next assistant text chunk out of a parsed SSE block.
 *
 * Supports two shapes, in order of preference:
 *   1. Real backend (run_agent_loop):  event: text_delta + data: {"text":...}
 *   2. Generic spec fallback:         data: {"token":...} or data: {"content":...}
 *
 * Returns `''` for housekeeping events (thinking, tool_start, tool_end, ...)
 * and stop sentinels — the caller handles those separately.
 */
function extractTextChunk(eventName: string | null, dataLine: string): string {
  if (!dataLine || dataLine === '[DONE]') return '';
  let payload: unknown;
  try {
    payload = JSON.parse(dataLine);
  } catch {
    return '';
  }
  if (!payload || typeof payload !== 'object') return '';
  const obj = payload as Record<string, unknown>;

  // Only text_delta events carry assistant prose. tool_start / tool_end /
  // thinking / done all use the same `data: {...}` envelope but should not
  // be appended to the user-visible assistant message.
  if (eventName === 'text_delta' && typeof obj.text === 'string') {
    return obj.text;
  }

  // Legacy / spec fallback: no event name, body uses `token` or `content`.
  if (!eventName) {
    if (typeof obj.token === 'string') return obj.token;
    if (typeof obj.content === 'string') return obj.content;
  }
  return '';
}

interface ParsedEvent {
  event: string | null;
  data: string;
}

// Convert one raw SSE block (everything between two blank lines) into its
// `event:` name and concatenated `data:` payload. Lines starting with `:` are
// SSE comments and ignored. Multiple `data:` lines are joined with `\n` per
// the SSE spec.
function parseSseBlock(block: string): ParsedEvent | null {
  const lines = block.split('\n');
  let event: string | null = null;
  const dataParts: string[] = [];
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line || line.startsWith(':')) continue;
    if (line.startsWith('event:')) {
      event = line.slice(6).trim();
    } else if (line.startsWith('data:')) {
      dataParts.push(line.slice(5).replace(/^ /, ''));
    }
  }
  if (event === null && dataParts.length === 0) return null;
  return { event, data: dataParts.join('\n') };
}

export interface UseStreamingChatResult {
  messages: Message[];
  isStreaming: boolean;
  send: (sessionId: string, text: string) => Promise<void>;
  abort: () => void;
  reset: () => void;
}

/**
 * Drive a single streaming chat against `agentApi.streamChat`.
 *
 * Lifecycle on `send()`:
 *   1. Append user message + an empty assistant placeholder.
 *   2. Open the SSE stream (with an AbortController) and pump chunks into the
 *      assistant placeholder as they arrive.
 *   3. Stop when the server emits `event: done` (or `data: [DONE]`), or when
 *      the reader closes naturally, or when `abort()` is called.
 *   4. On error/abort, suffix the assistant message with `[错误: ...]` so the
 *      user can see what went wrong instead of an empty bubble.
 */
export function useStreamingChat(): UseStreamingChatResult {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(async (sessionId: string, text: string) => {
    setMessages((m) => [...m, { role: 'user', content: text }]);
    setMessages((m) => [...m, { role: 'assistant', content: '' }]);
    setIsStreaming(true);

    const ac = new AbortController();
    abortRef.current = ac;

    const appendToAssistant = (chunk: string) => {
      if (!chunk) return;
      setMessages((m) => {
        const last = m[m.length - 1];
        if (!last || last.role !== 'assistant') return m;
        return [...m.slice(0, -1), { ...last, content: last.content + chunk }];
      });
    };

    let stoppedByDone = false;

    try {
      const stream = await agentApi.streamChat({ session_id: sessionId, text }, ac.signal);
      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let buf = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        // Normalize CRLF so `\n\n` splitting is portable across servers.
        buf += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');

        let sep = buf.indexOf(SSE_DELIMITER);
        while (sep !== -1) {
          const block = buf.slice(0, sep);
          buf = buf.slice(sep + SSE_DELIMITER.length);
          const parsed = parseSseBlock(block);
          if (parsed) {
            if (parsed.event === 'done' || parsed.data === '[DONE]') {
              stoppedByDone = true;
              break;
            }
            if (parsed.event === 'error') {
              try {
                const obj = JSON.parse(parsed.data) as { text?: string; message?: string };
                throw new Error(obj.text ?? obj.message ?? 'Agent 流式错误');
              } catch (e) {
                if (e instanceof Error) throw e;
                throw new Error('Agent 流式错误');
              }
            }
            const chunk = extractTextChunk(parsed.event, parsed.data);
            if (chunk) appendToAssistant(chunk);
          }
          if (stoppedByDone) break;
          sep = buf.indexOf(SSE_DELIMITER);
        }
        if (stoppedByDone) break;
      }
    } catch (err) {
      // `AbortError` is the expected outcome of abort() — surface it as a
      // friendlier "[已中止]" tag rather than a raw error message.
      const isAbort =
        err instanceof Error && (err.name === 'AbortError' || err.message.includes('aborted'));
      const tag = isAbort
        ? '[已中止]'
        : `[错误: ${err instanceof Error ? err.message : '流式连接失败'}]`;
      setMessages((m) => {
        const last = m[m.length - 1];
        if (!last || last.role !== 'assistant') return m;
        const sep = last.content ? '\n\n' : '';
        return [...m.slice(0, -1), { ...last, content: last.content + sep + tag }];
      });
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, []);

  const abort = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setIsStreaming(false);
  }, []);

  return { messages, isStreaming, send, abort, reset };
}
