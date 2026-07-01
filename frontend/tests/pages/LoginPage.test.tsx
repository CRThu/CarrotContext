import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import LoginPage from '../../src/pages/LoginPage'
import { useAuthStore } from '../../src/stores/authStore'

vi.mock('../../src/lib/api', () => ({
  api: {
    auth: {
      login: vi.fn().mockResolvedValue({ access_token: 'test-token' }),
    },
  },
}))

describe('LoginPage', () => {
  beforeEach(() => {
    useAuthStore.setState({ token: null, isAuthenticated: false })
  })

  it('renders login form', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )
    expect(screen.getByText('CarrotContext')).toBeInTheDocument()
    expect(screen.getByText('企业知识库管理系统')).toBeInTheDocument()
    expect(screen.getByLabelText('用户名')).toBeInTheDocument()
    expect(screen.getByLabelText('密码')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument()
  })

  it('renders input placeholders', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )
    expect(screen.getByPlaceholderText('请输入用户名')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('请输入密码')).toBeInTheDocument()
  })
})
