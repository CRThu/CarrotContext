import { useAuthStore } from '../stores/authStore'
import type { User, Knowledge, TreeNode, FileContent, LockStatus, GitCommit, SearchResult, PermissionGroup, GroupMember, AccessRule } from '../types'

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
      request<FileContent>(`/knowledge/${id}/files/${path}`),
    updateFile: (id: string, path: string, content: string) =>
      request<{ message: string }>(`/knowledge/${id}/files/${path}`, {
        method: 'PUT',
        body: JSON.stringify(content),
      }),
    createDir: (id: string, dirPath: string) =>
      request<{ message: string }>(`/knowledge/${id}/dirs`, {
        method: 'POST',
        body: JSON.stringify({ dir_path: dirPath }),
      }),
    moveFile: (id: string, sourcePath: string, destPath: string) =>
      request<{ message: string }>(`/knowledge/${id}/files/move`, {
        method: 'POST',
        body: JSON.stringify({ source_path: sourcePath, dest_path: destPath }),
      }),
    deleteFile: (id: string, path: string) =>
      request<{ message: string }>(`/knowledge/${id}/files/${path}`, {
        method: 'DELETE',
      }),
    uploadFile: async (id: string, file: File, path: string = '') => {
      const token = useAuthStore.getState().token
      const formData = new FormData()
      formData.append('file', file)
      if (path) formData.append('path', path)

      const response = await fetch(`${API_BASE}/knowledge/${id}/files/upload`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '上传失败' }))
        throw new Error(error.detail || '上传失败')
      }
      return response.json()
    },
    rawFile: (id: string, path: string) => {
      const token = useAuthStore.getState().token
      const headers: Record<string, string> = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      return `${API_BASE}/knowledge/${id}/files/${path}/raw`
    },
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
    log: (id: string, limit?: number, filePath?: string) => {
      const params = new URLSearchParams()
      if (limit) params.append('limit', String(limit))
      if (filePath) params.append('file_path', filePath)
      const query = params.toString()
      return request<GitCommit[]>(`/git/${id}/log${query ? `?${query}` : ''}`)
    },
    diff: (id: string, filePath?: string, commit?: string) => {
      const params = new URLSearchParams()
      if (filePath) params.append('file_path', filePath)
      if (commit) params.append('commit', commit)
      const query = params.toString()
      return request<{ diff: string }>(
        `/git/${id}/diff${query ? `?${query}` : ''}`
      )
    },
    fileAtCommit: (id: string, commit: string, path: string) =>
      request<{ content: string }>(`/git/${id}/file-at-commit?commit=${commit}&path=${encodeURIComponent(path)}`),
    commit: (id: string, message: string, filePath?: string) =>
      request<GitCommit>(`/git/${id}/commit`, {
        method: 'POST',
        body: JSON.stringify({ message, file_path: filePath }),
      }),
    revert: (id: string, commitHash: string) =>
      request<{ message: string }>(`/git/${id}/revert`, {
        method: 'POST',
        body: JSON.stringify({ commit_hash: commitHash }),
      }),
    init: (id: string) =>
      request<{ message: string }>(`/git/${id}/init`, {
        method: 'POST',
      }),
  },
  search: {
    search: (query: string, mode: string = 'all') =>
      request<{ results: SearchResult[]; total: number }>(
        `/search?q=${encodeURIComponent(query)}&mode=${mode}`
      ),
  },
  admin: {
    listUsers: () => request<{ users: User[] }>('/auth/users'),
    updateUserRole: (userId: number, role: string) =>
      request<User>(`/auth/users/${userId}/role`, {
        method: 'PUT',
        body: JSON.stringify({ role }),
      }),
    deleteUser: (userId: number) =>
      request<{ message: string }>(`/auth/users/${userId}`, {
        method: 'DELETE',
      }),
  },
  groups: {
    list: () => request<{ groups: PermissionGroup[] }>('/auth/groups'),
    create: (name: string, description: string = '') =>
      request<PermissionGroup>('/auth/groups', {
        method: 'POST',
        body: JSON.stringify({ name, description }),
      }),
    delete: (groupId: number) =>
      request<{ message: string }>(`/auth/groups/${groupId}`, {
        method: 'DELETE',
      }),
    members: (groupId: number) =>
      request<GroupMember[]>(`/auth/groups/${groupId}/members`),
    addMember: (groupId: number, userId: number) =>
      request<GroupMember>(`/auth/groups/${groupId}/members`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId }),
      }),
    removeMember: (groupId: number, userId: number) =>
      request<{ message: string }>(`/auth/groups/${groupId}/members/${userId}`, {
        method: 'DELETE',
      }),
  },
  permissions: {
    list: (knowledgeId: string) =>
      request<{ rules: AccessRule[] }>(`/knowledge/${knowledgeId}/permissions`),
    set: (knowledgeId: string, groupId: number | null, accessLevel: string) =>
      request<AccessRule>(`/knowledge/${knowledgeId}/permissions`, {
        method: 'POST',
        body: JSON.stringify({ group_id: groupId, access_level: accessLevel }),
      }),
    delete: (knowledgeId: string, ruleId: number) =>
      request<{ message: string }>(`/knowledge/${knowledgeId}/permissions/${ruleId}`, {
        method: 'DELETE',
      }),
  },
}
