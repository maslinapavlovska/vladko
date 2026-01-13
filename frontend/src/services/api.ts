import axios from 'axios';
import type {
  HealthStatus,
  QueryRequest,
  QueryResponse,
  UploadResponse,
  Project,
  ProjectDetail,
  Document,
  Chat,
  ChatDetail,
  ChatList,
  ChatSearchResult,
} from '../types';

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

// ==================== Project API ====================

export async function listProjects(): Promise<Project[]> {
  const response = await api.get('/projects');
  return response.data.projects;
}

export async function createProject(name: string, description?: string, color?: string): Promise<Project> {
  const response = await api.post('/projects', { name, description, color });
  return response.data;
}

export async function getProject(id: string, detailed = false): Promise<ProjectDetail> {
  const response = await api.get(`/projects/${id}`, {
    params: { detailed },
  });
  return response.data;
}

export async function updateProject(id: string, data: { name?: string; description?: string; color?: string }): Promise<Project> {
  const response = await api.patch(`/projects/${id}`, data);
  return response.data;
}

export async function deleteProject(id: string): Promise<{ status: string; deleted_documents: number; deleted_chats: number }> {
  const response = await api.delete(`/projects/${id}`);
  return response.data;
}

// ==================== Document API ====================

export async function uploadDocument(file: File, projectId: string): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/documents/upload', formData, {
    params: { project_id: projectId },
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000, // 5 minutes for large PDFs
  });
  return response.data;
}

export async function listDocuments(projectId: string): Promise<Document[]> {
  const response = await api.get('/documents', {
    params: { project_id: projectId },
  });
  return response.data.documents;
}

export async function getDocument(id: string): Promise<Document> {
  const response = await api.get(`/documents/${id}`);
  return response.data;
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/documents/${id}`);
}

// ==================== Query API ====================

export async function queryDocuments(request: QueryRequest): Promise<QueryResponse> {
  const response = await api.post('/query', request);
  return response.data;
}

export async function resetDatabase(): Promise<void> {
  await api.delete('/reset');
}

// ==================== Chat API ====================

export async function listChats(projectId: string, page = 1, perPage = 20): Promise<ChatList> {
  const response = await api.get('/conversations', {
    params: { project_id: projectId, page, per_page: perPage },
  });
  return response.data;
}

export async function createChat(projectId: string, title?: string): Promise<Chat> {
  const response = await api.post('/conversations', title ? { title } : {}, {
    params: { project_id: projectId },
  });
  return response.data;
}

export async function getChat(id: string): Promise<ChatDetail> {
  const response = await api.get(`/conversations/${id}`);
  return response.data;
}

export async function updateChat(id: string, title: string): Promise<Chat> {
  const response = await api.patch(`/conversations/${id}`, { title });
  return response.data;
}

export async function deleteChat(id: string): Promise<void> {
  await api.delete(`/conversations/${id}`);
}

export async function searchChats(projectId: string, query: string, limit = 20): Promise<ChatSearchResult[]> {
  const response = await api.get('/conversations/search', {
    params: { project_id: projectId, q: query, limit },
  });
  return response.data;
}

// Legacy aliases for backwards compatibility
export const listConversations = (projectId: string, page?: number, perPage?: number) => listChats(projectId, page, perPage);
export const createConversation = (projectId: string, title?: string) => createChat(projectId, title);
export const getConversation = getChat;
export const updateConversation = updateChat;
export const deleteConversation = deleteChat;
export const searchConversations = searchChats;
