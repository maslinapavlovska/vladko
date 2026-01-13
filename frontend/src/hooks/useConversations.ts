import { useState, useEffect, useCallback } from 'react';
import type { Chat, ChatDetail } from '../types';
import {
  listChats,
  createChat,
  getChat,
  updateChat,
  deleteChat,
} from '../services/api';

export function useConversations(projectId: string | null) {
  const [conversations, setConversations] = useState<Chat[]>([]);
  const [activeConversation, setActiveConversation] = useState<ChatDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load chats list for current project
  const loadConversations = useCallback(async () => {
    if (!projectId) {
      setConversations([]);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const result = await listChats(projectId);
      setConversations(result.chats);
    } catch (err) {
      setError('Failed to load chats');
      console.error('Error loading chats:', err);
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  // Load a specific chat with messages
  const loadConversation = useCallback(async (id: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const chat = await getChat(id);
      setActiveConversation(chat);
      return chat;
    } catch (err) {
      setError('Failed to load chat');
      console.error('Error loading chat:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Create a new chat
  const create = useCallback(async (title?: string) => {
    if (!projectId) {
      setError('No project selected');
      return null;
    }

    setError(null);
    try {
      const chat = await createChat(projectId, title);
      setConversations(prev => [chat, ...prev]);
      // Load the full chat detail
      const detail = await getChat(chat.id);
      setActiveConversation(detail);
      return chat;
    } catch (err) {
      setError('Failed to create chat');
      console.error('Error creating chat:', err);
      return null;
    }
  }, [projectId]);

  // Update chat title
  const update = useCallback(async (id: string, title: string) => {
    setError(null);
    try {
      const updated = await updateChat(id, title);
      setConversations(prev =>
        prev.map(c => (c.id === id ? { ...c, title: updated.title } : c))
      );
      if (activeConversation?.id === id) {
        setActiveConversation(prev => prev ? { ...prev, title: updated.title } : null);
      }
      return updated;
    } catch (err) {
      setError('Failed to update chat');
      console.error('Error updating chat:', err);
      return null;
    }
  }, [activeConversation?.id]);

  // Delete a chat
  const remove = useCallback(async (id: string) => {
    setError(null);
    try {
      await deleteChat(id);
      setConversations(prev => prev.filter(c => c.id !== id));
      if (activeConversation?.id === id) {
        setActiveConversation(null);
      }
      return true;
    } catch (err) {
      setError('Failed to delete chat');
      console.error('Error deleting chat:', err);
      return false;
    }
  }, [activeConversation?.id]);

  // Clear active chat (start fresh)
  const clearActive = useCallback(() => {
    setActiveConversation(null);
  }, []);

  // Refresh the active chat (after new messages)
  const refreshActive = useCallback(async () => {
    if (activeConversation?.id) {
      await loadConversation(activeConversation.id);
    }
  }, [activeConversation?.id, loadConversation]);

  // Load chats when project changes
  useEffect(() => {
    loadConversations();
    // Clear active conversation when project changes
    setActiveConversation(null);
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
