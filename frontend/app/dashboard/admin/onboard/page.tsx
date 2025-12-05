'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/auth-context'
import { adminAPI } from '@/lib/api'
import { useSnackbar } from '@/components/SnackbarProvider'
import { useRouter } from 'next/navigation'
import {
  Box,
  Container,
  Paper,
  Card,
  CardContent,
  Button,
  TextField,
  Typography,
  Alert,
  AlertTitle,
  CircularProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  InputAdornment,
} from '@mui/material'
import {
  PersonAdd as PersonAddIcon,
  ArrowBack as ArrowBackIcon,
  ContentCopy as CopyIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
} from '@mui/icons-material'

interface OnboardedAdmin {
  id: number
  username: string
  email: string
  name: string
  company: string
  password: string
  roles: string[]
  message: string
}

export default function OnboardAdminPage() {
  const { user, hasRole } = useAuth()
  const router = useRouter()
  const { showSnackbar } = useSnackbar()

  const [formData, setFormData] = useState({
    email: '',
    company: '',
    name: '',
  })
  const [loading, setLoading] = useState(false)
  const [onboardedAdmin, setOnboardedAdmin] = useState<OnboardedAdmin | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [showDialog, setShowDialog] = useState(false)
  const [errors, setErrors] = useState<{ [key: string]: string }>({})

  // Check if user is super admin
  if (user && !hasRole('super_admin')) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error">
          <AlertTitle>Access Denied</AlertTitle>
          Only Super Admins can onboard new admin users. Please contact your system administrator.
        </Alert>
        <Button
          variant="contained"
          startIcon={<ArrowBackIcon />}
          onClick={() => router.push('/dashboard')}
          sx={{ mt: 2 }}
        >
          Back to Dashboard
        </Button>
      </Container>
    )
  }

  const validateForm = () => {
    const newErrors: { [key: string]: string } = {}

    if (!formData.email) {
      newErrors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format'
    }

    if (!formData.company || formData.company.length < 2) {
      newErrors.company = 'Company name must be at least 2 characters'
    }

    if (!formData.name || formData.name.length < 2) {
      newErrors.name = 'Name must be at least 2 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      showSnackbar('Please fix the form errors', 'error')
      return
    }

    setLoading(true)
    try {
      const response = await adminAPI.onboardAdmin(formData)
      const adminData = response.data

      setOnboardedAdmin(adminData)
      setShowDialog(true)

      // Reset form
      setFormData({
        email: '',
        company: '',
        name: '',
      })
      setErrors({})

      showSnackbar('Admin user onboarded successfully!', 'success')
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to onboard admin'
      showSnackbar(errorMessage, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleCopyPassword = () => {
    if (onboardedAdmin?.password) {
      navigator.clipboard.writeText(onboardedAdmin.password)
      showSnackbar('Password copied to clipboard!', 'success')
    }
  }

  const handleCopyCredentials = () => {
    if (onboardedAdmin) {
      const credentials = `Username: ${onboardedAdmin.username}\nPassword: ${onboardedAdmin.password}\nEmail: ${onboardedAdmin.email}`
      navigator.clipboard.writeText(credentials)
      showSnackbar('Credentials copied to clipboard!', 'success')
    }
  }

  const handleCloseDialog = () => {
    setShowDialog(false)
    setShowPassword(false)
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => router.push('/dashboard/admin')}
        sx={{ mb: 3 }}
      >
        Back to Admin Panel
      </Button>

      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <PersonAddIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
          <Box>
            <Typography variant="h4" gutterBottom>
              Onboard Admin User
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Create a new admin user with auto-generated secure credentials
            </Typography>
          </Box>
        </Box>

        <Alert severity="info" sx={{ mb: 3 }}>
          <AlertTitle>Super Admin Action</AlertTitle>
          This form will create a new admin user with an auto-generated secure password.
          Make sure to save the credentials securely after submission.
        </Alert>

        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Email Address"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            error={!!errors.email}
            helperText={errors.email || 'Admin user\'s email address'}
            margin="normal"
            required
            disabled={loading}
          />

          <TextField
            fullWidth
            label="Full Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            error={!!errors.name}
            helperText={errors.name || 'Admin user\'s full name'}
            margin="normal"
            required
            disabled={loading}
          />

          <TextField
            fullWidth
            label="Company / Organization"
            value={formData.company}
            onChange={(e) => setFormData({ ...formData, company: e.target.value })}
            error={!!errors.company}
            helperText={errors.company || 'Company or organization name'}
            margin="normal"
            required
            disabled={loading}
          />

          <Box sx={{ mt: 4, display: 'flex', gap: 2 }}>
            <Button
              type="submit"
              variant="contained"
              size="large"
              fullWidth
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : <PersonAddIcon />}
            >
              {loading ? 'Creating Admin...' : 'Create Admin User'}
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Success Dialog */}
      <Dialog
        open={showDialog}
        onClose={handleCloseDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ bgcolor: 'success.main', color: 'white' }}>
          ✅ Admin User Created Successfully!
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          {onboardedAdmin && (
            <Box>
              <Alert severity="warning" sx={{ mb: 3 }}>
                <AlertTitle>Important: Save These Credentials</AlertTitle>
                The password is only shown once. Make sure to save it securely.
              </Alert>

              <Card sx={{ mb: 2, bgcolor: 'grey.50' }}>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Username
                  </Typography>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    {onboardedAdmin.username}
                  </Typography>

                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Email
                  </Typography>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    {onboardedAdmin.email}
                  </Typography>

                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Full Name
                  </Typography>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    {onboardedAdmin.name}
                  </Typography>

                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Company
                  </Typography>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    {onboardedAdmin.company}
                  </Typography>

                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Auto-Generated Password
                  </Typography>
                  <TextField
                    fullWidth
                    value={onboardedAdmin.password}
                    type={showPassword ? 'text' : 'password'}
                    InputProps={{
                      readOnly: true,
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() => setShowPassword(!showPassword)}
                            edge="end"
                          >
                            {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                          </IconButton>
                          <IconButton onClick={handleCopyPassword} edge="end">
                            <CopyIcon />
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      mb: 2,
                      '& .MuiInputBase-input': {
                        fontFamily: 'monospace',
                        fontSize: '1.1rem',
                        fontWeight: 'bold',
                      }
                    }}
                  />

                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Role
                  </Typography>
                  <Typography variant="body1" sx={{ color: 'success.main', fontWeight: 'bold' }}>
                    {onboardedAdmin.roles.join(', ')}
                  </Typography>
                </CardContent>
              </Card>

              <Alert severity="info">
                The admin user can now login with these credentials and access the admin panel.
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2, gap: 1 }}>
          <Button
            onClick={handleCopyCredentials}
            startIcon={<CopyIcon />}
            variant="outlined"
          >
            Copy All Credentials
          </Button>
          <Button onClick={handleCloseDialog} variant="contained">
            Done
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}
