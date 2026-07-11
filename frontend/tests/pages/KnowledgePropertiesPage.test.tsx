import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import KnowledgePropertiesPage from '../../src/pages/KnowledgePropertiesPage'
import { useAuthStore } from '../../src/stores/authStore'

vi.mock('../../src/lib/api', () => ({
  api: {
    knowledge: {
      get: vi.fn().mockResolvedValue({
        id: 'test-kb',
        name: 'Test Knowledge Base',
        description: 'A test knowledge base',
        tags: ['test', 'demo'],
        category: '测试',
        created_by: 'admin',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
        version: 1,
        summary: 'Test summary',
      }),
      update: vi.fn().mockResolvedValue({}),
    },
  },
}))

describe('KnowledgePropertiesPage', () => {
  beforeEach(() => {
    useAuthStore.setState({
      token: 'test-token',
      isAuthenticated: true,
      user: { id: 1, username: 'admin', role: 'admin' },
    })
  })

  it('renders properties page with knowledge info', async () => {
    render(
      <MemoryRouter initialEntries={['/knowledge/test-kb/properties']}>
        <Routes>
          <Route path="/knowledge/:id/properties" element={<KnowledgePropertiesPage />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('知识库属性')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Test Knowledge Base')).toBeInTheDocument()
    })
  })

  it('displays read-only fields', async () => {
    render(
      <MemoryRouter initialEntries={['/knowledge/test-kb/properties']}>
        <Routes>
          <Route path="/knowledge/:id/properties" element={<KnowledgePropertiesPage />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('test-kb')).toBeInTheDocument()
      expect(screen.getByText('admin')).toBeInTheDocument()
    })
  })

  it('displays editable fields for admin', async () => {
    render(
      <MemoryRouter initialEntries={['/knowledge/test-kb/properties']}>
        <Routes>
          <Route path="/knowledge/:id/properties" element={<KnowledgePropertiesPage />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Knowledge Base')).toBeInTheDocument()
      expect(screen.getByDisplayValue('A test knowledge base')).toBeInTheDocument()
    })
  })

  it('shows save button for admin', async () => {
    render(
      <MemoryRouter initialEntries={['/knowledge/test-kb/properties']}>
        <Routes>
          <Route path="/knowledge/:id/properties" element={<KnowledgePropertiesPage />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /保存/ })).toBeInTheDocument()
    })
  })
})
