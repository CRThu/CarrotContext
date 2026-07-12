import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useToastStore } from '../stores/toastStore'
import { api } from '../lib/api'
import type { Knowledge, PermissionGroup, AccessRule } from '../types'
import {
  ArrowLeft,
  Save,
  Settings,
  Tag,
  Calendar,
  User,
  Hash,
  Shield,
  Plus,
  Trash2,
  X,
} from 'lucide-react'
import { ThemeToggle } from '../components/ThemeToggle'

const ACCESS_LEVELS = [
  { value: 'manage', label: '管理', description: '完全控制', color: 'purple' },
  { value: 'write', label: '写入', description: '编辑文件', color: 'blue' },
  { value: 'read', label: '只读', description: '查看内容', color: 'green' },
  { value: 'none', label: '无权限', description: '拒绝访问', color: 'gray' },
]

export default function KnowledgePropertiesPage() {
  const { id } = useParams<{ id: string }>()
  const [kb, setKb] = useState<Knowledge | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')
  const [category, setCategory] = useState('')
  const [summary, setSummary] = useState('')

  const [rules, setRules] = useState<AccessRule[]>([])
  const [groups, setGroups] = useState<PermissionGroup[]>([])
  const [newRuleGroupId, setNewRuleGroupId] = useState<number | ''>('')
  const [newRuleLevel, setNewRuleLevel] = useState('read')
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)

  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()
  const addToast = useToastStore((s) => s.addToast)

  const canEdit = user?.role === 'admin'

  useEffect(() => {
    if (id) {
      loadKnowledge(id)
      if (canEdit) {
        loadRules(id)
        loadGroups()
      }
    }
  }, [id])

  const loadKnowledge = async (kbId: string) => {
    try {
      const data = await api.knowledge.get(kbId)
      setKb(data)
      setName(data.name)
      setDescription(data.description || '')
      setTags(data.tags || [])
      setCategory(data.category || '')
      setSummary(data.summary || '')
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const loadRules = async (kbId: string) => {
    try {
      const result = await api.permissions.list(kbId)
      setRules(result.rules)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载权限失败')
    }
  }

  const loadGroups = async () => {
    try {
      const result = await api.groups.list()
      setGroups(result.groups)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载组失败')
    }
  }

  const handleSave = async () => {
    if (!id) return
    setSaving(true)
    setError('')
    try {
      await api.knowledge.update(id, { name, description, tags, category, summary })
      addToast({ type: 'success', message: '保存成功' })
    } catch (err) {
      addToast({ type: 'error', message: err instanceof Error ? err.message : '保存失败' })
    } finally {
      setSaving(false)
    }
  }

  const handleAddTag = () => {
    const trimmed = tagInput.trim()
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed])
      setTagInput('')
    }
  }

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag))
  }

  const handleAddRule = async () => {
    if (!id || newRuleGroupId === '') return
    try {
      await api.permissions.set(id, newRuleGroupId as number, newRuleLevel)
      setNewRuleGroupId('')
      setNewRuleLevel('read')
      loadRules(id)
      addToast({ type: 'success', message: '权限设置成功' })
    } catch (err) {
      addToast({ type: 'error', message: err instanceof Error ? err.message : '添加规则失败' })
    }
  }

  const handleDeleteRule = async (ruleId: number) => {
    if (!id) return
    try {
      await api.permissions.delete(id, ruleId)
      loadRules(id)
      setDeleteConfirm(null)
      addToast({ type: 'success', message: '权限已删除' })
    } catch (err) {
      addToast({ type: 'error', message: err instanceof Error ? err.message : '删除规则失败' })
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

  const availableGroups = groups.filter((g) => !rules.some((r) => r.group_id === g.id))

  return (
    <div className="h-screen flex flex-col bg-slate-50 dark:bg-slate-900">
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

      <main className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto p-6 space-y-6">
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 rounded-xl text-sm animate-slide-up">
              {error}
            </div>
          )}

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
                  placeholder="输入分类..."
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
                    标签
                  </span>
                </label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full"
                    >
                      {tag}
                      {canEdit && (
                        <button onClick={() => handleRemoveTag(tag)} className="hover:text-blue-800 dark:hover:text-blue-200">
                          <X className="w-3 h-3" />
                        </button>
                      )}
                    </span>
                  ))}
                </div>
                {canEdit && (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddTag() } }}
                      placeholder="输入标签后回车..."
                      className="flex-1 px-4 py-2.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-sm text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                    />
                    <button
                      onClick={handleAddTag}
                      disabled={!tagInput.trim()}
                      className="px-3 py-2.5 text-white bg-blue-500 hover:bg-blue-600 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                )}
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

          {canEdit && (
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-6">
              <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-4 flex items-center gap-2">
                <Shield className="w-4 h-4" />
                访问规则
              </h3>

              <div className="space-y-2 mb-4">
                {rules.length === 0 ? (
                  <p className="text-xs text-slate-400 dark:text-slate-500">暂无访问规则</p>
                ) : (
                  rules.map((rule) => (
                    <div
                      key={rule.id}
                      className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700/50 rounded-xl"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                          {rule.group_name || '匿名'}
                        </span>
                        <span className="text-xs text-slate-400">→</span>
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                          rule.access_level === 'manage'
                            ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400'
                            : rule.access_level === 'write'
                            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                            : rule.access_level === 'read'
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                            : 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400'
                        }`}>
                          {ACCESS_LEVELS.find((l) => l.value === rule.access_level)?.label}
                        </span>
                      </div>
                      {deleteConfirm === rule.id ? (
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleDeleteRule(rule.id)}
                            className="px-2 py-1 text-xs font-medium text-white bg-red-500 hover:bg-red-600 rounded transition-colors"
                          >
                            确认
                          </button>
                          <button
                            onClick={() => setDeleteConfirm(null)}
                            className="px-2 py-1 text-xs font-medium text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
                          >
                            取消
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setDeleteConfirm(rule.id)}
                          className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-all"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  ))
                )}
              </div>

              {availableGroups.length > 0 && (
                <div className="flex items-center gap-2 pt-2 border-t border-slate-100 dark:border-slate-700">
                  <select
                    value={newRuleGroupId}
                    onChange={(e) => setNewRuleGroupId(e.target.value ? Number(e.target.value) : '')}
                    className="flex-1 px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg text-sm text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  >
                    <option value="">选择组...</option>
                    {availableGroups.map((g) => (
                      <option key={g.id} value={g.id}>{g.name}</option>
                    ))}
                  </select>
                  <div className="flex gap-1">
                    {ACCESS_LEVELS.map((l) => (
                      <button
                        key={l.value}
                        onClick={() => setNewRuleLevel(l.value)}
                        className={`px-2 py-2 text-xs font-medium rounded-lg transition-all ${
                          newRuleLevel === l.value
                            ? l.color === 'purple'
                              ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400'
                              : l.color === 'blue'
                              ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                              : l.color === 'green'
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                              : 'bg-slate-200 dark:bg-slate-600 text-slate-600 dark:text-slate-300'
                            : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                        }`}
                        title={l.description}
                      >
                        {l.label}
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={handleAddRule}
                    disabled={newRuleGroupId === ''}
                    className="p-2 text-white bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              )}

              {groups.length === 0 && (
                <p className="text-xs text-slate-400 dark:text-slate-500 pt-2 border-t border-slate-100 dark:border-slate-700">
                  请先在管理后台创建组
                </p>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
