import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import KnowledgePage from '../../src/pages/KnowledgePage'

// Mock API
vi.mock('../../src/lib/api', () => ({
  api: {
    knowledge: {
      get: vi.fn().mockResolvedValue({ id: 'test-123', name: 'Test Knowledge' }),
      tree: vi.fn().mockResolvedValue([]),
      file: vi.fn().mockResolvedValue({ content: '# Test', path: 'test.md' }),
      updateFile: vi.fn().mockResolvedValue({}),
    },
  },
}))

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

describe('KnowledgePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state initially', () => {
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
