import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api } from '../../src/lib/api'
import { useAuthStore } from '../../src/stores/authStore'

// Mock fetch globally
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('api client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.setState({ token: null })
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    })
  })

  describe('request helper', () => {
    it('sends request to correct path', async () => {
      await api.auth.me()
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/auth/me',
        expect.objectContaining({ headers: expect.any(Object) })
      )
    })

    it('includes Authorization header when token exists', async () => {
      useAuthStore.setState({ token: 'test-token' })
      await api.auth.me()
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].headers['Authorization']).toBe('Bearer test-token')
    })

    it('does not include Authorization header when no token', async () => {
      await api.auth.me()
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].headers['Authorization']).toBeUndefined()
    })

    it('throws error on non-ok response', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: 'Not found' }),
      })
      await expect(api.auth.me()).rejects.toThrow('Not found')
    })

    it('throws generic error when response body has no detail', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({}),
      })
      await expect(api.auth.me()).rejects.toThrow('请求失败')
    })

    it('throws generic error when response.json() fails', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.reject(new Error('parse error')),
      })
      await expect(api.auth.me()).rejects.toThrow('请求失败')
    })
  })

  describe('auth', () => {
    it('login sends POST with credentials', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ access_token: 'jwt-123' }),
      })
      const result = await api.auth.login('user', 'pass')
      expect(result.access_token).toBe('jwt-123')
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('POST')
      expect(JSON.parse(callArgs[1].body)).toEqual({ username: 'user', password: 'pass' })
    })

    it('register sends POST with user data', async () => {
      const user = { id: 1, username: 'new', email: 'n@t.com', role: 'user', created_at: '', updated_at: '' }
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(user),
      })
      const result = await api.auth.register('new', 'n@t.com', 'pass123')
      expect(result.username).toBe('new')
    })

    it('me sends GET', async () => {
      const user = { id: 1, username: 'alice', email: 'a@t.com', role: 'admin', created_at: '', updated_at: '' }
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(user),
      })
      const result = await api.auth.me()
      expect(result.username).toBe('alice')
      expect(mockFetch.mock.calls[0][1].method).toBeUndefined()
    })
  })

  describe('knowledge', () => {
    it('list sends GET', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([]),
      })
      await api.knowledge.list()
      expect(mockFetch).toHaveBeenCalledWith('/api/knowledge', expect.any(Object))
    })

    it('get sends GET with id', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ id: 'kb-1' }),
      })
      await api.knowledge.get('kb-1')
      expect(mockFetch).toHaveBeenCalledWith('/api/knowledge/kb-1', expect.any(Object))
    })

    it('create sends POST with body', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ id: 'new' }),
      })
      await api.knowledge.create('New KB', 'desc', ['tag1'], 'cat')
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('POST')
      expect(JSON.parse(callArgs[1].body)).toEqual({
        name: 'New KB', description: 'desc', tags: ['tag1'], category: 'cat',
      })
    })

    it('delete sends DELETE', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ message: 'deleted' }),
      })
      await api.knowledge.delete('kb-1')
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[0]).toBe('/api/knowledge/kb-1')
      expect(callArgs[1].method).toBe('DELETE')
    })

    it('tree sends GET with path query', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([]),
      })
      await api.knowledge.tree('kb-1', 'src')
      expect(mockFetch).toHaveBeenCalledWith('/api/knowledge/kb-1/tree?path=src', expect.any(Object))
    })

    it('tree without path omits query', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([]),
      })
      await api.knowledge.tree('kb-1')
      expect(mockFetch).toHaveBeenCalledWith('/api/knowledge/kb-1/tree', expect.any(Object))
    })

    it('updateFile sends PUT', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ message: 'ok' }),
      })
      await api.knowledge.updateFile('kb-1', 'test.md', 'new content')
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[0]).toBe('/api/knowledge/kb-1/files/test.md')
      expect(callArgs[1].method).toBe('PUT')
    })

    it('moveFile sends POST', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ message: 'ok' }),
      })
      await api.knowledge.moveFile('kb-1', 'old.txt', 'new.txt')
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('POST')
      expect(JSON.parse(callArgs[1].body)).toEqual({
        source_path: 'old.txt', dest_path: 'new.txt',
      })
    })

    it('createDir sends POST', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ message: 'ok' }),
      })
      await api.knowledge.createDir('kb-1', 'newdir')
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('POST')
    })

    it('rawFile returns correct URL', () => {
      const url = api.knowledge.rawFile('kb-1', 'image.png')
      expect(url).toBe('/api/knowledge/kb-1/files/image.png/raw')
    })
  })

  describe('lock', () => {
    it('acquire sends POST', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ locked: true }),
      })
      await api.lock.acquire('kb-1', 'file.md')
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('POST')
    })

    it('release sends DELETE', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ locked: false }),
      })
      await api.lock.release('kb-1', 'file.md')
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('DELETE')
    })

    it('status sends GET', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ locked: false }),
      })
      await api.lock.status('kb-1', 'file.md')
      expect(mockFetch.mock.calls[0][0]).toContain('/api/lock/status?')
    })
  })

  describe('git', () => {
    it('log sends GET with limit', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([]),
      })
      await api.git.log('kb-1', 5)
      expect(mockFetch.mock.calls[0][0]).toBe('/api/git/kb-1/log?limit=5')
    })

    it('diff sends GET with params', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ diff: '' }),
      })
      await api.git.diff('kb-1', 'file.md', 'abc123')
      const url = mockFetch.mock.calls[0][0]
      expect(url).toContain('file_path=file.md')
      expect(url).toContain('commit=abc123')
    })

    it('commit sends POST', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ hash: 'abc' }),
      })
      await api.git.commit('kb-1', 'my commit', 'file.md')
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('POST')
      expect(JSON.parse(callArgs[1].body)).toEqual({
        message: 'my commit', file_path: 'file.md',
      })
    })
  })

  describe('search', () => {
    it('search sends GET with query and mode', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ results: [], total: 0 }),
      })
      await api.search.search('test query', 'metadata')
      const url = mockFetch.mock.calls[0][0]
      expect(url).toContain('q=test%20query')
      expect(url).toContain('mode=metadata')
    })
  })

  describe('admin', () => {
    it('listUsers sends GET', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ users: [] }),
      })
      await api.admin.listUsers()
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/users', expect.any(Object))
    })

    it('updateUserRole sends PUT', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      })
      await api.admin.updateUserRole(1, 'admin')
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('PUT')
      expect(JSON.parse(callArgs[1].body)).toEqual({ role: 'admin' })
    })

    it('deleteUser sends DELETE', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      })
      await api.admin.deleteUser(1)
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('DELETE')
    })
  })

  describe('groups', () => {
    it('list sends GET', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ groups: [] }),
      })
      await api.groups.list()
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/groups', expect.any(Object))
    })

    it('create sends POST', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      })
      await api.groups.create('editors', 'Editors group')
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('POST')
      expect(JSON.parse(callArgs[1].body)).toEqual({ name: 'editors', description: 'Editors group' })
    })

    it('delete sends DELETE', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      })
      await api.groups.delete(5)
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('DELETE')
    })

    it('addMember sends POST', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      })
      await api.groups.addMember(1, 2)
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('POST')
      expect(JSON.parse(callArgs[1].body)).toEqual({ user_id: 2 })
    })

    it('removeMember sends DELETE', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      })
      await api.groups.removeMember(1, 2)
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('DELETE')
    })
  })

  describe('permissions', () => {
    it('list sends GET', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ rules: [] }),
      })
      await api.permissions.list('kb-1')
      expect(mockFetch).toHaveBeenCalledWith('/api/knowledge/kb-1/permissions', expect.any(Object))
    })

    it('set sends POST', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      })
      await api.permissions.set('kb-1', 1, 'write')
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('POST')
      expect(JSON.parse(callArgs[1].body)).toEqual({ group_id: 1, access_level: 'write' })
    })

    it('set with null group_id', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      })
      await api.permissions.set('kb-1', null, 'read')
      const callArgs = mockFetch.mock.calls[0]
      expect(JSON.parse(callArgs[1].body)).toEqual({ group_id: null, access_level: 'read' })
    })

    it('delete sends DELETE', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      })
      await api.permissions.delete('kb-1', 10)
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].method).toBe('DELETE')
    })
  })
})
