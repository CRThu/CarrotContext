import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import GitHistory from '../../src/components/GitHistory/GitHistory'
import { useKnowledgeStore } from '../../src/stores/knowledgeStore'

vi.mock('../../src/lib/api', () => ({
  api: {
    git: {
      log: vi.fn().mockResolvedValue([
        { hash: 'abc12345', message: 'Initial commit', author: 'admin', date: '2024-01-01T00:00:00Z' },
        { hash: 'def67890', message: 'Update files', author: 'admin', date: '2024-01-02T00:00:00Z' },
      ]),
      diff: vi.fn().mockResolvedValue({ diff: '@@ -1 +1 @@\n-old\n+new' }),
    },
  },
}))

describe('GitHistory', () => {
  beforeEach(() => {
    useKnowledgeStore.setState({
      currentKnowledge: { id: 'test-kb', name: 'Test KB' },
    })
  })

  it('renders commit list', async () => {
    render(<GitHistory knowledgeId="test-kb" />)
    await waitFor(() => {
      expect(screen.getByText('Initial commit')).toBeInTheDocument()
      expect(screen.getByText('Update files')).toBeInTheDocument()
    })
  })

  it('displays commit hash (short)', async () => {
    render(<GitHistory knowledgeId="test-kb" />)
    await waitFor(() => {
      expect(screen.getByText('abc12345')).toBeInTheDocument()
      expect(screen.getByText('def67890')).toBeInTheDocument()
    })
  })

  it('displays commit author', async () => {
    render(<GitHistory knowledgeId="test-kb" />)
    await waitFor(() => {
      const authors = screen.getAllByText('admin')
      expect(authors.length).toBeGreaterThanOrEqual(2)
    })
  })

  it('shows refresh button', async () => {
    render(<GitHistory knowledgeId="test-kb" />)
    await waitFor(() => {
      expect(screen.getByText('刷新')).toBeInTheDocument()
    })
  })

  it('shows empty state when no commits', async () => {
    const { api } = await import('../../src/lib/api')
    vi.mocked(api.git.log).mockResolvedValueOnce([])
    render(<GitHistory knowledgeId="test-kb" />)
    await waitFor(() => {
      expect(screen.getByText('暂无提交历史')).toBeInTheDocument()
    })
  })
})
