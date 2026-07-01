import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useKnowledgeStore } from '../stores/knowledgeStore'
import { api } from '../lib/api'
import type { Knowledge } from '../types'
import { Plus, LogOut, Trash2, BookOpen, FolderOpen } from 'lucide-react'

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [newTags, setNewTags] = useState('')

  const logout = useAuthStore((state) => state.logout)
  const knowledgeList = useKnowledgeStore((state) => state.knowledgeList)
  const setKnowledgeList = useKnowledgeStore((state) => state.setKnowledgeList)
  const navigate = useNavigate()

  useEffect(() => {
    loadKnowledge()
  }, [])

  const loadKnowledge = async () => {
    try {
      const list = await api.knowledge.list()
      setKnowledgeList(list)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const tags = newTags.split(',').map((t) => t.trim()).filter(Boolean)
      await api.knowledge.create(newName, newDescription, tags)
      setShowCreateModal(false)
      setNewName('')
      setNewDescription('')
      setNewTags('')
      loadKnowledge()
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这个知识库吗？')) return
    try {
      await api.knowledge.delete(id)
      loadKnowledge()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navbar */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-100 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
              <BookOpen className="w-4 h-4 text-white" />
            </div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">CarrotContext</h1>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-sm"
            >
              <Plus className="w-4 h-4" />
              新建知识库
            </button>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-slate-500 hover:text-slate-800 rounded-xl transition-colors"
            >
              <LogOut className="w-4 h-4" />
              退出登录
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 rounded-xl text-sm animate-slide-up">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-flex items-center gap-2 text-sm text-slate-400">
              <div className="w-4 h-4 border-2 border-slate-300 border-t-blue-500 rounded-full animate-spin" />
              加载中...
            </div>
          </div>
        ) : knowledgeList.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <FolderOpen className="w-8 h-8 text-slate-300" />
            </div>
            <p className="text-slate-500 text-sm">暂无知识库</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-sm"
            >
              <Plus className="w-4 h-4" />
              创建第一个知识库
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {knowledgeList.map((item: Knowledge) => (
              <div
                key={item.id}
                className="bg-white rounded-xl border border-slate-100 shadow-sm p-6 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 cursor-pointer group"
                onClick={() => navigate(`/knowledge/${item.id}`)}
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-base font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">{item.name}</h3>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(item.id)
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-300 hover:text-red-500 rounded-lg hover:bg-red-50 transition-all"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-sm text-slate-500 mb-4 line-clamp-2">{item.description || '暂无描述'}</p>
                {item.tags && item.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {item.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-0.5 bg-slate-100 text-slate-600 text-xs rounded-md"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                <div className="flex items-center text-xs text-slate-400">
                  <span>创建者: {item.created_by}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md mx-4 shadow-xl shadow-slate-200/50 border border-slate-100 animate-slide-up">
            <h2 className="text-lg font-semibold text-slate-900 mb-5">新建知识库</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">名称</label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                  placeholder="输入知识库名称"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">描述</label>
                <textarea
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-none"
                  rows={3}
                  placeholder="输入知识库描述"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">标签 (逗号分隔)</label>
                <input
                  type="text"
                  value={newTags}
                  onChange={(e) => setNewTags(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                  placeholder="python, backend"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-sm text-slate-500 hover:text-slate-800 rounded-xl transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-xl transition-all duration-200 shadow-sm"
                >
                  创建
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
