import { useState, useEffect, useCallback } from 'react';
import type { Document } from '../types';
import { listDocuments, uploadDocument, deleteDocument } from '../services/api';

export function useDocuments(projectId: string | null) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    if (!projectId) {
      setDocuments([]);
      return;
    }

    try {
      setIsLoading(true);
      const docs = await listDocuments(projectId);
      setDocuments(docs);
      setError(null);
    } catch (err) {
      setError('Failed to load documents');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const upload = async (file: File) => {
    if (!projectId) {
      throw new Error('No project selected');
    }

    setIsLoading(true);
    setError(null);
    try {
      const result = await uploadDocument(file, projectId);
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

  const remove = async (documentId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await deleteDocument(documentId);
      await fetchDocuments();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Delete failed';
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
    refresh: fetchDocuments,
  };
}
