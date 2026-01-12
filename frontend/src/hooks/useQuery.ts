import { useState, useCallback } from 'react';
import type { Message } from '../types';
import { queryDocuments } from '../services/api';

export function useQuery(conversationId?: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendQuery = useCallback(async (question: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await queryDocuments({
        question,
        conversation_id: conversationId || undefined,
        include_history: !!conversationId,
      });

      const assistantMessage: Message = {
        id: response.message_id || (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        reasoning: response.reasoning,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get response';
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'error',
        content: `Error: ${errorMessage}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const setMessagesFromConversation = useCallback((msgs: Message[]) => {
    setMessages(msgs);
  }, []);

  return {
    messages,
    isLoading,
    sendQuery,
    clearMessages,
    setMessages: setMessagesFromConversation,
  };
}
