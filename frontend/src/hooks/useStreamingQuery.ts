import { useState, useCallback, useRef } from 'react';
import type {
  Citation,
  Reasoning,
  StreamStatus,
  StreamState,
  OptionValidation,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface SSEEvent {
  type: string;
  data: unknown;
}

function parseSSEEvents(buffer: string): { parsed: SSEEvent[]; remaining: string } {
  const events: SSEEvent[] = [];
  const lines = buffer.split('\n');

  let currentEvent: { type?: string; data?: string } = {};
  let processedUpTo = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.startsWith('event: ')) {
      currentEvent.type = line.slice(7);
    } else if (line.startsWith('data: ')) {
      currentEvent.data = line.slice(6);
    } else if (line === '' && currentEvent.type && currentEvent.data) {
      try {
        events.push({
          type: currentEvent.type,
          data: JSON.parse(currentEvent.data),
        });
      } catch (e) {
        console.warn('Failed to parse SSE data:', currentEvent.data);
      }
      currentEvent = {};
      processedUpTo = lines.slice(0, i + 1).join('\n').length + 1;
    }
  }

  return {
    parsed: events,
    remaining: buffer.slice(processedUpTo),
  };
}

export function useStreamingQuery() {
  const [state, setState] = useState<StreamState>({
    status: null,
    partialAnswer: '',
    citations: null,
    reasoning: null,
    optionsValidation: null,
    isStreaming: false,
    error: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const resetState = useCallback(() => {
    setState({
      status: null,
      partialAnswer: '',
      citations: null,
      reasoning: null,
      optionsValidation: null,
      isStreaming: false,
      error: null,
    });
  }, []);

  const handleEvent = useCallback((event: SSEEvent) => {
    switch (event.type) {
      case 'status':
        setState(prev => ({
          ...prev,
          status: event.data as StreamStatus,
        }));
        break;

      case 'token':
        setState(prev => ({
          ...prev,
          partialAnswer: prev.partialAnswer + (event.data as { content: string }).content,
        }));
        break;

      case 'citations':
        setState(prev => ({
          ...prev,
          citations: (event.data as { citations: Citation[] }).citations,
        }));
        break;

      case 'validation':
        setState(prev => ({
          ...prev,
          optionsValidation: (event.data as { options_validation: OptionValidation[] }).options_validation,
        }));
        break;

      case 'reasoning':
        setState(prev => ({
          ...prev,
          reasoning: (event.data as { reasoning: Reasoning }).reasoning,
        }));
        break;

      case 'done':
        setState(prev => ({
          ...prev,
          isStreaming: false,
          status: { stage: 'complete', message: 'Complete' },
        }));
        break;

      case 'error':
        setState(prev => ({
          ...prev,
          error: (event.data as { message: string }).message,
          isStreaming: false,
        }));
        break;
    }
  }, []);

  const sendQuery = useCallback(async (question: string, chatId?: string, projectId?: string) => {
    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    setState(prev => ({
      ...prev,
      isStreaming: true,
      partialAnswer: '',
      citations: null,
      reasoning: null,
      optionsValidation: null,
      error: null,
      status: { stage: 'detecting', message: 'Starting...' },
    }));

    try {
      const response = await fetch(`${API_BASE_URL}/query/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          chat_id: chatId,
          project_id: projectId,
          include_history: !!chatId,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const { parsed, remaining } = parseSSEEvents(buffer);
        buffer = remaining;

        for (const event of parsed) {
          handleEvent(event);
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        // Request was cancelled, don't set error
        return;
      }

      setState(prev => ({
        ...prev,
        error: err instanceof Error ? err.message : 'Stream failed',
        isStreaming: false,
      }));
    }
  }, [handleEvent]);

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setState(prev => ({
      ...prev,
      isStreaming: false,
    }));
  }, []);

  return {
    ...state,
    sendQuery,
    cancel,
    resetState,
  };
}
