import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '../../src/stores/authStore'

describe('authStore', () => {
  beforeEach(() => {
    useAuthStore.setState({
      token: null,
      isAuthenticated: false,
      user: null,
    })
  })

  it('has correct initial state', () => {
    const state = useAuthStore.getState()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
    expect(state.user).toBeNull()
  })

  it('login sets token and isAuthenticated', () => {
    useAuthStore.getState().login('test-jwt-token')
    const state = useAuthStore.getState()
    expect(state.token).toBe('test-jwt-token')
    expect(state.isAuthenticated).toBe(true)
  })

  it('login sets user when provided', () => {
    const user = { id: 1, username: 'alice', role: 'admin' }
    useAuthStore.getState().login('token', user)
    const state = useAuthStore.getState()
    expect(state.user).toEqual(user)
    expect(state.isAuthenticated).toBe(true)
  })

  it('login without user sets user to null', () => {
    useAuthStore.getState().login('token')
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('logout clears all state', () => {
    const user = { id: 1, username: 'alice', role: 'admin' }
    useAuthStore.getState().login('token', user)
    useAuthStore.getState().logout()
    const state = useAuthStore.getState()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
    expect(state.user).toBeNull()
  })

  it('setUser updates user data', () => {
    const user = { id: 1, username: 'alice', role: 'user' }
    useAuthStore.getState().setUser(user)
    expect(useAuthStore.getState().user).toEqual(user)
  })

  it('setUser replaces existing user', () => {
    const user1 = { id: 1, username: 'alice', role: 'user' }
    const user2 = { id: 2, username: 'bob', role: 'admin' }
    useAuthStore.getState().setUser(user1)
    useAuthStore.getState().setUser(user2)
    expect(useAuthStore.getState().user).toEqual(user2)
  })

  it('login then logout cycles correctly', () => {
    const user = { id: 1, username: 'alice', role: 'admin' }
    useAuthStore.getState().login('token-1', user)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)

    useAuthStore.getState().logout()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
    expect(useAuthStore.getState().token).toBeNull()

    useAuthStore.getState().login('token-2')
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
    expect(useAuthStore.getState().token).toBe('token-2')
  })
})
