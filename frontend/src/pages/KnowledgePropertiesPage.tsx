import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { api } from '../lib/api'
import type { Knowledge } from '../types'
import {
  ArrowLeft,
  Save,
  Settings,
  Tag,
  Calendar,
  User,
  Hash,
} from 'lucide-react'
import { ThemeToggle } from '../components/ThemeToggle'

export default function KnowledgePropertiesPage() {
  const { id } = useParams<{ id: string }>()
  const [kb, setKb] = useState<Knowledge | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Editable fields
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState('')
  const [category, setCategory] = useState('')
  const [summary, setSummary] = useState('')

  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()

  const canEdit = user?.role === 'admin'

  useEffect(() => {
    if (id) loadKnowledge(id)
  }, [id])

  const loadKnowledge = async (kbId: string) => {
    try {
      const data = await api.knowledge.get(kbId)
      setKb(data)
      setName(data.name)
      setDescription(data.description || '')
      setTags(data.tags?.join(', ') || '')
      setCategory(data.category || '')
      setSummary(data.summary || '')
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!id) return
    setSaving(true)
    setError('')
    setSuccess('')

    try {
      const tagList = tags.split(',').map((t) => t.trim()).filter(Boolean)
      await api.knowledge.update(id, {
        name,
        description,
        tags: tagList,
        category,
        summary,
      })
      setSuccess('保存成功')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="inline-flex items-center gap-2 text-sm text-slate-400">
          <div className="w-4 h-4 border-2 border-slate-300 dark:border-slate-600 border-t-blue-500 rounded-full animate-spin" />
          加载中...
        </div>
      </div>
    )
  }

  if (!kb) {
    return (
      <div className="h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <p className="text-slate-500 dark:text-slate-400">知识库不存在</p>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-slate-50 dark:bg-slate-900">
      {/* Navbar */}
      <header className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md border-b border-slate-100 dark:border-slate-700 z-40 flex-shrink-0">
        <div className="px-4 py-3 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(`/knowledge/${id}`)}
              className="p-2 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-slate-500 to-slate-600 rounded-lg flex items-center justify-center shadow-sm">
                <Settings className="w-4 h-4 text-white" />
              </div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">知识库属性</h1>
            </div>
          </div>
          <ThemeToggle />
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto p-6 space-y-6">
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 rounded-xl text-sm animate-slide-up">
              {error}
            </div>
          )}

          {success && (
            <div className="p-3 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 text-green-600 dark:text-green-400 rounded-xl text-sm animate-slide-up">
              {success}
            </div>
          )}

          {/* Read-only info */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-6">
            <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-4">基本信息</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-sm">
                <Hash className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                <span className="text-slate-500 dark:text-slate-400 w-20">ID</span>
                <span className="text-slate-900 dark:text-white font-mono">{kb.id}</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <User className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                <span className="text-slate-500 dark:text-slate-400 w-20">创建者</span>
                <span className="text-slate-900 dark:text-white">{kb.created_by}</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Calendar className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                <span className="text-slate-500 dark:text-slate-400 w-20">创建时间</span>
                <span className="text-slate-900 dark:text-white">{new Date(kb.created_at).toLocaleString('zh-CN')}</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Calendar className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                <span className="text-slate-500 dark:text-slate-400 w-20">更新时间</span>
                <span className="text-slate-900 dark:text-white">{new Date(kb.updated_at).toLocaleString('zh-CN')}</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Hash className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                <span className="text-slate-500 dark:text-slate-400 w-20">版本</span>
                <span className="text-slate-900 dark:text-white">v{kb.version}</span>
              </div>
            </div>
          </div>

          {/* Editable fields */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-6">
            <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-4">编辑属性</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">名称</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={!canEdit}
                  className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-sm text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">分类</label>
                <input
                  type="text"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  disabled={!canEdit}
                  className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-sm text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">描述</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={!canEdit}
                  rows={3}
                  className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-sm text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-none disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                  <span className="flex items-center gap-1.5">
                    <Tag className="w-3.5 h-3.5" />
                    标签 (逗号分隔)
                  </span>
                </label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  disabled={!canEdit}
                  placeholder="python, backend"
                  className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-sm text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">摘要</label>
                <textarea
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  disabled={!canEdit}
                  rows={4}
                  placeholder="知识库内容摘要..."
                  className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-sm text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-none disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              {canEdit && (
                <div className="flex justify-end pt-2">
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-xl transition-all duration-200 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Save className="w-4 h-4" />
                    {saving ? '保存中...' : '保存'}
                  </button>
                </div>
              )}

              {!canEdit && (
                <p className="text-xs text-slate-400 dark:text-slate-500 text-center">
                  只有管理员可以编辑属性
                </p>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
