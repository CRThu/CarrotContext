import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

// Mock stores
vi.mock('../../src/stores/knowledgeStore', () => ({
  useKnowledgeStore: vi.fn((selector) => {
    const state = {
      currentKnowledge: { id: 'test-123', name: 'Test Knowledge' },
      fileTree: [],
      setCurrentKnowledge: vi.fn(),
      setFileTree: vi.fn(),
    }
    return selector(state)
  }),
}))

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ id: 'test-123' }),
    useNavigate: () => vi.fn(),
  }
})

// Mock API with mutable refs so beforeEach can re-set implementations
const mockGet = vi.fn().mockResolvedValue({ id: 'test-123', name: 'Test Knowledge' })
const mockTree = vi.fn().mockResolvedValue([])
const mockFile = vi.fn().mockResolvedValue({ content: '# Test', path: 'test.md' })
const mockUpdateFile = vi.fn().mockResolvedValue({})

vi.mock('../../src/lib/api', () => ({
  api: {
    knowledge: {
      get: (...args: unknown[]) => mockGet(...args),
      tree: (...args: unknown[]) => mockTree(...args),
      file: (...args: unknown[]) => mockFile(...args),
      updateFile: (...args: unknown[]) => mockUpdateFile(...args),
    },
  },
}))

import KnowledgePage from '../../src/pages/KnowledgePage'

describe('KnowledgePage', () => {
  beforeEach(() => {
    mockGet.mockResolvedValue({ id: 'test-123', name: 'Test Knowledge' })
    mockTree.mockResolvedValue([])
    mockFile.mockResolvedValue({ content: '# Test', path: 'test.md' })
    mockUpdateFile.mockResolvedValue({})
  })

  it('shows loading state initially', async () => {
    // Override to never-resolving to prevent state updates
    mockGet.mockReturnValue(new Promise(() => {}))
    mockTree.mockReturnValue(new Promise(() => {}))

    render(
      <MemoryRouter>
        <KnowledgePage />
      </MemoryRouter>
    )
    expect(screen.getByText('加载中...')).toBeInTheDocument()
  })

  it('renders after loading', async () => {
    render(
      <MemoryRouter>
        <KnowledgePage />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.queryByText('加载中...')).not.toBeInTheDocument()
    })
    expect(screen.getByText('Test Knowledge')).toBeInTheDocument()
  })

  it('shows file selection prompt', async () => {
    render(
      <MemoryRouter>
        <KnowledgePage />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByText('选择一个文件查看内容')).toBeInTheDocument()
    })
  })
})
