import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useKnowledgeStore } from '../stores/knowledgeStore'
import { api } from '../lib/api'
import type { Knowledge } from '../types'

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
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">CarrotContext</h1>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              新建知识库
            </button>
            <button
              onClick={logout}
              className="px-4 py-2 text-gray-600 hover:text-gray-900"
            >
              退出登录
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-8">加载中...</div>
        ) : knowledgeList.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">暂无知识库</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              创建第一个知识库
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {knowledgeList.map((item: Knowledge) => (
              <div
                key={item.id}
                className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => navigate(`/knowledge/${item.id}`)}
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.name}</h3>
                <p className="text-gray-600 text-sm mb-4 line-clamp-2">{item.description || '暂无描述'}</p>
                <div className="flex flex-wrap gap-2 mb-4">
                  {item.tags?.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="flex justify-between items-center text-xs text-gray-500">
                  <span>创建者: {item.created_by}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(item.id)
                    }}
                    className="text-red-500 hover:text-red-700"
                  >
                    删除
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold mb-4">新建知识库</h2>
            <form onSubmit={handleCreate}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">名称</label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                <textarea
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  rows={3}
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">标签 (逗号分隔)</label>
                <input
                  type="text"
                  value={newTags}
                  onChange={(e) => setNewTags(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="python, backend"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-900"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
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
