import { create } from 'zustand'
import type { Knowledge, TreeNode, FileContent } from '../types'

interface KnowledgeState {
  knowledgeList: Knowledge[]
  currentKnowledge: Knowledge | null
  fileTree: TreeNode[]
  currentFile: FileContent | null
  setKnowledgeList: (list: Knowledge[]) => void
  setCurrentKnowledge: (knowledge: Knowledge | null) => void
  setFileTree: (tree: TreeNode[]) => void
  setCurrentFile: (file: FileContent | null) => void
}

export const useKnowledgeStore = create<KnowledgeState>((set) => ({
  knowledgeList: [],
  currentKnowledge: null,
  fileTree: [],
  currentFile: null,
  setKnowledgeList: (list) => set({ knowledgeList: list }),
  setCurrentKnowledge: (knowledge) => set({ currentKnowledge: knowledge }),
  setFileTree: (tree) => set({ fileTree: tree }),
  setCurrentFile: (file) => set({ currentFile: file }),
}))
