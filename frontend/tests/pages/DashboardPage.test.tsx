import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import DashboardPage from '../../src/pages/DashboardPage'
import { useAuthStore } from '../../src/stores/authStore'
import { useKnowledgeStore } from '../../src/stores/knowledgeStore'

vi.mock('../../src/lib/api', () => ({
  api: {
    knowledge: {
      list: vi.fn().mockResolvedValue([]),
      delete: vi.fn().mockResolvedValue({ message: 'ok' }),
    },
  },
}))

describe('DashboardPage', () => {
  beforeEach(() => {
    useAuthStore.setState({ token: 'test-token', isAuthenticated: true })
    useKnowledgeStore.setState({ knowledgeList: [] })
  })

  it('renders dashboard with header', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    )
    expect(screen.getByText('CarrotContext')).toBeInTheDocument()
    expect(screen.getByText('新建知识库')).toBeInTheDocument()
    expect(screen.getByText('退出登录')).toBeInTheDocument()
  })

  it('shows loading state initially', () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    )
    expect(screen.getByText('加载中...')).toBeInTheDocument()
  })
})
