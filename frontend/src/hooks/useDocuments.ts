import { useState, useEffect, useCallback } from 'react';
import { listDocuments, uploadDocument, deleteDocument, resetDatabase } from '../services/api';

export function useDocuments() {
  const [documents, setDocuments] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
      setError(null);
    } catch (err) {
      setError('Failed to load documents');
      console.error(err);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const upload = async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await uploadDocument(file);
      await fetchDocuments();
      return result;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Upload failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const remove = async (filename: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await deleteDocument(filename);
      await fetchDocuments();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Delete failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const reset = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await resetDatabase();
      setDocuments([]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Reset failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    documents,
    isLoading,
    error,
    upload,
    remove,
    reset,
    refresh: fetchDocuments,
  };
}
