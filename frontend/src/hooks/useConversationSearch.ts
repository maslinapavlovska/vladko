import { useState, useEffect, useCallback, useRef } from 'react';
import { searchChats } from '../services/api';
import type { ChatSearchResult } from '../types';

interface UseConversationSearchOptions {
  debounceMs?: number;
  minQueryLength?: number;
}

interface UseConversationSearchReturn {
  query: string;
  setQuery: (query: string) => void;
  results: ChatSearchResult[];
  isSearching: boolean;
  isActive: boolean;
  error: string | null;
  clearSearch: () => void;
}

export function useConversationSearch(
  projectId: string | null,
  options: UseConversationSearchOptions = {}
): UseConversationSearchReturn {
  const { debounceMs = 300, minQueryLength = 1 } = options;

  const [query, setQuery] = useState('');
  const [results, setResults] = useState<ChatSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const timerRef = useRef<number | null>(null);

  const isActive = query.length >= minQueryLength && projectId !== null;

  useEffect(() => {
    // Clear results if query is too short or no project
    if (!isActive || !projectId) {
      setResults([]);
      setError(null);
      return;
    }

    // Clear previous timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    // Debounce search
    timerRef.current = window.setTimeout(async () => {
      setIsSearching(true);
      setError(null);

      try {
        const response = await searchChats(projectId, query);
        setResults(response);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message || 'Search failed');
        }
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    }, debounceMs);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [query, projectId, debounceMs, isActive]);

  // Clear search when project changes
  useEffect(() => {
    setQuery('');
    setResults([]);
    setError(null);
  }, [projectId]);

  const clearSearch = useCallback(() => {
    setQuery('');
    setResults([]);
    setError(null);
  }, []);

  return {
    query,
    setQuery,
    results,
    isSearching,
    isActive,
    error,
    clearSearch,
  };
}
