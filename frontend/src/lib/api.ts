import { useAuthStore } from '../stores/authStore'
import type { User, Knowledge, TreeNode, FileContent, LockStatus, GitCommit, SearchResult } from '../types'

const API_BASE = '/api'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = useAuthStore.getState().token
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || '请求失败')
  }

  return response.json()
}

export const api = {
  auth: {
    login: (username: string, password: string) =>
      request<{ access_token: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      }),
    register: (username: string, email: string, password: string) =>
      request<User>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, email, password }),
      }),
    me: () => request<User>('/auth/me'),
  },
  knowledge: {
    list: () => request<Knowledge[]>('/knowledge'),
    get: (id: string) => request<Knowledge>(`/knowledge/${id}`),
    create: (name: string, description: string, tags: string[], category: string = '默认') =>
      request<Knowledge>('/knowledge', {
        method: 'POST',
        body: JSON.stringify({ name, description, tags, category }),
      }),
    update: (id: string, data: Partial<Knowledge>) =>
      request<Knowledge>(`/knowledge/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<{ message: string }>(`/knowledge/${id}`, { method: 'DELETE' }),
    tree: (id: string, path?: string) =>
      request<TreeNode[]>(`/knowledge/${id}/tree${path ? `?path=${path}` : ''}`),
    file: (id: string, path: string) =>
      request<FileContent>(`/knowledge/${id}/file/${path}`),
    updateFile: (id: string, path: string, content: string) =>
      request<{ message: string }>(`/knowledge/${id}/file/${path}`, {
        method: 'PUT',
        body: JSON.stringify(content),
      }),
  },
  lock: {
    acquire: (knowledgeId: string, filePath: string) =>
      request<LockStatus>('/lock', {
        method: 'POST',
        body: JSON.stringify({ knowledge_id: knowledgeId, file_path: filePath }),
      }),
    release: (knowledgeId: string, filePath: string) =>
      request<LockStatus>('/lock', {
        method: 'DELETE',
        body: JSON.stringify({ knowledge_id: knowledgeId, file_path: filePath }),
      }),
    status: (knowledgeId: string, filePath: string) =>
      request<LockStatus>(`/lock/status?knowledge_id=${knowledgeId}&file_path=${filePath}`),
  },
  git: {
    log: (id: string, limit?: number) =>
      request<GitCommit[]>(`/git/${id}/log${limit ? `?limit=${limit}` : ''}`),
    diff: (id: string, _filePath?: string, _commit?: string) =>
      request<{ diff: string }>(`/git/${id}/diff`, {
        method: 'GET',
      }),
    commit: (id: string, message: string, filePath?: string) =>
      request<GitCommit>(`/git/${id}/commit`, {
        method: 'POST',
        body: JSON.stringify({ message, file_path: filePath }),
      }),
  },
  search: {
    search: (query: string, mode: string = 'all') =>
      request<{ results: SearchResult[]; total: number }>(
        `/search?q=${encodeURIComponent(query)}&mode=${mode}`
      ),
  },
}
