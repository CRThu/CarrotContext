import { describe, it, expect, beforeEach } from 'vitest'
import { useKnowledgeStore } from '../../src/stores/knowledgeStore'

describe('knowledgeStore', () => {
  beforeEach(() => {
    useKnowledgeStore.setState({
      knowledgeList: [],
      currentKnowledge: null,
      fileTree: [],
      currentFile: null,
    })
  })

  it('has correct initial state', () => {
    const state = useKnowledgeStore.getState()
    expect(state.knowledgeList).toEqual([])
    expect(state.currentKnowledge).toBeNull()
    expect(state.fileTree).toEqual([])
    expect(state.currentFile).toBeNull()
  })

  it('setKnowledgeList sets the list', () => {
    const list = [
      { id: 'kb-1', name: 'KB 1', description: 'd1', created_by: 'u1', created_at: '', updated_by: 'u1', updated_at: '', tags: [], summary: '', version: 1, category: '默认' },
      { id: 'kb-2', name: 'KB 2', description: 'd2', created_by: 'u2', created_at: '', updated_by: 'u2', updated_at: '', tags: [], summary: '', version: 1, category: '默认' },
    ]
    useKnowledgeStore.getState().setKnowledgeList(list)
    expect(useKnowledgeStore.getState().knowledgeList).toEqual(list)
    expect(useKnowledgeStore.getState().knowledgeList).toHaveLength(2)
  })

  it('setKnowledgeList replaces existing list', () => {
    useKnowledgeStore.getState().setKnowledgeList([{ id: 'old', name: 'Old', description: '', created_by: '', created_at: '', updated_by: '', updated_at: '', tags: [], summary: '', version: 1, category: '默认' }])
    useKnowledgeStore.getState().setKnowledgeList([])
    expect(useKnowledgeStore.getState().knowledgeList).toEqual([])
  })

  it('setCurrentKnowledge sets current knowledge', () => {
    const kb = { id: 'kb-1', name: 'Test KB', description: 'test', created_by: 'u1', created_at: '', updated_by: 'u1', updated_at: '', tags: ['tag1'], summary: 'sum', version: 1, category: '默认' }
    useKnowledgeStore.getState().setCurrentKnowledge(kb)
    expect(useKnowledgeStore.getState().currentKnowledge).toEqual(kb)
  })

  it('setCurrentKnowledge can set to null', () => {
    const kb = { id: 'kb-1', name: 'Test KB', description: '', created_by: '', created_at: '', updated_by: '', updated_at: '', tags: [], summary: '', version: 1, category: '默认' }
    useKnowledgeStore.getState().setCurrentKnowledge(kb)
    useKnowledgeStore.getState().setCurrentKnowledge(null)
    expect(useKnowledgeStore.getState().currentKnowledge).toBeNull()
  })

  it('setFileTree sets the tree', () => {
    const tree = [
      { name: 'readme.md', path: 'readme.md', is_dir: false },
      { name: 'src', path: 'src', is_dir: true, children: [] },
    ]
    useKnowledgeStore.getState().setFileTree(tree)
    expect(useKnowledgeStore.getState().fileTree).toEqual(tree)
    expect(useKnowledgeStore.getState().fileTree).toHaveLength(2)
  })

  it('setCurrentFile sets current file', () => {
    const file = { path: 'test.md', content: '# Hello', size: 100, modified_at: '' }
    useKnowledgeStore.getState().setCurrentFile(file)
    expect(useKnowledgeStore.getState().currentFile).toEqual(file)
  })

  it('setCurrentFile can set to null', () => {
    const file = { path: 'test.md', content: '', size: 0, modified_at: '' }
    useKnowledgeStore.getState().setCurrentFile(file)
    useKnowledgeStore.getState().setCurrentFile(null)
    expect(useKnowledgeStore.getState().currentFile).toBeNull()
  })

  it('all setters work independently', () => {
    const kb = { id: 'kb-1', name: 'KB', description: '', created_by: '', created_at: '', updated_by: '', updated_at: '', tags: [], summary: '', version: 1, category: '默认' }
    const tree = [{ name: 'f.md', path: 'f.md', is_dir: false }]
    const file = { path: 'f.md', content: 'data', size: 4, modified_at: '' }

    useKnowledgeStore.getState().setCurrentKnowledge(kb)
    useKnowledgeStore.getState().setFileTree(tree)
    useKnowledgeStore.getState().setCurrentFile(file)

    const state = useKnowledgeStore.getState()
    expect(state.currentKnowledge).toEqual(kb)
    expect(state.fileTree).toEqual(tree)
    expect(state.currentFile).toEqual(file)
    expect(state.knowledgeList).toEqual([])
  })
})
