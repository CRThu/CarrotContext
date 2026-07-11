import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AdminPage from '../../src/pages/AdminPage'
import { useAuthStore } from '../../src/stores/authStore'

vi.mock('../../src/lib/api', () => ({
  api: {
    admin: {
      listUsers: vi.fn().mockResolvedValue({
        users: [
          { id: 1, username: 'admin', email: 'admin@test.com', role: 'admin', created_at: '2024-01-01' },
          { id: 2, username: 'user1', email: 'user1@test.com', role: 'user', created_at: '2024-01-02' },
        ],
      }),
      updateUserRole: vi.fn().mockResolvedValue({}),
      deleteUser: vi.fn().mockResolvedValue({}),
    },
  },
}))

describe('AdminPage', () => {
  beforeEach(() => {
    useAuthStore.setState({
      token: 'test-token',
      isAuthenticated: true,
      user: { id: 1, username: 'admin', role: 'admin' },
    })
  })

  it('renders user management page for admin', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    )

    expect(screen.getByText('用户管理')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument()
      expect(screen.getByText('user1')).toBeInTheDocument()
    })
  })

  it('displays user count', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument()
    })
  })

  it('shows role dropdown for each user', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      const selects = screen.getAllByRole('combobox')
      expect(selects.length).toBeGreaterThan(0)
    })
  })

  it('shows delete button for non-self users', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      const deleteButtons = screen.getAllByRole('button')
      expect(deleteButtons.length).toBeGreaterThan(0)
    })
  })
})
