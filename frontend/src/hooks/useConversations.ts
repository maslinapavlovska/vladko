import { useState, useEffect, useCallback } from 'react';
import type { Conversation, ConversationDetail } from '../types';
import {
  listConversations,
  createConversation,
  getConversation,
  updateConversation,
  deleteConversation,
} from '../services/api';

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<ConversationDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load conversations list
  const loadConversations = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await listConversations();
      setConversations(result.conversations);
    } catch (err) {
      setError('Failed to load conversations');
      console.error('Error loading conversations:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load a specific conversation with messages
  const loadConversation = useCallback(async (id: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const conversation = await getConversation(id);
      setActiveConversation(conversation);
      return conversation;
    } catch (err) {
      setError('Failed to load conversation');
      console.error('Error loading conversation:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Create a new conversation
  const create = useCallback(async (title?: string) => {
    setError(null);
    try {
      const conversation = await createConversation(title);
      setConversations(prev => [conversation, ...prev]);
      // Load the full conversation detail
      const detail = await getConversation(conversation.id);
      setActiveConversation(detail);
      return conversation;
    } catch (err) {
      setError('Failed to create conversation');
      console.error('Error creating conversation:', err);
      return null;
    }
  }, []);

  // Update conversation title
  const update = useCallback(async (id: string, title: string) => {
    setError(null);
    try {
      const updated = await updateConversation(id, title);
      setConversations(prev =>
        prev.map(c => (c.id === id ? { ...c, title: updated.title } : c))
      );
      if (activeConversation?.id === id) {
        setActiveConversation(prev => prev ? { ...prev, title: updated.title } : null);
      }
      return updated;
    } catch (err) {
      setError('Failed to update conversation');
      console.error('Error updating conversation:', err);
      return null;
    }
  }, [activeConversation?.id]);

  // Delete a conversation
  const remove = useCallback(async (id: string) => {
    setError(null);
    try {
      await deleteConversation(id);
      setConversations(prev => prev.filter(c => c.id !== id));
      if (activeConversation?.id === id) {
        setActiveConversation(null);
      }
      return true;
    } catch (err) {
      setError('Failed to delete conversation');
      console.error('Error deleting conversation:', err);
      return false;
    }
  }, [activeConversation?.id]);

  // Clear active conversation (start fresh)
  const clearActive = useCallback(() => {
    setActiveConversation(null);
  }, []);

  // Refresh the active conversation (after new messages)
  const refreshActive = useCallback(async () => {
    if (activeConversation?.id) {
      await loadConversation(activeConversation.id);
    }
  }, [activeConversation?.id, loadConversation]);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  return {
    conversations,
    activeConversation,
    isLoading,
    error,
    loadConversations,
    loadConversation,
    create,
    update,
    remove,
    clearActive,
    refreshActive,
    setActiveConversation,
  };
}
