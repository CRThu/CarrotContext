export interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'user'
  created_at: string
  updated_at: string
}

export interface Knowledge {
  id: string
  name: string
  description: string
  created_by: string
  created_at: string
  updated_by: string
  updated_at: string
  tags: string[]
  summary: string
  version: number
  category: string
}

export interface TreeNode {
  name: string
  path: string
  is_dir: boolean
  children?: TreeNode[]
}

export interface FileContent {
  path: string
  content: string
  size: number
  modified_at: string
  is_binary?: boolean
}

export interface LockStatus {
  knowledge_id: string
  file_path: string
  locked: boolean
  locked_by?: string
  locked_at?: string
}

export interface GitCommit {
  hash: string
  author: string
  email: string
  date: string
  message: string
}

export interface SearchResult {
  knowledge_id: string
  file_path: string
  title: string
  score: number
  snippet: string
}
