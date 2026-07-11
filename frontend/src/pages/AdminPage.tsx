import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { api } from '../lib/api'
import type { User } from '../types'
import {
  ArrowLeft,
  Users,
  Shield,
  Trash2,
  UserCog,
} from 'lucide-react'
import { ThemeToggle } from '../components/ThemeToggle'

export default function AdminPage() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()

  useEffect(() => {
    if (user?.role !== 'admin') {
      navigate('/')
      return
    }
    loadUsers()
  }, [user])

  const loadUsers = async () => {
    try {
      const result = await api.admin.listUsers()
      setUsers(result.users)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleRoleChange = async (userId: number, newRole: string) => {
    try {
      await api.admin.updateUserRole(userId, newRole)
      loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : '修改失败')
    }
  }

  const handleDelete = async (userId: number) => {
    if (!confirm('确定要删除这个用户吗？')) return
    try {
      await api.admin.deleteUser(userId)
      loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  if (user?.role !== 'admin') {
    return null
  }

  return (
    <div className="h-screen flex flex-col bg-slate-50 dark:bg-slate-900">
      {/* Navbar */}
      <header className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md border-b border-slate-100 dark:border-slate-700 z-40 flex-shrink-0">
        <div className="px-4 py-3 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/')}
              className="p-2 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg flex items-center justify-center shadow-sm">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">用户管理</h1>
            </div>
          </div>
          <ThemeToggle />
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 rounded-xl text-sm animate-slide-up">
              {error}
            </div>
          )}

          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-100 dark:border-slate-700 flex items-center gap-2">
              <Users className="w-5 h-5 text-slate-500 dark:text-slate-400" />
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">用户列表</h2>
              <span className="ml-2 px-2 py-0.5 bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 text-xs rounded-full">
                {users.length}
              </span>
            </div>

            {loading ? (
              <div className="p-8 flex items-center justify-center">
                <div className="inline-flex items-center gap-2 text-sm text-slate-400">
                  <div className="w-4 h-4 border-2 border-slate-300 dark:border-slate-600 border-t-blue-500 rounded-full animate-spin" />
                  加载中...
                </div>
              </div>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-700">
                {users.map((u) => (
                  <div
                    key={u.id}
                    className="p-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-slate-200 to-slate-300 dark:from-slate-600 dark:to-slate-700 rounded-full flex items-center justify-center">
                        <UserCog className="w-5 h-5 text-slate-500 dark:text-slate-400" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-slate-900 dark:text-white">
                          {u.username}
                          {u.id === user?.id && (
                            <span className="ml-2 text-xs text-blue-600 dark:text-blue-400">(当前)</span>
                          )}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">{u.email}</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <select
                        value={u.role}
                        onChange={(e) => handleRoleChange(u.id, e.target.value)}
                        disabled={u.id === user?.id}
                        className="px-3 py-1.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg text-sm text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                      >
                        <option value="user">普通用户</option>
                        <option value="admin">管理员</option>
                      </select>

                      {u.id !== user?.id && (
                        <button
                          onClick={() => handleDelete(u.id)}
                          className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-all"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
