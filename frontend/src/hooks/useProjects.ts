import { useState, useEffect, useCallback } from 'react';
import type { Project, ProjectDetail } from '../types';
import {
  listProjects,
  createProject as createProjectApi,
  getProject as getProjectApi,
  updateProject as updateProjectApi,
  deleteProject as deleteProjectApi,
} from '../services/api';

interface UseProjectsReturn {
  projects: Project[];
  loading: boolean;
  error: string | null;
  activeProject: ProjectDetail | null;
  setActiveProjectId: (id: string | null) => void;
  createProject: (name: string, description?: string, color?: string) => Promise<Project>;
  updateProject: (id: string, data: { name?: string; description?: string; color?: string }) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  refreshProjects: () => Promise<void>;
}

export function useProjects(): UseProjectsReturn {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [activeProject, setActiveProject] = useState<ProjectDetail | null>(null);

  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listProjects();
      setProjects(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchActiveProject = useCallback(async (id: string) => {
    try {
      const data = await getProjectApi(id, true);
      setActiveProject(data);
    } catch (err) {
      console.error('Failed to fetch project details:', err);
      setActiveProject(null);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  useEffect(() => {
    if (activeProjectId) {
      fetchActiveProject(activeProjectId);
    } else {
      setActiveProject(null);
    }
  }, [activeProjectId, fetchActiveProject]);

  const createProject = useCallback(async (name: string, description?: string, color?: string): Promise<Project> => {
    const project = await createProjectApi(name, description, color);
    setProjects((prev) => [project, ...prev]);
    return project;
  }, []);

  const updateProject = useCallback(async (id: string, data: { name?: string; description?: string; color?: string }) => {
    const updated = await updateProjectApi(id, data);
    setProjects((prev) => prev.map((p) => (p.id === id ? { ...p, ...updated } : p)));
    if (activeProjectId === id) {
      setActiveProject((prev) => prev ? { ...prev, ...updated } : null);
    }
  }, [activeProjectId]);

  const deleteProject = useCallback(async (id: string) => {
    await deleteProjectApi(id);
    setProjects((prev) => prev.filter((p) => p.id !== id));
    if (activeProjectId === id) {
      setActiveProjectId(null);
      setActiveProject(null);
    }
  }, [activeProjectId]);

  return {
    projects,
    loading,
    error,
    activeProject,
    setActiveProjectId,
    createProject,
    updateProject,
    deleteProject,
    refreshProjects: fetchProjects,
  };
}
