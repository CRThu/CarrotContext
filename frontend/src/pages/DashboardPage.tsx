import { useEffect, useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useKnowledgeStore } from '../stores/knowledgeStore'
import { api } from '../lib/api'
import type { Knowledge } from '../types'
import {
  Plus,
  LogOut,
  Trash2,
  BookOpen,
  FolderOpen,
  Folder,
  ChevronRight,
  ChevronDown,
  FileText,
  ExternalLink,
  Tag,
  User,
  Calendar,
} from 'lucide-react'

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [newTags, setNewTags] = useState('')
  const [newCategory, setNewCategory] = useState('默认')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [selectedKB, setSelectedKB] = useState<Knowledge | null>(null)
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set())

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
      await api.knowledge.create(newName, newDescription, tags, newCategory || '默认')
      setShowCreateModal(false)
      setNewName('')
      setNewDescription('')
      setNewTags('')
      setNewCategory('默认')
      loadKnowledge()
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这个知识库吗？')) return
    try {
      await api.knowledge.delete(id)
      if (selectedKB?.id === id) setSelectedKB(null)
      loadKnowledge()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  // Group KBs by category
  const categoryGroups = useMemo(() => {
    const groups: Record<string, Knowledge[]> = {}
    knowledgeList.forEach((kb) => {
      const cat = kb.category || '默认'
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(kb)
    })
    return groups
  }, [knowledgeList])

  const categories = Object.keys(categoryGroups).sort()

  const toggleCategory = (cat: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev)
      if (next.has(cat)) next.delete(cat)
      else next.add(cat)
      return next
    })
  }

  const allCategories = useMemo(() => {
    const cats = new Set<string>()
    knowledgeList.forEach((kb) => cats.add(kb.category || '默认'))
    return Array.from(cats).sort()
  }, [knowledgeList])

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      {/* Navbar */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-100 z-40 flex-shrink-0">
        <div className="px-4 py-3 flex justify-between items-center">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
              <BookOpen className="w-4 h-4 text-white" />
            </div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">CarrotContext</h1>
          </div>
          <div className="flex items-center gap-3">
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

      {/* Two-column layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <aside className="w-72 bg-white border-r border-slate-200/60 flex flex-col overflow-hidden flex-shrink-0">
          <div className="p-3 border-b border-slate-100">
            <button
              onClick={() => setShowCreateModal(true)}
              className="w-full flex items-center justify-center gap-1.5 px-3 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-sm"
            >
              <Plus className="w-4 h-4" />
              新建知识库
            </button>
          </div>

          <div className="flex-1 overflow-y-auto scrollbar-thin p-2">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="inline-flex items-center gap-2 text-sm text-slate-400">
                  <div className="w-4 h-4 border-2 border-slate-300 border-t-blue-500 rounded-full animate-spin" />
                  加载中...
                </div>
              </div>
            ) : knowledgeList.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 px-4">
                <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mb-3">
                  <FolderOpen className="w-6 h-6 text-slate-300" />
                </div>
                <p className="text-sm text-slate-400 text-center">暂无知识库</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="mt-3 text-xs text-blue-600 hover:text-blue-700 font-medium"
                >
                  创建第一个知识库
                </button>
              </div>
            ) : (
              <div className="space-y-0.5">
                {/* All KBs */}
                <button
                  onClick={() => { setSelectedCategory(null); setSelectedKB(null) }}
                  className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm transition-colors ${
                    !selectedCategory
                      ? 'bg-blue-50 text-blue-600 font-medium'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <BookOpen className="w-4 h-4 flex-shrink-0" />
                  <span className="truncate">全部知识库</span>
                  <span className="ml-auto text-xs text-slate-400">{knowledgeList.length}</span>
                </button>

                {/* Category groups */}
                {categories.map((cat) => {
                  const isExpanded = expandedCategories.has(cat)
                  const isSelected = selectedCategory === cat
                  const kbs = categoryGroups[cat]

                  return (
                    <div key={cat}>
                      <button
                        onClick={() => { toggleCategory(cat); setSelectedCategory(cat); setSelectedKB(null) }}
                        className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm transition-colors ${
                          isSelected && !isExpanded
                            ? 'bg-blue-50 text-blue-600 font-medium'
                            : 'text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        <span className="flex-shrink-0">
                          {isExpanded ? (
                            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                          )}
                        </span>
                        {isExpanded ? (
                          <FolderOpen className="w-4 h-4 text-blue-500 flex-shrink-0" />
                        ) : (
                          <Folder className="w-4 h-4 text-blue-500 flex-shrink-0" />
                        )}
                        <span className="truncate">{cat}</span>
                        <span className="ml-auto text-xs text-slate-400">{kbs.length}</span>
                      </button>

                      {isExpanded && (
                        <div className="border-l border-slate-100 ml-4">
                          {kbs.map((kb) => (
                            <button
                              key={kb.id}
                              onClick={() => setSelectedKB(kb)}
                              className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm transition-colors ${
                                selectedKB?.id === kb.id
                                  ? 'bg-blue-50 text-blue-600 font-medium'
                                  : 'text-slate-600 hover:bg-slate-50'
                              }`}
                            >
                              <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                              <span className="truncate">{kb.name}</span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </aside>

        {/* Right Content Area */}
        <main className="flex-1 overflow-y-auto bg-slate-50">
          <div className="max-w-3xl mx-auto p-8">
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 rounded-xl text-sm animate-slide-up">
                {error}
              </div>
            )}

            {!selectedKB ? (
              <div className="flex flex-col items-center justify-center min-h-[500px]">
                <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mb-4">
                  <BookOpen className="w-8 h-8 text-slate-300" />
                </div>
                <p className="text-slate-500 text-sm">
                  {knowledgeList.length === 0 ? '暂无知识库，点击左侧按钮创建' : '选择一个知识库查看详情'}
                </p>
              </div>
            ) : (
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-8 animate-fade-in">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-slate-900 mb-2">{selectedKB.name}</h2>
                    <p className="text-sm text-slate-500">{selectedKB.description || '暂无描述'}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => navigate(`/knowledge/${selectedKB.id}`)}
                      className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-sm"
                    >
                      <ExternalLink className="w-4 h-4" />
                      打开
                    </button>
                    <button
                      onClick={() => handleDelete(selectedKB.id)}
                      className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  {selectedKB.tags && selectedKB.tags.length > 0 && (
                    <div className="flex items-center gap-2">
                      <Tag className="w-4 h-4 text-slate-400" />
                      <div className="flex flex-wrap gap-1.5">
                        {selectedKB.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-2.5 py-0.5 bg-slate-100 text-slate-600 text-xs rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex items-center gap-2 text-sm text-slate-500">
                    <User className="w-4 h-4 text-slate-400" />
                    <span>创建者: {selectedKB.created_by}</span>
                  </div>

                  <div className="flex items-center gap-2 text-sm text-slate-500">
                    <Calendar className="w-4 h-4 text-slate-400" />
                    <span>创建时间: {new Date(selectedKB.created_at).toLocaleDateString('zh-CN')}</span>
                  </div>

                  {selectedKB.summary && (
                    <div className="pt-4 border-t border-slate-100">
                      <p className="text-sm text-slate-600 leading-relaxed">{selectedKB.summary}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </main>
      </div>

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
                <label className="block text-sm font-medium text-slate-700 mb-1.5">分类</label>
                <input
                  type="text"
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  list="category-list"
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                  placeholder="输入分类名称"
                />
                <datalist id="category-list">
                  {allCategories.map((cat) => (
                    <option key={cat} value={cat} />
                  ))}
                </datalist>
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
