import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import RegisterPage from '../../src/pages/RegisterPage'
import { useAuthStore } from '../../src/stores/authStore'

vi.mock('../../src/lib/api', () => ({
  api: {
    auth: {
      register: vi.fn().mockResolvedValue({}),
      login: vi.fn().mockResolvedValue({ access_token: 'test-token' }),
      me: vi.fn().mockResolvedValue({ id: 1, username: 'testuser', role: 'user' }),
    },
  },
}))

describe('RegisterPage', () => {
  beforeEach(() => {
    useAuthStore.setState({ token: null, isAuthenticated: false })
  })

  it('renders registration form', () => {
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    )
    expect(screen.getByText('注册新账号')).toBeInTheDocument()
    expect(screen.getByLabelText('用户名')).toBeInTheDocument()
    expect(screen.getByLabelText('邮箱')).toBeInTheDocument()
    expect(screen.getByLabelText('密码')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '注册' })).toBeInTheDocument()
  })

  it('renders login link', () => {
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    )
    expect(screen.getByText('返回登录')).toBeInTheDocument()
  })

  it('renders theme toggle', () => {
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    )
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBeGreaterThan(1)
  })
})
