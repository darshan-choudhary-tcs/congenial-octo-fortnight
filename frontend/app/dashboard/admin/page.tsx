'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { adminAPI, authAPI, promptsAPI } from '@/lib/api'
import { ThemeToggle } from '@/components/ThemeToggle'
import { useSnackbar } from '@/components/SnackbarProvider'
import { formatDate } from '@/lib/utils'
import { useRouter } from 'next/navigation'
import {
  Box,
  Container,
  Paper,
  Card,
  CardContent,
  Button,
  IconButton,
  TextField,
  Typography,
  Chip,
  Divider,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  CircularProgress,
  Menu,
} from '@mui/material'
import {
  People as UsersIcon,
  Shield as ShieldIcon,
  TrendingUp as ActivityIcon,
  PersonAdd as UserPlusIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Home as HomeIcon,
  Settings as SettingsIcon,
  TrendingUp as TrendingUpIcon,
  AttachMoney as DollarSignIcon,
  FlashOn as ZapIcon,
  Key as KeyIcon,
  Logout as LogOutIcon,
  ArrowBack as ArrowBackIcon,
  Code as CodeIcon,
  Description as DescriptionIcon,
  Category as CategoryIcon,
  Info as InfoIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material'

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
  token_usage?: {
    total_tokens: number
    total_cost: number
    tokens_last_30_days: number
    tokens_last_7_days: number
    cost_last_30_days: number
    provider_breakdown: {
      [key: string]: {
        tokens: number
        requests: number
      }
    }
    currency: string
  }
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
  vision: {
    custom_vision_model: string
    custom_vision_base_url: string
    custom_vision_timeout: number
    ollama_vision_model: string
    ollama_vision_base_url: string
    ollama_vision_timeout: number
  }
  ocr: {
    supported_formats: string[]
    max_file_size: number
    max_file_size_mb: number
    image_max_dimension: number
    confidence_threshold: number
    enable_preprocessing: boolean
    pdf_dpi: number
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
    custom_vision_available: boolean
    ollama_vision_available: boolean
  }
}

interface Prompt {
  name: string
  category: string
  description: string
  template: string
  variables: string[]
  version: string
  output_format: string
  purpose: string
  examples: string[]
  is_custom: boolean
  usage_count: number
  created_at: string
}

interface PromptStats {
  total_prompts: number
  custom_prompts: number
  built_in_prompts: number
  total_usage: number
  most_used: Array<{
    name: string
    usage_count: number
    category: string
  }>
  by_category: Record<string, number>
}

export default function AdminPage() {
  const { user: currentUser, logout } = useAuth()
  const { showSnackbar } = useSnackbar()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [users, setUsers] = useState<User[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [llmConfig, setLLMConfig] = useState<LLMConfig | null>(null)
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [activeTab, setActiveTab] = useState(0)
  const [showPasswordReset, setShowPasswordReset] = useState(false)
  const [resetPasswordUserId, setResetPasswordUserId] = useState<string | null>(null)
  const [resetPasswordUsername, setResetPasswordUsername] = useState<string>('')
  const [newPassword, setNewPassword] = useState('')
  const [settingsAnchor, setSettingsAnchor] = useState<null | HTMLElement>(null)
  const [showPasswordDialog, setShowPasswordDialog] = useState(false)
  const [oldPassword, setOldPassword] = useState('')
  const [newPasswordSelf, setNewPasswordSelf] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'viewer',
  })

  // Prompt Library states
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [promptStats, setPromptStats] = useState<PromptStats | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null)
  const [showPromptDetails, setShowPromptDetails] = useState(false)

  useEffect(() => {
    // Check admin or super_admin permission
    if (currentUser && !currentUser.roles.includes('admin') && !currentUser.roles.includes('super_admin')) {
      showSnackbar('You do not have permission to access this page', 'error')
      router.push('/dashboard')
      return
    }
    if (currentUser) {
      loadData()
    }
  }, [currentUser])

  useEffect(() => {
    if (currentUser?.roles.includes('super_admin') && activeTab === 4) {
      loadPromptsData()
    }
  }, [selectedCategory, activeTab, currentUser])

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

      // Filter roles based on user role
      let filteredRoles = rolesRes.data
      if (currentUser?.roles.includes('admin') && !currentUser?.roles.includes('super_admin')) {
        // Admin users should only see admin and authenticated_user roles
        filteredRoles = rolesRes.data.filter((role: Role) =>
          role.name === 'admin' || role.name === 'authenticated_user'
        )
      }
      // Super admin sees all roles (no filtering needed)

      setRoles(filteredRoles)
      setStats(statsRes.data)
      setLLMConfig(configRes.data)
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to load admin data', 'error')
    } finally {
      setLoading(false)
    }
  }

  const loadPromptsData = async () => {
    try {
      const category = selectedCategory === 'all' ? undefined : selectedCategory
      const [promptsRes, statsRes] = await Promise.all([
        promptsAPI.listPrompts(category ? { category } : undefined),
        promptsAPI.getStats(),
      ])
      setPrompts(promptsRes.data.prompts)
      setPromptStats(statsRes.data)
    } catch (error: any) {
      console.error('Error loading prompts:', error)
      showSnackbar(error.response?.data?.detail || 'Failed to load prompts', 'error')
    }
  }

  const handleCreateUser = async () => {
    try {
      await adminAPI.createUser(formData)
      showSnackbar('User created successfully', 'success')
      setShowCreateUser(false)
      setFormData({ username: '', email: '', password: '', full_name: '', role: 'viewer' })
      await loadData()
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to create user', 'error')
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
      showSnackbar('User updated successfully', 'success')
      setEditingUser(null)
      await loadData()
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to update user', 'error')
    }
  }

  const handleDeleteUser = async (userId: string, username: string) => {
    if (!confirm(`Are you sure you want to delete user "${username}"?`)) return
    try {
      await adminAPI.deleteUser(userId)
      showSnackbar('User deleted successfully', 'success')
      await loadData()
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to delete user', 'error')
    }
  }

  const handleOpenPasswordReset = (userId: string, username: string) => {
    setResetPasswordUserId(userId)
    setResetPasswordUsername(username)
    setNewPassword('')
    setShowPasswordReset(true)
  }

  const handleResetPassword = async () => {
    if (!resetPasswordUserId || !newPassword) {
      showSnackbar('Please enter a new password', 'warning')
      return
    }

    if (newPassword.length < 6) {
      showSnackbar('Password must be at least 6 characters', 'warning')
      return
    }

    try {
      await adminAPI.resetUserPassword(resetPasswordUserId, newPassword)
      showSnackbar(`Password successfully reset for ${resetPasswordUsername}`, 'success')
      setShowPasswordReset(false)
      setResetPasswordUserId(null)
      setResetPasswordUsername('')
      setNewPassword('')
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to reset password', 'error')
    }
  }

  const handleChangePassword = async () => {
    if (!oldPassword || !newPasswordSelf || !confirmPassword) {
      showSnackbar('Please fill in all fields', 'warning')
      return
    }

    if (newPasswordSelf.length < 6) {
      showSnackbar('New password must be at least 6 characters', 'warning')
      return
    }

    if (newPasswordSelf !== confirmPassword) {
      showSnackbar('New passwords do not match', 'warning')
      return
    }

    try {
      await authAPI.changePassword(oldPassword, newPasswordSelf)
      showSnackbar('Password changed successfully', 'success')
      setShowPasswordDialog(false)
      setOldPassword('')
      setNewPasswordSelf('')
      setConfirmPassword('')
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to change password', 'error')
    }
  }

  const getRoleBadgeColor = (role: string): 'error' | 'primary' | 'secondary' | 'success' | 'default' => {
    switch (role) {
      case 'super_admin':
        return 'error'
      case 'admin':
        return 'secondary'
      case 'authenticated_user':
        return 'primary'
      case 'analyst':
        return 'success'
      case 'viewer':
        return 'default'
      default:
        return 'default'
    }
  }

  if (loading) {
    return (
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress size={48} />
      </Box>
    )
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper sx={{ borderRadius: 0, borderBottom: 1, borderColor: 'divider' }} elevation={1}>
        <Container maxWidth="xl">
          <Box sx={{ py: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <IconButton
                onClick={() => router.push('/dashboard')}
                size="small"
                sx={{ mr: 1 }}
              >
                <ArrowBackIcon />
              </IconButton>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SettingsIcon color="primary" />
                <Typography variant="h5" fontWeight="bold">
                  Admin Panel
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ textAlign: 'right' }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {currentUser?.full_name || currentUser?.username}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'capitalize' }}>
                  {currentUser?.roles.join(', ')}
                </Typography>
              </Box>
              <ThemeToggle />
              <IconButton
                size="small"
                onClick={(e) => setSettingsAnchor(e.currentTarget)}
              >
                <SettingsIcon />
              </IconButton>
              <Button
                variant="outlined"
                size="small"
                startIcon={<LogOutIcon />}
                onClick={logout}
              >
                Logout
              </Button>
            </Box>
          </Box>
        </Container>
      </Paper>

      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* System Stats */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" variant="body2" gutterBottom>
                  Total Users
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <UsersIcon sx={{ color: 'primary.main', fontSize: 32 }} />
                  <Typography variant="h3" fontWeight="bold">
                    {stats?.total_users || 0}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" variant="body2" gutterBottom>
                  Active (24h)
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ActivityIcon sx={{ color: 'success.main', fontSize: 32 }} />
                  <Typography variant="h3" fontWeight="bold">
                    {stats?.active_users_24h || 0}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" variant="body2" gutterBottom>
                  Total Conversations
                </Typography>
                <Typography variant="h3" fontWeight="bold">
                  {stats?.total_conversations || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" variant="body2" gutterBottom>
                  Agent Executions
                </Typography>
                <Typography variant="h3" fontWeight="bold">
                  {stats?.total_agent_executions || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Token Usage Stats */}
        {stats?.token_usage && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={3}>
              <Card sx={{ background: 'linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%)' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    Total Tokens
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ZapIcon sx={{ color: '#9333ea', fontSize: 32 }} />
                    <Typography variant="h3" fontWeight="bold">
                      {stats.token_usage.total_tokens.toLocaleString()}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card sx={{ background: 'linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%)' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    Total Cost
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <DollarSignIcon sx={{ color: '#16a34a', fontSize: 32 }} />
                    <Typography variant="h3" fontWeight="bold">
                      ${stats.token_usage.total_cost.toFixed(4)}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card sx={{ background: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    Last 30 Days
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TrendingUpIcon sx={{ color: '#2563eb', fontSize: 32 }} />
                    <Typography variant="h3" fontWeight="bold">
                      {stats.token_usage.tokens_last_30_days.toLocaleString()}
                    </Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    ${stats.token_usage.cost_last_30_days.toFixed(4)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card sx={{ background: 'linear-gradient(135deg, #fed7aa 0%, #fdba74 100%)' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    Last 7 Days
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ActivityIcon sx={{ color: '#ea580c', fontSize: 32 }} />
                    <Typography variant="h3" fontWeight="bold">
                      {stats.token_usage.tokens_last_7_days.toLocaleString()}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        <Paper sx={{ mb: 4 }}>
          <Tabs
            value={activeTab}
            onChange={(e, newValue) => setActiveTab(newValue)}
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab label="User Management" />
            <Tab label="Roles & Permissions" />
            <Tab label="System Statistics" />
            <Tab label="LLM Configuration" />
            {currentUser?.roles.includes('super_admin') && (
              <Tab label="Prompt Library" />
            )}
          </Tabs>
        </Paper>

          {/* User Management Tab */}
          {activeTab === 0 && (
            <Paper>
              <Box sx={{ p: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: 1, borderColor: 'divider' }}>
                <Box>
                  <Typography variant="h6" fontWeight="bold">User Management</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Manage user accounts and permissions
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  {currentUser?.roles.includes('super_admin') && (
                    <Button
                      variant="contained"
                      color="secondary"
                      startIcon={<ShieldIcon />}
                      onClick={() => router.push('/dashboard/admin/onboard')}
                    >
                      Onboard Admin
                    </Button>
                  )}
                  <Button
                    variant="contained"
                    startIcon={<UserPlusIcon />}
                    onClick={() => setShowCreateUser(!showCreateUser)}
                  >
                    Create User
                  </Button>
                </Box>
              </Box>
              <Box sx={{ p: 3 }}>
                {/* Create User Form */}
                {showCreateUser && (
                  <Paper sx={{ p: 3, mb: 3, bgcolor: 'action.hover' }}>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      Create New User
                    </Typography>
                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Username"
                          value={formData.username}
                          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                          placeholder="johndoe"
                        />
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Email"
                          type="email"
                          value={formData.email}
                          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                          placeholder="john@example.com"
                        />
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Password"
                          type="password"
                          value={formData.password}
                          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                          placeholder="••••••••"
                        />
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Full Name"
                          value={formData.full_name}
                          onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                          placeholder="John Doe"
                        />
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <FormControl fullWidth>
                          <InputLabel>Role</InputLabel>
                          <Select
                            value={formData.role}
                            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                            label="Role"
                          >
                            {roles.map((role) => (
                              <MenuItem key={role.id} value={role.name}>
                                {role.name}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Grid>
                    </Grid>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button variant="contained" onClick={handleCreateUser}>
                        Create User
                      </Button>
                      <Button variant="outlined" onClick={() => setShowCreateUser(false)}>
                        Cancel
                      </Button>
                    </Box>
                  </Paper>
                )}

                {/* User List */}
                <TableContainer sx={{ maxHeight: 600 }}>
                  <Table stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Username</TableCell>
                        <TableCell>Email</TableCell>
                        <TableCell>Full Name</TableCell>
                        <TableCell>Role</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Joined</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {users.map((user) => (
                        <TableRow key={user.id} hover>
                          <TableCell>
                            <Typography fontWeight="bold">{user.username}</Typography>
                          </TableCell>
                          <TableCell>{user.email}</TableCell>
                          <TableCell>{user.full_name}</TableCell>
                          <TableCell>
                            <Chip
                              label={user.role}
                              color={getRoleBadgeColor(user.role)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            {user.is_active ? (
                              <Chip label="Active" color="success" size="small" />
                            ) : (
                              <Chip label="Inactive" color="error" size="small" />
                            )}
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {formatDate(user.created_at)}
                            </Typography>
                            {user.last_login && (
                              <Typography variant="caption" color="text.secondary">
                                Last: {formatDate(user.last_login)}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell align="right">
                            <IconButton
                              size="small"
                              onClick={() => router.push(`/dashboard/admin/users/${user.id}`)}
                              color="primary"
                              title="Edit User"
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              size="small"
                              onClick={() => handleOpenPasswordReset(user.id, user.username)}
                              color="warning"
                              title="Reset Password"
                            >
                              <KeyIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              size="small"
                              onClick={() => handleDeleteUser(user.id, user.username)}
                              disabled={user.username === currentUser?.username}
                              color="error"
                              title="Delete User"
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            </Paper>
          )}

          {/* Roles & Permissions Tab */}
          {activeTab === 1 && (
            <Grid container spacing={3}>
              {roles.map((role) => (
                <Grid item xs={12} md={4} key={role.id}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <ShieldIcon />
                        <Typography variant="h6" fontWeight="bold">
                          {role.name}
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {role.description}
                      </Typography>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="body2" fontWeight="bold" gutterBottom>
                        Permissions:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                        {role.permissions.map((permission) => (
                          <Chip
                            key={permission}
                            label={permission}
                            size="small"
                            color="success"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="body2" color="text.secondary">
                        {users.filter((u) => u.role === role.name).length} users with this role
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}

          {/* System Statistics Tab */}
          {activeTab === 2 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      System Overview
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Key metrics and statistics
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" fontWeight="medium">Total Users</Typography>
                        <Typography variant="h5" fontWeight="bold">{stats?.total_users || 0}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" fontWeight="medium">Total Documents</Typography>
                        <Typography variant="h5" fontWeight="bold">{stats?.total_documents || 0}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" fontWeight="medium">Total Conversations</Typography>
                        <Typography variant="h5" fontWeight="bold">{stats?.total_conversations || 0}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" fontWeight="medium">Total Messages</Typography>
                        <Typography variant="h5" fontWeight="bold">{stats?.total_messages || 0}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" fontWeight="medium">Agent Executions</Typography>
                        <Typography variant="h5" fontWeight="bold">{stats?.total_agent_executions || 0}</Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      Token Usage
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      LLM token consumption and costs
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    {stats?.token_usage ? (
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" fontWeight="medium">Total Tokens</Typography>
                          <Typography variant="h5" fontWeight="bold">{stats.token_usage.total_tokens.toLocaleString()}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" fontWeight="medium">Total Cost</Typography>
                          <Typography variant="h5" fontWeight="bold" color="success.main">
                            ${stats.token_usage.total_cost.toFixed(4)}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" fontWeight="medium">Last 30 Days</Typography>
                          <Box sx={{ textAlign: 'right' }}>
                            <Typography variant="h5" fontWeight="bold">
                              {stats.token_usage.tokens_last_30_days.toLocaleString()}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              ${stats.token_usage.cost_last_30_days.toFixed(4)}
                            </Typography>
                          </Box>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" fontWeight="medium">Last 7 Days</Typography>
                          <Typography variant="h5" fontWeight="bold">
                            {stats.token_usage.tokens_last_7_days.toLocaleString()}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="body2" fontWeight="medium" sx={{ mb: 1 }}>
                            Provider Breakdown
                          </Typography>
                          {Object.entries(stats.token_usage.provider_breakdown).map(([provider, data]) => (
                            <Box key={provider} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1 }}>
                              <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                                {provider}
                              </Typography>
                              <Box sx={{ textAlign: 'right' }}>
                                <Typography variant="body2" fontWeight="bold">
                                  {data.tokens.toLocaleString()}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {data.requests} requests
                                </Typography>
                              </Box>
                            </Box>
                          ))}
                        </Box>
                      </Box>
                    ) : (
                      <Box sx={{ textAlign: 'center', py: 4 }}>
                        <Typography color="text.secondary">
                          No token usage data available
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      Performance Metrics
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      System performance indicators
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                      <Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" fontWeight="medium">Average Confidence Score</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {stats?.avg_confidence_score
                              ? `${(stats.avg_confidence_score * 100).toFixed(1)}%`
                              : 'N/A'}
                          </Typography>
                        </Box>
                        <Box sx={{ height: 8, bgcolor: 'action.hover', borderRadius: 1, overflow: 'hidden' }}>
                          <Box
                            sx={{
                              height: '100%',
                              bgcolor: 'success.main',
                              width: `${(stats?.avg_confidence_score || 0) * 100}%`,
                            }}
                          />
                        </Box>
                      </Box>
                      <Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" fontWeight="medium">Active Users (24h)</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {stats?.active_users_24h || 0} / {stats?.total_users || 0}
                          </Typography>
                        </Box>
                        <Box sx={{ height: 8, bgcolor: 'action.hover', borderRadius: 1, overflow: 'hidden' }}>
                          <Box
                            sx={{
                              height: '100%',
                              bgcolor: 'primary.main',
                              width: `${((stats?.active_users_24h || 0) / (stats?.total_users || 1)) * 100}%`,
                            }}
                          />
                        </Box>
                      </Box>
                      <Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" fontWeight="medium">Avg Messages per Conversation</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {stats?.total_conversations
                              ? (stats.total_messages / stats.total_conversations).toFixed(1)
                              : 'N/A'}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* LLM Configuration Tab */}
          {activeTab === 3 && (
            <Grid container spacing={3}>
              {/* LLM Settings */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <SettingsIcon />
                      <Typography variant="h6" fontWeight="bold">
                        LLM Settings
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Language Model configurations
                    </Typography>
                    <Divider sx={{ mb: 2 }} />

                    {/* Custom LLM */}
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="body2" fontWeight="bold" color="primary.main" gutterBottom>
                        Custom LLM (GenAI Lab)
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" color="text.secondary">Base URL:</Typography>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace', maxWidth: '60%', textAlign: 'right', wordBreak: 'break-all' }}>
                            {llmConfig?.llm.custom_base_url || 'N/A'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" color="text.secondary">Model:</Typography>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                            {llmConfig?.llm.custom_model || 'N/A'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" color="text.secondary">API Key:</Typography>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                            {llmConfig?.llm.custom_api_key || 'N/A'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" color="text.secondary">Embedding Model:</Typography>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                            {llmConfig?.llm.custom_embedding_model || 'N/A'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', pt: 1 }}>
                          <Typography variant="body2" color="text.secondary">Status:</Typography>
                          <Chip
                            label={llmConfig?.provider_status.custom_available ? '✓ Available' : '✗ Unavailable'}
                            color={llmConfig?.provider_status.custom_available ? 'success' : 'error'}
                            size="small"
                          />
                        </Box>
                      </Box>
                    </Box>

                    {/* Ollama */}
                    <Box>
                      <Typography variant="body2" fontWeight="bold" sx={{ color: '#9333ea' }} gutterBottom>
                        Ollama (Local)
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" color="text.secondary">Base URL:</Typography>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                            {llmConfig?.llm.ollama_base_url || 'N/A'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" color="text.secondary">Model:</Typography>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                            {llmConfig?.llm.ollama_model || 'N/A'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" color="text.secondary">Embedding Model:</Typography>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                            {llmConfig?.llm.ollama_embedding_model || 'N/A'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', pt: 1 }}>
                          <Typography variant="body2" color="text.secondary">Status:</Typography>
                          <Chip
                            label={llmConfig?.provider_status.ollama_available ? '✓ Available' : '✗ Unavailable'}
                            color={llmConfig?.provider_status.ollama_available ? 'success' : 'error'}
                            size="small"
                          />
                        </Box>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Agent Settings */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      Agent Settings
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Agent behavior configurations
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" color="text.secondary">Temperature:</Typography>
                        <Typography variant="body2" fontWeight="bold" sx={{ fontFamily: 'monospace' }}>
                          {llmConfig?.agent.temperature || 0}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" color="text.secondary">Max Iterations:</Typography>
                        <Typography variant="body2" fontWeight="bold" sx={{ fontFamily: 'monospace' }}>
                          {llmConfig?.agent.max_iterations || 0}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">Enable Memory:</Typography>
                        <Chip
                          label={llmConfig?.agent.enable_memory ? 'Enabled' : 'Disabled'}
                          color={llmConfig?.agent.enable_memory ? 'success' : 'default'}
                          size="small"
                        />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* RAG Settings */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      RAG Settings
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Retrieval-Augmented Generation configurations
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" color="text.secondary">Chunk Size:</Typography>
                        <Typography variant="body2" fontWeight="bold" sx={{ fontFamily: 'monospace' }}>
                          {llmConfig?.rag.chunk_size || 0}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" color="text.secondary">Chunk Overlap:</Typography>
                        <Typography variant="body2" fontWeight="bold" sx={{ fontFamily: 'monospace' }}>
                          {llmConfig?.rag.chunk_overlap || 0}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" color="text.secondary">Max Retrieval Docs:</Typography>
                        <Typography variant="body2" fontWeight="bold" sx={{ fontFamily: 'monospace' }}>
                          {llmConfig?.rag.max_retrieval_docs || 0}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">Similarity Threshold:</Typography>
                        <Typography variant="body2" fontWeight="bold" sx={{ fontFamily: 'monospace' }}>
                          {llmConfig?.rag.similarity_threshold || 0}
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Explainability Settings */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      Explainability Settings
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Transparency and explainability features
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" color="text.secondary">Explainability Level:</Typography>
                        <Chip
                          label={llmConfig?.explainability.explainability_level || 'N/A'}
                          variant="outlined"
                          size="small"
                        />
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" color="text.secondary">Confidence Scoring:</Typography>
                        <Chip
                          label={llmConfig?.explainability.enable_confidence_scoring ? 'Enabled' : 'Disabled'}
                          color={llmConfig?.explainability.enable_confidence_scoring ? 'success' : 'default'}
                          size="small"
                        />
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" color="text.secondary">Source Attribution:</Typography>
                        <Chip
                          label={llmConfig?.explainability.enable_source_attribution ? 'Enabled' : 'Disabled'}
                          color={llmConfig?.explainability.enable_source_attribution ? 'success' : 'default'}
                          size="small"
                        />
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">Reasoning Chains:</Typography>
                        <Chip
                          label={llmConfig?.explainability.enable_reasoning_chains ? 'Enabled' : 'Disabled'}
                          color={llmConfig?.explainability.enable_reasoning_chains ? 'success' : 'default'}
                          size="small"
                        />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Vision Settings */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      Vision Settings
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Vision model configurations for OCR and image analysis
                    </Typography>
                    <Divider sx={{ mb: 2 }} />

                    {/* Custom Vision */}
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="body2" fontWeight="bold" color="primary.main" gutterBottom>
                        Custom Vision (GenAI Lab)
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" color="text.secondary">Model:</Typography>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace', maxWidth: '60%', textAlign: 'right', wordBreak: 'break-all' }}>
                            {llmConfig?.vision.custom_vision_model || 'N/A'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" color="text.secondary">Base URL:</Typography>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace', maxWidth: '60%', textAlign: 'right', wordBreak: 'break-all' }}>
                            {llmConfig?.vision.custom_vision_base_url || 'N/A'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" color="text.secondary">Timeout:</Typography>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                            {llmConfig?.vision.custom_vision_timeout || 0}s
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', pt: 1 }}>
                          <Typography variant="body2" color="text.secondary">Status:</Typography>
                          <Chip
                            label={llmConfig?.provider_status.custom_vision_available ? '✓ Available' : '✗ Unavailable'}
                            color={llmConfig?.provider_status.custom_vision_available ? 'success' : 'error'}
                            size="small"
                          />
                        </Box>
                      </Box>
                    </Box>

                    {/* Ollama Vision */}
                    <Box>
                      <Typography variant="body2" fontWeight="bold" sx={{ color: '#9333ea' }} gutterBottom>
                        Ollama Vision (Local)
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" color="text.secondary">Model:</Typography>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                            {llmConfig?.vision.ollama_vision_model || 'N/A'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" color="text.secondary">Base URL:</Typography>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                            {llmConfig?.vision.ollama_vision_base_url || 'N/A'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: 1, borderColor: 'divider' }}>
                          <Typography variant="body2" color="text.secondary">Timeout:</Typography>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                            {llmConfig?.vision.ollama_vision_timeout || 0}s
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', pt: 1 }}>
                          <Typography variant="body2" color="text.secondary">Status:</Typography>
                          <Chip
                            label={llmConfig?.provider_status.ollama_vision_available ? '✓ Available' : '✗ Unavailable'}
                            color={llmConfig?.provider_status.ollama_vision_available ? 'success' : 'error'}
                            size="small"
                          />
                        </Box>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* OCR Settings */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      OCR Settings
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Optical Character Recognition configurations
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" color="text.secondary">Max File Size:</Typography>
                        <Typography variant="body2" fontWeight="bold" sx={{ fontFamily: 'monospace' }}>
                          {llmConfig?.ocr.max_file_size_mb || 0} MB
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" color="text.secondary">Image Max Dimension:</Typography>
                        <Typography variant="body2" fontWeight="bold" sx={{ fontFamily: 'monospace' }}>
                          {llmConfig?.ocr.image_max_dimension || 0}px
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" color="text.secondary">Confidence Threshold:</Typography>
                        <Typography variant="body2" fontWeight="bold" sx={{ fontFamily: 'monospace' }}>
                          {llmConfig?.ocr.confidence_threshold || 0}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" color="text.secondary">PDF DPI:</Typography>
                        <Typography variant="body2" fontWeight="bold" sx={{ fontFamily: 'monospace' }}>
                          {llmConfig?.ocr.pdf_dpi || 0}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" color="text.secondary">Preprocessing:</Typography>
                        <Chip
                          label={llmConfig?.ocr.enable_preprocessing ? 'Enabled' : 'Disabled'}
                          color={llmConfig?.ocr.enable_preprocessing ? 'success' : 'default'}
                          size="small"
                        />
                      </Box>
                      <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>Supported Formats:</Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                          {llmConfig?.ocr.supported_formats?.map((format) => (
                            <Chip
                              key={format}
                              label={format}
                              size="small"
                              variant="outlined"
                              sx={{ fontFamily: 'monospace' }}
                            />
                          ))}
                        </Box>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* Prompt Library Tab (Super Admin Only) */}
          {activeTab === 4 && currentUser?.roles.includes('super_admin') && (
            <Box>
              {/* Stats Cards */}
              <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" variant="body2" gutterBottom>
                        Total Prompts
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CodeIcon sx={{ color: 'primary.main', fontSize: 32 }} />
                        <Typography variant="h3" fontWeight="bold">
                          {promptStats?.total_prompts || 0}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" variant="body2" gutterBottom>
                        Built-in Prompts
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <DescriptionIcon sx={{ color: 'success.main', fontSize: 32 }} />
                        <Typography variant="h3" fontWeight="bold">
                          {promptStats?.built_in_prompts || 0}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" variant="body2" gutterBottom>
                        Custom Prompts
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <EditIcon sx={{ color: 'warning.main', fontSize: 32 }} />
                        <Typography variant="h3" fontWeight="bold">
                          {promptStats?.custom_prompts || 0}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Category Filter and Prompts List */}
              <Paper>
                <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Box>
                      <Typography variant="h6" fontWeight="bold">Prompt Library</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Browse and manage all system prompts
                      </Typography>
                    </Box>
                    <FormControl sx={{ minWidth: 200 }}>
                      <InputLabel>Category</InputLabel>
                      <Select
                        value={selectedCategory}
                        label="Category"
                        onChange={(e) => setSelectedCategory(e.target.value)}
                      >
                        <MenuItem value="all">All Categories</MenuItem>
                        {promptStats && Object.keys(promptStats.by_category).sort().map((cat) => (
                          <MenuItem key={cat} value={cat}>
                            {cat} ({promptStats.by_category[cat]})
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Box>

                  {/* Category Stats */}
                  {promptStats && (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                      {Object.entries(promptStats.by_category).sort().map(([cat, count]) => (
                        <Chip
                          key={cat}
                          label={`${cat}: ${count}`}
                          variant={selectedCategory === cat ? 'filled' : 'outlined'}
                          color={selectedCategory === cat ? 'primary' : 'default'}
                          onClick={() => setSelectedCategory(cat)}
                          sx={{ cursor: 'pointer' }}
                        />
                      ))}
                      {selectedCategory !== 'all' && (
                        <Chip
                          label="Clear Filter"
                          variant="outlined"
                          color="default"
                          onDelete={() => setSelectedCategory('all')}
                          onClick={() => setSelectedCategory('all')}
                        />
                      )}
                    </Box>
                  )}
                </Box>

                {/* Prompts Grid */}
                <Box sx={{ p: 3 }}>
                  <Grid container spacing={2}>
                    {prompts.map((prompt) => (
                      <Grid item xs={12} md={6} lg={4} key={prompt.name}>
                        <Card
                          sx={{
                            height: '100%',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            '&:hover': {
                              boxShadow: 4,
                              transform: 'translateY(-2px)',
                            },
                          }}
                          onClick={() => {
                            setSelectedPrompt(prompt)
                            setShowPromptDetails(true)
                          }}
                        >
                          <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                              <Typography variant="h6" fontWeight="bold" sx={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>
                                {prompt.name}
                              </Typography>
                              {prompt.is_custom && (
                                <Chip label="Custom" size="small" color="warning" />
                              )}
                            </Box>
                            <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                              <Chip
                                label={prompt.category}
                                size="small"
                                color="primary"
                                variant="outlined"
                                icon={<CategoryIcon />}
                              />
                              <Chip
                                label={`v${prompt.version}`}
                                size="small"
                                variant="outlined"
                              />
                            </Box>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2, minHeight: 40 }}>
                              {prompt.description}
                            </Typography>
                            <Divider sx={{ my: 1 }} />
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <Typography variant="caption" color="text.secondary">
                                {prompt.variables.length} variables
                              </Typography>
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>

                  {prompts.length === 0 && (
                    <Box sx={{ textAlign: 'center', py: 8 }}>
                      <CodeIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                      <Typography variant="h6" color="text.secondary">
                        No prompts found in this category
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Paper>

              {/* Most Used Prompts */}
              {promptStats && promptStats.most_used.length > 0 && (
                <Paper sx={{ mt: 4, p: 3 }}>
                  <Typography variant="h6" fontWeight="bold" gutterBottom>
                    Most Used Prompts
                  </Typography>
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Rank</TableCell>
                          <TableCell>Prompt Name</TableCell>
                          <TableCell>Category</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {promptStats.most_used.map((prompt, index) => (
                          <TableRow key={prompt.name} hover>
                            <TableCell>
                              <Chip
                                label={`#${index + 1}`}
                                size="small"
                                color={index === 0 ? 'success' : index === 1 ? 'info' : 'default'}
                              />
                            </TableCell>
                            <TableCell>
                              <Typography fontWeight="bold" sx={{ fontFamily: 'monospace' }}>
                                {prompt.name}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip label={prompt.category} size="small" color="primary" variant="outlined" />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Paper>
              )}
            </Box>
          )}
      </Container>

      {/* Prompt Details Dialog */}
      <Dialog
        open={showPromptDetails}
        onClose={() => setShowPromptDetails(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedPrompt && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h6" fontWeight="bold" sx={{ fontFamily: 'monospace' }}>
                    {selectedPrompt.name}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                    <Chip label={selectedPrompt.category} size="small" color="primary" />
                    <Chip label={`v${selectedPrompt.version}`} size="small" />
                    {selectedPrompt.is_custom && (
                      <Chip label="Custom" size="small" color="warning" />
                    )}
                  </Box>
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* Description */}
                <Box>
                  <Typography variant="subtitle2" fontWeight="bold" color="text.secondary" gutterBottom>
                    Description
                  </Typography>
                  <Typography variant="body2">{selectedPrompt.description}</Typography>
                </Box>

                {/* Purpose */}
                {selectedPrompt.purpose && (
                  <Box>
                    <Typography variant="subtitle2" fontWeight="bold" color="text.secondary" gutterBottom>
                      Purpose
                    </Typography>
                    <Typography variant="body2">{selectedPrompt.purpose}</Typography>
                  </Box>
                )}

                {/* Variables */}
                <Box>
                  <Typography variant="subtitle2" fontWeight="bold" color="text.secondary" gutterBottom>
                    Variables ({selectedPrompt.variables.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {selectedPrompt.variables.map((variable) => (
                      <Chip
                        key={variable}
                        label={`{${variable}}`}
                        size="small"
                        variant="outlined"
                        sx={{ fontFamily: 'monospace' }}
                      />
                    ))}
                    {selectedPrompt.variables.length === 0 && (
                      <Typography variant="body2" color="text.secondary">
                        No variables required
                      </Typography>
                    )}
                  </Box>
                </Box>

                {/* Template */}
                <Box>
                  <Typography variant="subtitle2" fontWeight="bold" color="text.secondary" gutterBottom>
                    Template
                  </Typography>
                  <Paper
                    sx={{
                      p: 2,
                      bgcolor: 'grey.900',
                      color: 'grey.100',
                      fontFamily: 'monospace',
                      fontSize: '0.85rem',
                      maxHeight: 400,
                      overflow: 'auto',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {selectedPrompt.template}
                  </Paper>
                </Box>

                {/* Output Format */}
                <Box>
                  <Typography variant="subtitle2" fontWeight="bold" color="text.secondary" gutterBottom>
                    Output Format
                  </Typography>
                  <Chip label={selectedPrompt.output_format} size="small" variant="outlined" />
                </Box>

                {/* Examples */}
                {selectedPrompt.examples && selectedPrompt.examples.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" fontWeight="bold" color="text.secondary" gutterBottom>
                      Examples
                    </Typography>
                    {selectedPrompt.examples.map((example, index) => (
                      <Paper key={index} sx={{ p: 2, mb: 1, bgcolor: 'action.hover' }}>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                          {example}
                        </Typography>
                      </Paper>
                    ))}
                  </Box>
                )}

                {/* Metadata */}
                <Box>
                  <Typography variant="subtitle2" fontWeight="bold" color="text.secondary" gutterBottom>
                    Metadata
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">Created:</Typography>
                      <Typography variant="body2">{formatDate(selectedPrompt.created_at)}</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">Type:</Typography>
                      <Typography variant="body2">
                        {selectedPrompt.is_custom ? 'Custom (Runtime)' : 'Built-in'}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setShowPromptDetails(false)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Password Reset Dialog */}
      <Dialog
        open={showPasswordReset}
        onClose={() => setShowPasswordReset(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Reset Password for {resetPasswordUsername}</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="New Password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Enter new password (min 6 characters)"
              helperText="Password must be at least 6 characters long"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPasswordReset(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleResetPassword}
            disabled={!newPassword || newPassword.length < 6}
          >
            Reset Password
          </Button>
        </DialogActions>
      </Dialog>

      {/* Password Change Dialog */}
      <Dialog open={showPasswordDialog} onClose={() => setShowPasswordDialog(false)}>
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            type="password"
            label="Current Password"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            margin="normal"
          />
          <TextField
            fullWidth
            type="password"
            label="New Password"
            value={newPasswordSelf}
            onChange={(e) => setNewPasswordSelf(e.target.value)}
            margin="normal"
          />
          <TextField
            fullWidth
            type="password"
            label="Confirm New Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPasswordDialog(false)}>Cancel</Button>
          <Button onClick={handleChangePassword} variant="contained">Change Password</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
