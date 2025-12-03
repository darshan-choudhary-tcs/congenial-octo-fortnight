'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { adminAPI } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/components/ui/use-toast'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Users, Shield, Activity, Loader2, UserPlus, Edit, Trash2, Home, Settings } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { useRouter } from 'next/navigation'

interface User {
  id: string
  username: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  created_at: string
  last_login?: string
}

interface Role {
  id: string
  name: string
  description: string
  permissions: string[]
}

interface SystemStats {
  total_users: number
  total_documents: number
  total_conversations: number
  total_messages: number
  total_agent_executions: number
  active_users_24h: number
  avg_confidence_score: number
}

interface LLMConfig {
  llm: {
    custom_base_url: string
    custom_model: string
    custom_api_key: string
    custom_embedding_model: string
    ollama_base_url: string
    ollama_model: string
    ollama_embedding_model: string
  }
  agent: {
    temperature: number
    max_iterations: number
    enable_memory: boolean
  }
  rag: {
    chunk_size: number
    chunk_overlap: number
    max_retrieval_docs: number
    similarity_threshold: number
  }
  explainability: {
    explainability_level: string
    enable_confidence_scoring: boolean
    enable_source_attribution: boolean
    enable_reasoning_chains: boolean
  }
  provider_status: {
    custom_available: boolean
    ollama_available: boolean
  }
}

export default function AdminPage() {
  const { user: currentUser } = useAuth()
  const { toast } = useToast()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [users, setUsers] = useState<User[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [llmConfig, setLLMConfig] = useState<LLMConfig | null>(null)
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'viewer',
  })

  useEffect(() => {
    // Check admin permission
    if (currentUser && !currentUser.roles.includes('admin')) {
      toast({
        title: 'Access Denied',
        description: 'You do not have permission to access this page',
        variant: 'destructive',
      })
      router.push('/dashboard')
      return
    }
    if (currentUser) {
      loadData()
    }
  }, [currentUser])

  const loadData = async () => {
    try {
      setLoading(true)
      const [usersRes, rolesRes, statsRes, configRes] = await Promise.all([
        adminAPI.getUsers(),
        adminAPI.getRoles(),
        adminAPI.getSystemStats(),
        adminAPI.getLLMConfig(),
      ])
      setUsers(usersRes.data)
      setRoles(rolesRes.data)
      setStats(statsRes.data)
      setLLMConfig(configRes.data)
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to load admin data',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCreateUser = async () => {
    try {
      await adminAPI.createUser(formData)
      toast({
        title: 'Success',
        description: 'User created successfully',
      })
      setShowCreateUser(false)
      setFormData({ username: '', email: '', password: '', full_name: '', role: 'viewer' })
      await loadData()
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create user',
        variant: 'destructive',
      })
    }
  }

  const handleUpdateUser = async () => {
    if (!editingUser) return
    try {
      await adminAPI.updateUser(editingUser.id, {
        email: editingUser.email,
        full_name: editingUser.full_name,
        role: editingUser.role,
        is_active: editingUser.is_active,
      })
      toast({
        title: 'Success',
        description: 'User updated successfully',
      })
      setEditingUser(null)
      await loadData()
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update user',
        variant: 'destructive',
      })
    }
  }

  const handleDeleteUser = async (userId: string, username: string) => {
    if (!confirm(`Are you sure you want to delete user "${username}"?`)) return
    try {
      await adminAPI.deleteUser(userId)
      toast({
        title: 'Success',
        description: 'User deleted successfully',
      })
      await loadData()
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete user',
        variant: 'destructive',
      })
    }
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'analyst':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'viewer':
        return 'bg-gray-100 text-gray-800 border-gray-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <div className="bg-white dark:bg-gray-950 border-b shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard')}>
              <Home className="h-4 w-4 mr-2" />
              Dashboard
            </Button>
            <div className="flex items-center gap-2">
              <Settings className="h-6 w-6 text-primary" />
              <h1 className="text-2xl font-bold">Admin Panel</h1>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Badge variant="destructive" className="px-3 py-1">
              <Shield className="h-3 w-3 mr-1" />
              Administrator
            </Badge>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* System Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Users</CardDescription>
              <CardTitle className="text-3xl flex items-center gap-2">
                <Users className="h-6 w-6 text-blue-600" />
                {stats?.total_users || 0}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Active (24h)</CardDescription>
              <CardTitle className="text-3xl flex items-center gap-2">
                <Activity className="h-6 w-6 text-green-600" />
                {stats?.active_users_24h || 0}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Conversations</CardDescription>
              <CardTitle className="text-3xl">{stats?.total_conversations || 0}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Agent Executions</CardDescription>
              <CardTitle className="text-3xl">{stats?.total_agent_executions || 0}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="users" className="space-y-6">
          <TabsList>
            <TabsTrigger value="users">User Management</TabsTrigger>
            <TabsTrigger value="roles">Roles & Permissions</TabsTrigger>
            <TabsTrigger value="stats">System Statistics</TabsTrigger>
            <TabsTrigger value="llm-config">LLM Configuration</TabsTrigger>
          </TabsList>

          {/* User Management Tab */}
          <TabsContent value="users">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>User Management</CardTitle>
                    <CardDescription>Manage user accounts and permissions</CardDescription>
                  </div>
                  <Button onClick={() => setShowCreateUser(!showCreateUser)}>
                    <UserPlus className="h-4 w-4 mr-2" />
                    Create User
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {/* Create User Form */}
                {showCreateUser && (
                  <div className="mb-6 p-4 border rounded-lg bg-muted/50">
                    <h3 className="font-semibold mb-4">Create New User</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="username">Username</Label>
                        <Input
                          id="username"
                          value={formData.username}
                          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                          placeholder="johndoe"
                        />
                      </div>
                      <div>
                        <Label htmlFor="email">Email</Label>
                        <Input
                          id="email"
                          type="email"
                          value={formData.email}
                          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                          placeholder="john@example.com"
                        />
                      </div>
                      <div>
                        <Label htmlFor="password">Password</Label>
                        <Input
                          id="password"
                          type="password"
                          value={formData.password}
                          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                          placeholder="••••••••"
                        />
                      </div>
                      <div>
                        <Label htmlFor="full_name">Full Name</Label>
                        <Input
                          id="full_name"
                          value={formData.full_name}
                          onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                          placeholder="John Doe"
                        />
                      </div>
                      <div>
                        <Label htmlFor="role">Role</Label>
                        <Select value={formData.role} onValueChange={(value) => setFormData({ ...formData, role: value })}>
                          <SelectTrigger id="role">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {roles.map((role) => (
                              <SelectItem key={role.id} value={role.name}>
                                {role.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="flex gap-2 mt-4">
                      <Button onClick={handleCreateUser}>Create User</Button>
                      <Button variant="outline" onClick={() => setShowCreateUser(false)}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}

                {/* User List */}
                <ScrollArea className="h-[500px]">
                  <div className="space-y-2">
                    {users.map((user) => (
                      <div
                        key={user.id}
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors bg-card"
                      >
                        {editingUser?.id === user.id ? (
                          <div className="flex-1 grid grid-cols-4 gap-4 items-center">
                            <Input
                              value={editingUser.email}
                              onChange={(e) => setEditingUser({ ...editingUser, email: e.target.value })}
                            />
                            <Input
                              value={editingUser.full_name}
                              onChange={(e) => setEditingUser({ ...editingUser, full_name: e.target.value })}
                            />
                            <Select
                              value={editingUser.role}
                              onValueChange={(value) => setEditingUser({ ...editingUser, role: value })}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {roles.map((role) => (
                                  <SelectItem key={role.id} value={role.name}>
                                    {role.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <div className="flex gap-2">
                              <Button size="sm" onClick={handleUpdateUser}>
                                Save
                              </Button>
                              <Button size="sm" variant="outline" onClick={() => setEditingUser(null)}>
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <>
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <h3 className="font-semibold">{user.username}</h3>
                                <Badge className={getRoleBadgeColor(user.role)}>{user.role}</Badge>
                                {!user.is_active && <Badge variant="destructive">Inactive</Badge>}
                              </div>
                              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                <span>{user.email}</span>
                                <span>•</span>
                                <span>{user.full_name}</span>
                                <span>•</span>
                                <span>Joined {formatDate(user.created_at)}</span>
                                {user.last_login && (
                                  <>
                                    <span>•</span>
                                    <span>Last login {formatDate(user.last_login)}</span>
                                  </>
                                )}
                              </div>
                            </div>
                            <div className="flex gap-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => router.push(`/dashboard/admin/users/${user.id}`)}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteUser(user.id, user.username)}
                                disabled={user.username === currentUser?.username}
                              >
                                <Trash2 className="h-4 w-4 text-destructive" />
                              </Button>
                            </div>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Roles & Permissions Tab */}
          <TabsContent value="roles">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {roles.map((role) => (
                <Card key={role.id}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="h-5 w-5" />
                      {role.name}
                    </CardTitle>
                    <CardDescription>{role.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <p className="text-sm font-semibold mb-2">Permissions:</p>
                      <div className="space-y-1">
                        {role.permissions.map((permission) => (
                          <div key={permission} className="flex items-center gap-2 text-sm">
                            <div className="w-2 h-2 rounded-full bg-green-600" />
                            <span>{permission}</span>
                          </div>
                        ))}
                      </div>
                      <div className="mt-4 pt-4 border-t">
                        <p className="text-sm text-muted-foreground">
                          {users.filter((u) => u.role === role.name).length} users with this role
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* System Statistics Tab */}
          <TabsContent value="stats">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>System Overview</CardTitle>
                  <CardDescription>Key metrics and statistics</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-sm font-medium">Total Users</span>
                      <span className="text-2xl font-bold">{stats?.total_users || 0}</span>
                    </div>
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-sm font-medium">Total Documents</span>
                      <span className="text-2xl font-bold">{stats?.total_documents || 0}</span>
                    </div>
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-sm font-medium">Total Conversations</span>
                      <span className="text-2xl font-bold">{stats?.total_conversations || 0}</span>
                    </div>
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-sm font-medium">Total Messages</span>
                      <span className="text-2xl font-bold">{stats?.total_messages || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Agent Executions</span>
                      <span className="text-2xl font-bold">{stats?.total_agent_executions || 0}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Performance Metrics</CardTitle>
                  <CardDescription>System performance indicators</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium">Average Confidence Score</span>
                        <span className="text-sm font-bold">
                          {stats?.avg_confidence_score
                            ? `${(stats.avg_confidence_score * 100).toFixed(1)}%`
                            : 'N/A'}
                        </span>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-green-600"
                          style={{
                            width: `${(stats?.avg_confidence_score || 0) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium">Active Users (24h)</span>
                        <span className="text-sm font-bold">
                          {stats?.active_users_24h || 0} / {stats?.total_users || 0}
                        </span>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-600"
                          style={{
                            width: `${((stats?.active_users_24h || 0) / (stats?.total_users || 1)) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium">Avg Messages per Conversation</span>
                        <span className="text-sm font-bold">
                          {stats?.total_conversations
                            ? (stats.total_messages / stats.total_conversations).toFixed(1)
                            : 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* LLM Configuration Tab */}
          <TabsContent value="llm-config">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* LLM Settings */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="h-5 w-5" />
                    LLM Settings
                  </CardTitle>
                  <CardDescription>Language Model configurations</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-semibold text-sm mb-3 text-blue-600">Custom LLM (GenAI Lab)</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between items-start pb-2 border-b">
                          <span className="text-muted-foreground">Base URL:</span>
                          <span className="font-mono text-xs break-all text-right max-w-[60%]">
                            {llmConfig?.llm.custom_base_url || 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between items-center pb-2 border-b">
                          <span className="text-muted-foreground">Model:</span>
                          <span className="font-mono text-xs">{llmConfig?.llm.custom_model || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between items-center pb-2 border-b">
                          <span className="text-muted-foreground">API Key:</span>
                          <span className="font-mono text-xs">{llmConfig?.llm.custom_api_key || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between items-center pb-2 border-b">
                          <span className="text-muted-foreground">Embedding Model:</span>
                          <span className="font-mono text-xs">{llmConfig?.llm.custom_embedding_model || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between items-center pt-1">
                          <span className="text-muted-foreground">Status:</span>
                          <Badge variant={llmConfig?.provider_status.custom_available ? 'default' : 'destructive'}>
                            {llmConfig?.provider_status.custom_available ? '✓ Available' : '✗ Unavailable'}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    <div className="pt-4">
                      <h4 className="font-semibold text-sm mb-3 text-purple-600">Ollama (Local)</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between items-center pb-2 border-b">
                          <span className="text-muted-foreground">Base URL:</span>
                          <span className="font-mono text-xs">{llmConfig?.llm.ollama_base_url || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between items-center pb-2 border-b">
                          <span className="text-muted-foreground">Model:</span>
                          <span className="font-mono text-xs">{llmConfig?.llm.ollama_model || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between items-center pb-2 border-b">
                          <span className="text-muted-foreground">Embedding Model:</span>
                          <span className="font-mono text-xs">{llmConfig?.llm.ollama_embedding_model || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between items-center pt-1">
                          <span className="text-muted-foreground">Status:</span>
                          <Badge variant={llmConfig?.provider_status.ollama_available ? 'default' : 'destructive'}>
                            {llmConfig?.provider_status.ollama_available ? '✓ Available' : '✗ Unavailable'}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Agent Settings */}
              <Card>
                <CardHeader>
                  <CardTitle>Agent Settings</CardTitle>
                  <CardDescription>Agent behavior configurations</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between items-center pb-2 border-b">
                      <span className="text-muted-foreground">Temperature:</span>
                      <span className="font-mono font-semibold">{llmConfig?.agent.temperature || 0}</span>
                    </div>
                    <div className="flex justify-between items-center pb-2 border-b">
                      <span className="text-muted-foreground">Max Iterations:</span>
                      <span className="font-mono font-semibold">{llmConfig?.agent.max_iterations || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Enable Memory:</span>
                      <Badge variant={llmConfig?.agent.enable_memory ? 'default' : 'secondary'}>
                        {llmConfig?.agent.enable_memory ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* RAG Settings */}
              <Card>
                <CardHeader>
                  <CardTitle>RAG Settings</CardTitle>
                  <CardDescription>Retrieval-Augmented Generation configurations</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between items-center pb-2 border-b">
                      <span className="text-muted-foreground">Chunk Size:</span>
                      <span className="font-mono font-semibold">{llmConfig?.rag.chunk_size || 0}</span>
                    </div>
                    <div className="flex justify-between items-center pb-2 border-b">
                      <span className="text-muted-foreground">Chunk Overlap:</span>
                      <span className="font-mono font-semibold">{llmConfig?.rag.chunk_overlap || 0}</span>
                    </div>
                    <div className="flex justify-between items-center pb-2 border-b">
                      <span className="text-muted-foreground">Max Retrieval Docs:</span>
                      <span className="font-mono font-semibold">{llmConfig?.rag.max_retrieval_docs || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Similarity Threshold:</span>
                      <span className="font-mono font-semibold">{llmConfig?.rag.similarity_threshold || 0}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Explainability Settings */}
              <Card>
                <CardHeader>
                  <CardTitle>Explainability Settings</CardTitle>
                  <CardDescription>Transparency and explainability features</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between items-center pb-2 border-b">
                      <span className="text-muted-foreground">Explainability Level:</span>
                      <Badge variant="outline">{llmConfig?.explainability.explainability_level || 'N/A'}</Badge>
                    </div>
                    <div className="flex justify-between items-center pb-2 border-b">
                      <span className="text-muted-foreground">Confidence Scoring:</span>
                      <Badge variant={llmConfig?.explainability.enable_confidence_scoring ? 'default' : 'secondary'}>
                        {llmConfig?.explainability.enable_confidence_scoring ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center pb-2 border-b">
                      <span className="text-muted-foreground">Source Attribution:</span>
                      <Badge variant={llmConfig?.explainability.enable_source_attribution ? 'default' : 'secondary'}>
                        {llmConfig?.explainability.enable_source_attribution ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Reasoning Chains:</span>
                      <Badge variant={llmConfig?.explainability.enable_reasoning_chains ? 'default' : 'secondary'}>
                        {llmConfig?.explainability.enable_reasoning_chains ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
