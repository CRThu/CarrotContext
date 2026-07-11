import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { api } from '../lib/api'
import type { User, PermissionGroup, GroupMember } from '../types'
import {
  ArrowLeft,
  Users,
  Shield,
  Trash2,
  UserCog,
  Plus,
  UserPlus,
  UserMinus,
} from 'lucide-react'
import { ThemeToggle } from '../components/ThemeToggle'

type Tab = 'users' | 'groups'

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>('users')
  const [users, setUsers] = useState<User[]>([])
  const [groups, setGroups] = useState<PermissionGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Group management state
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null)
  const [groupMembers, setGroupMembers] = useState<GroupMember[]>([])
  const [newGroupName, setNewGroupName] = useState('')
  const [newGroupDesc, setNewGroupDesc] = useState('')
  const [showNewGroup, setShowNewGroup] = useState(false)

  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()

  useEffect(() => {
    if (user?.role !== 'admin') {
      navigate('/')
      return
    }
    loadData()
  }, [user])

  const loadData = async () => {
    try {
      const [usersResult, groupsResult] = await Promise.all([
        api.admin.listUsers(),
        api.groups.list(),
      ])
      setUsers(usersResult.users)
      setGroups(groupsResult.groups)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleRoleChange = async (userId: number, newRole: string) => {
    try {
      await api.admin.updateUserRole(userId, newRole)
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : '修改失败')
    }
  }

  const handleDelete = async (userId: number) => {
    if (!confirm('确定要删除这个用户吗？')) return
    try {
      await api.admin.deleteUser(userId)
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) return
    try {
      await api.groups.create(newGroupName.trim(), newGroupDesc.trim())
      setNewGroupName('')
      setNewGroupDesc('')
      setShowNewGroup(false)
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败')
    }
  }

  const handleDeleteGroup = async (groupId: number) => {
    if (!confirm('确定要删除这个组吗？关联的访问规则也会被删除。')) return
    try {
      await api.groups.delete(groupId)
      if (selectedGroup === groupId) {
        setSelectedGroup(null)
        setGroupMembers([])
      }
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  const loadGroupMembers = async (groupId: number) => {
    setSelectedGroup(groupId)
    try {
      const members = await api.groups.members(groupId)
      setGroupMembers(members)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载成员失败')
    }
  }

  const handleAddMember = async (groupId: number, userId: number) => {
    try {
      await api.groups.addMember(groupId, userId)
      loadGroupMembers(groupId)
    } catch (err) {
      setError(err instanceof Error ? err.message : '添加失败')
    }
  }

  const handleRemoveMember = async (groupId: number, userId: number) => {
    try {
      await api.groups.removeMember(groupId, userId)
      loadGroupMembers(groupId)
    } catch (err) {
      setError(err instanceof Error ? err.message : '移除失败')
    }
  }

  if (user?.role !== 'admin') {
    return null
  }

  const nonMembers = users.filter(
    (u) => !groupMembers.some((m) => m.user_id === u.id)
  )

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
              <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">管理后台</h1>
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

          {/* Tabs */}
          <div className="flex gap-1 mb-6 bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700 p-1">
            <button
              onClick={() => setTab('users')}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                tab === 'users'
                  ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <Users className="w-4 h-4" />
              用户管理
            </button>
            <button
              onClick={() => setTab('groups')}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                tab === 'groups'
                  ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <Users className="w-4 h-4" />
              组管理
            </button>
          </div>

          {loading ? (
            <div className="p-8 flex items-center justify-center">
              <div className="inline-flex items-center gap-2 text-sm text-slate-400">
                <div className="w-4 h-4 border-2 border-slate-300 dark:border-slate-600 border-t-blue-500 rounded-full animate-spin" />
                加载中...
              </div>
            </div>
          ) : tab === 'users' ? (
            /* Users Tab */
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm overflow-hidden">
              <div className="p-4 border-b border-slate-100 dark:border-slate-700 flex items-center gap-2">
                <Users className="w-5 h-5 text-slate-500 dark:text-slate-400" />
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white">用户列表</h2>
                <span className="ml-2 px-2 py-0.5 bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 text-xs rounded-full">
                  {users.length}
                </span>
              </div>

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
            </div>
          ) : (
            /* Groups Tab */
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Group List */}
              <div className="lg:col-span-1 bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-slate-500 dark:text-slate-400" />
                    <h2 className="text-lg font-semibold text-slate-900 dark:text-white">组</h2>
                  </div>
                  <button
                    onClick={() => setShowNewGroup(true)}
                    className="p-2 text-slate-400 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-all"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>

                {showNewGroup && (
                  <div className="p-4 border-b border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/50">
                    <input
                      type="text"
                      value={newGroupName}
                      onChange={(e) => setNewGroupName(e.target.value)}
                      placeholder="组名"
                      className="w-full px-3 py-2 mb-2 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg text-sm text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                    />
                    <input
                      type="text"
                      value={newGroupDesc}
                      onChange={(e) => setNewGroupDesc(e.target.value)}
                      placeholder="描述（可选）"
                      className="w-full px-3 py-2 mb-2 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg text-sm text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={handleCreateGroup}
                        disabled={!newGroupName.trim()}
                        className="flex-1 px-3 py-1.5 text-sm font-medium text-white bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors disabled:opacity-50"
                      >
                        创建
                      </button>
                      <button
                        onClick={() => {
                          setShowNewGroup(false)
                          setNewGroupName('')
                          setNewGroupDesc('')
                        }}
                        className="px-3 py-1.5 text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
                      >
                        取消
                      </button>
                    </div>
                  </div>
                )}

                <div className="divide-y divide-slate-100 dark:divide-slate-700 max-h-96 overflow-y-auto">
                  {groups.length === 0 ? (
                    <div className="p-4 text-center text-sm text-slate-400">暂无组</div>
                  ) : (
                    groups.map((g) => (
                      <div
                        key={g.id}
                        onClick={() => loadGroupMembers(g.id)}
                        className={`p-3 cursor-pointer transition-colors ${
                          selectedGroup === g.id
                            ? 'bg-blue-50 dark:bg-blue-900/30'
                            : 'hover:bg-slate-50 dark:hover:bg-slate-700/50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-sm font-medium text-slate-900 dark:text-white">{g.name}</div>
                            {g.description && (
                              <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{g.description}</div>
                            )}
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteGroup(g.id)
                            }}
                            className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-all"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Group Members */}
              <div className="lg:col-span-2 bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm overflow-hidden">
                {selectedGroup ? (
                  <>
                    <div className="p-4 border-b border-slate-100 dark:border-slate-700 flex items-center gap-2">
                      <UserCog className="w-5 h-5 text-slate-500 dark:text-slate-400" />
                      <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                        成员 - {groups.find((g) => g.id === selectedGroup)?.name}
                      </h2>
                      <span className="ml-2 px-2 py-0.5 bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 text-xs rounded-full">
                        {groupMembers.length}
                      </span>
                    </div>

                    <div className="divide-y divide-slate-100 dark:divide-slate-700 max-h-96 overflow-y-auto">
                      {groupMembers.length === 0 ? (
                        <div className="p-4 text-center text-sm text-slate-400">暂无成员</div>
                      ) : (
                        groupMembers.map((m) => (
                          <div
                            key={m.user_id}
                            className="p-3 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 bg-gradient-to-br from-slate-200 to-slate-300 dark:from-slate-600 dark:to-slate-700 rounded-full flex items-center justify-center">
                                <UserCog className="w-4 h-4 text-slate-500 dark:text-slate-400" />
                              </div>
                              <span className="text-sm font-medium text-slate-900 dark:text-white">{m.username}</span>
                            </div>
                            <button
                              onClick={() => handleRemoveMember(selectedGroup, m.user_id)}
                              className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-all"
                            >
                              <UserMinus className="w-4 h-4" />
                            </button>
                          </div>
                        ))
                      )}
                    </div>

                    {/* Add Members */}
                    {nonMembers.length > 0 && (
                      <div className="p-4 border-t border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/50">
                        <div className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2">添加成员</div>
                        <div className="flex flex-wrap gap-2">
                          {nonMembers.map((u) => (
                            <button
                              key={u.id}
                              onClick={() => handleAddMember(selectedGroup, u.id)}
                              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:border-blue-300 dark:hover:border-blue-700 transition-all"
                            >
                              <UserPlus className="w-3 h-3" />
                              {u.username}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="p-8 flex items-center justify-center text-sm text-slate-400">
                    选择一个组查看成员
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
