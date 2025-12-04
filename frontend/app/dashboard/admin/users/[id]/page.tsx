'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { adminAPI } from '@/lib/api'
import { useSnackbar } from '@/components/SnackbarProvider'
import { formatDate } from '@/lib/utils'
import { useRouter, useParams } from 'next/navigation'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Divider,
  FormControl,
  FormHelperText,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  SelectChangeEvent,
  TextField,
  Typography,
} from '@mui/material'
import {
  ArrowBack as ArrowBackIcon,
  Save as SaveIcon,
  Person as PersonIcon,
  Email as EmailIcon,
  Security as SecurityIcon,
  CalendarMonth as CalendarIcon,
  Timeline as ActivityIcon,
} from '@mui/icons-material'

interface User {
  id: string
  username: string
  email: string
  full_name: string
  role: string
  roles?: string[]
  is_active: boolean
  created_at: string
  last_login?: string
  preferred_llm?: string
  explainability_level?: string
}

interface Role {
  id: string
  name: string
  description: string
  permissions: string[]
}

export default function EditUserPage() {
  const { user: currentUser } = useAuth()
  const { showSnackbar } = useSnackbar()
  const router = useRouter()
  const params = useParams()
  const userId = params.id as string

  const [loading, setLoading] = useState<boolean>(true)
  const [saving, setSaving] = useState<boolean>(false)
  const [user, setUser] = useState<User | null>(null)
  const [roles, setRoles] = useState<Role[]>([])
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    role: '',
    is_active: true,
  })

  useEffect(() => {
    // Check admin permission
    if (currentUser && !currentUser.roles.includes('admin')) {
      showSnackbar('You do not have permission to access this page', 'error')
      router.push('/dashboard')
      return
    }

    if (currentUser) {
      loadData()
    }
  }, [currentUser, userId])

  const loadData = async () => {
    try {
      setLoading(true)
      const [userRes, rolesRes] = await Promise.all([
        adminAPI.getUser(userId),
        adminAPI.getRoles(),
      ])

      const userData = userRes.data
      if (!userData) {
        showSnackbar('User not found', 'error')
        router.push('/dashboard/admin')
        return
      }

      setUser(userData)
      setRoles(rolesRes.data)

      // Initialize form data
      setFormData({
        email: userData.email || '',
        full_name: userData.full_name || '',
        role: userData.role || (userData.roles && userData.roles[0]) || 'viewer',
        is_active: userData.is_active ?? true,
      })
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to load user data', 'error')
      router.push('/dashboard/admin')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      await adminAPI.updateUser(userId, {
        email: formData.email,
        full_name: formData.full_name,
        roles: [formData.role],
        is_active: formData.is_active,
      })

      showSnackbar('User updated successfully', 'success')
      router.push('/dashboard/admin')
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to update user', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleRoleChange = (event: SelectChangeEvent<string>) => {
    setFormData({ ...formData, role: event.target.value })
  }

  const getRoleChipColor = (roleName: string): 'error' | 'primary' | 'success' | 'default' => {
    switch (roleName) {
      case 'admin':
        return 'error'
      case 'analyst':
        return 'primary'
      case 'viewer':
        return 'success'
      default:
        return 'default'
    }
  }

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <CircularProgress size={48} />
      </Box>
    )
  }

  if (!user) {
    return null
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => router.push('/dashboard/admin')}
          sx={{ mb: 2 }}
        >
          Back to Admin
        </Button>
        <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
          Edit User
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Update user information and permissions
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* User Info Card */}
        <Card>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <PersonIcon />
              <Typography variant="h6" component="h2">
                User Information
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              View and edit basic user information
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {/* Username (Read-only) */}
              <Box>
                <TextField
                  fullWidth
                  label="Username"
                  value={user.username}
                  disabled
                  helperText="Username cannot be changed"
                />
              </Box>

              {/* Email */}
              <Box>
                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="user@example.com"
                  InputProps={{
                    startAdornment: <EmailIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                  }}
                />
              </Box>

              {/* Full Name */}
              <Box>
                <TextField
                  fullWidth
                  label="Full Name"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  placeholder="John Doe"
                />
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Role & Permissions Card */}
        <Card>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <SecurityIcon />
              <Typography variant="h6" component="h2">
                Role & Permissions
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Assign user role and manage access permissions
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {/* Role Selection */}
              <FormControl fullWidth>
                <InputLabel id="role-label">Role</InputLabel>
                <Select
                  labelId="role-label"
                  id="role"
                  value={formData.role}
                  label="Role"
                  onChange={handleRoleChange}
                >
                  {roles.map((role) => (
                    <MenuItem key={role.id} value={role.name}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={role.name}
                          color={getRoleChipColor(role.name)}
                          size="small"
                        />
                        <Typography variant="body2" color="text.secondary">
                          - {role.description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Show permissions for selected role */}
              {formData.role && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Permissions
                  </Typography>
                  <Paper
                    variant="outlined"
                    sx={{ p: 2, bgcolor: 'action.hover' }}
                  >
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {roles
                        .find((r) => r.name === formData.role)
                        ?.permissions.map((permission) => (
                          <Chip
                            key={permission}
                            label={permission}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                    </Box>
                  </Paper>
                </Box>
              )}
            </Box>
          </CardContent>
        </Card>

        {/* Account Status Card */}
        <Card>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <ActivityIcon />
              <Typography variant="h6" component="h2">
                Account Status
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Manage user account status and activity
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {/* Active Status */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Account Status
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {formData.is_active ? 'Active - User can log in' : 'Inactive - User cannot log in'}
                  </Typography>
                </Box>
                <Button
                  variant="contained"
                  color={formData.is_active ? 'error' : 'primary'}
                  onClick={() => setFormData({ ...formData, is_active: !formData.is_active })}
                >
                  {formData.is_active ? 'Deactivate' : 'Activate'}
                </Button>
              </Box>

              <Divider />

              {/* Account Info */}
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CalendarIcon sx={{ fontSize: 20, color: 'text.secondary' }} />
                  <Typography variant="body2" color="text.secondary">
                    Created:
                  </Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {formatDate(user.created_at)}
                  </Typography>
                </Box>
                {user.last_login && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ActivityIcon sx={{ fontSize: 20, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      Last Login:
                    </Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {formatDate(user.last_login)}
                    </Typography>
                  </Box>
                )}
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <SaveIcon />}
            onClick={handleSave}
            disabled={saving || user.username === currentUser?.username}
            fullWidth
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
          <Button
            variant="outlined"
            onClick={() => router.push('/dashboard/admin')}
            disabled={saving}
            sx={{ minWidth: 120 }}
          >
            Cancel
          </Button>
        </Box>

        {user.username === currentUser?.username && (
          <Paper
            sx={{
              p: 2,
              bgcolor: 'warning.light',
              color: 'warning.dark',
              textAlign: 'center',
            }}
          >
            <Typography variant="body2">
              ⚠️ You cannot modify your own account. Ask another admin for assistance.
            </Typography>
          </Paper>
        )}
      </Box>
    </Container>
  )
}
