import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useStreamingChat } from '../use-streaming-chat';

// Build a `ReadableStream<Uint8Array>` from a list of pre-encoded SSE chunks.
// Each chunk is enqueued as-is so the hook's internal buffer/split logic gets
// exercised against arbitrary fragmentation (mid-event, multi-event-per-chunk).
function mockStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const c of chunks) controller.enqueue(encoder.encode(c));
      controller.close();
    },
  });
}

describe('useStreamingChat', () => {
  beforeEach(() => { vi.restoreAllMocks(); });
  afterEach(() => { vi.restoreAllMocks(); });

  it('appends user message then accumulates assistant tokens from real SSE events', async () => {
    // Real backend (app/agent/api/v1/chat_router.py + run_agent_loop) emits
    //   event: text_delta\ndata: {"text": "..."}\n\n
    // followed by `event: done`. We assert the hook accumulates `data.text`
    // across text_delta events and ignores housekeeping events.
    vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response(
        mockStream([
          'event: thinking\ndata: {"text": "正在分析..."}\n\n',
          'event: text_delta\ndata: {"text": "你"}\n\n',
          'event: text_delta\ndata: {"text": "好"}\n\n',
          'event: done\ndata: {"session_id": "s1", "message_id": 1}\n\n',
        ]),
        { status: 200, headers: { 'Content-Type': 'text/event-stream' } }
      )
    );

    const { result } = renderHook(() => useStreamingChat());
    await act(async () => {
      await result.current.send('s1', 'hi');
    });

    await waitFor(() => expect(result.current.isStreaming).toBe(false));
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0]).toEqual({ role: 'user', content: 'hi' });
    expect(result.current.messages[1]).toEqual({ role: 'assistant', content: '你好' });
  });

  it('aborts the in-flight stream when abort() is called', async () => {
    // Spy on AbortController.prototype.abort so we don't have to swap the
    // global class out (which leaks if the test fails mid-way).
    const abortSpy = vi.spyOn(AbortController.prototype, 'abort');

    vi.spyOn(global, 'fetch').mockImplementation(
      () => new Promise(() => { /* never resolves so the abort path triggers */ })
    );

    const { result } = renderHook(() => useStreamingChat());

    // Kick off send() but don't await — it will hang on the unresolved fetch.
    act(() => {
      void result.current.send('s1', 'hi');
    });

    // Now abort and verify AbortController.abort() was invoked.
    act(() => {
      result.current.abort();
    });

    expect(abortSpy).toHaveBeenCalled();
  });
});
