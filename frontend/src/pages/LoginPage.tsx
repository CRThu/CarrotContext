import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { api } from '../lib/api'
import { BookOpen } from 'lucide-react'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const login = useAuthStore((state) => state.login)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const result = await api.auth.login(username, password)
      login(result.access_token)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 relative overflow-hidden">
      {/* Decorative background orbs */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-blue-100/60 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-indigo-100/60 rounded-full blur-3xl" />

      <div className="relative max-w-md w-full mx-4 space-y-8 p-10 bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-100 animate-fade-in">
        {/* Logo */}
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/25 mb-4">
            <BookOpen className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">CarrotContext</h1>
          <p className="mt-1.5 text-sm text-slate-500">企业知识库管理系统</p>
        </div>

        <form className="space-y-5" onSubmit={handleSubmit}>
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-600 rounded-xl text-sm animate-slide-up">
              {error}
            </div>
          )}

          <div className="space-y-1.5">
            <label htmlFor="username" className="block text-sm font-medium text-slate-700">
              用户名
            </label>
            <input
              id="username"
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              placeholder="请输入用户名"
            />
          </div>

          <div className="space-y-1.5">
            <label htmlFor="password" className="block text-sm font-medium text-slate-700">
              密码
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              placeholder="请输入密码"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:ring-offset-2 transition-all duration-200 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '登录中...' : '登录'}
          </button>
        </form>
      </div>
    </div>
  )
}
