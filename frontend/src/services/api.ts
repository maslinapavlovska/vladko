import axios from 'axios';
import type { HealthStatus, QueryRequest, QueryResponse, UploadResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for LLM generation
});

export async function checkHealth(): Promise<HealthStatus> {
  try {
    const response = await api.get('/health');
    return {
      api: 'ok',
      ollama: response.data.ollama === 'ok' ? 'ok' : 'unreachable',
    };
  } catch {
    return { api: 'error', ollama: 'unreachable' };
  }
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000, // 5 minutes for large PDFs
  });
  return response.data;
}

export async function listDocuments(): Promise<string[]> {
  const response = await api.get('/documents');
  return response.data;
}

export async function deleteDocument(filename: string): Promise<void> {
  await api.delete(`/documents/${encodeURIComponent(filename)}`);
}

export async function queryDocuments(request: QueryRequest): Promise<QueryResponse> {
  const response = await api.post('/query', request);
  return response.data;
}

export async function resetDatabase(): Promise<void> {
  await api.delete('/reset');
}
