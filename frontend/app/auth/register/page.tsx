'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/lib/auth-context'
import {
  Box,
  Container,
  Typography,
  Button,
  TextField,
  Card,
  CardContent,
  Alert,
  AppBar,
  Toolbar,
  Stack
} from '@mui/material'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Psychology as BrainIcon } from '@mui/icons-material'

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const { register } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await register(formData)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ minHeight: '100vh' }}>
      {/* Navigation */}
      <AppBar
        position="fixed"
        sx={{
          backgroundColor: 'background.paper',
          backdropFilter: 'blur(10px)',
          boxShadow: 1
        }}
      >
        <Toolbar>
          <Box
            sx={{ display: 'flex', alignItems: 'center', gap: 1, flexGrow: 1, cursor: 'pointer' }}
            onClick={() => router.push('/')}
          >
            <BrainIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                background: 'linear-gradient(90deg, #2563eb 0%, #4f46e5 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              AERO: AI for Energy Resource Optimization
            </Typography>
          </Box>
          <Stack direction="row" spacing={2} alignItems="center">
            <ThemeToggle />
            <Button
              variant="text"
              onClick={() => router.push('/auth/login')}
            >
              Login
            </Button>
          </Stack>
        </Toolbar>
      </AppBar>

      {/* Register Form */}
      <Container maxWidth="sm">
        <Box
          sx={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            py: 12
          }}
        >
          <Card sx={{ width: '100%' }}>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                Register
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
                Create a new account to get started
              </Typography>

              <Box component="form" onSubmit={handleSubmit}>
                <Stack spacing={3}>
                  {error && (
                    <Alert severity="error">{error}</Alert>
                  )}

                  <TextField
                    fullWidth
                    label="Username"
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    required
                    disabled={loading}
                    autoComplete="username"
                  />

                  <TextField
                    fullWidth
                    label="Email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                    disabled={loading}
                    autoComplete="email"
                  />

                  <TextField
                    fullWidth
                    label="Full Name (Optional)"
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    disabled={loading}
                    autoComplete="name"
                  />

                  <TextField
                    fullWidth
                    label="Password"
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    required
                    disabled={loading}
                    autoComplete="new-password"
                    inputProps={{ minLength: 6 }}
                    helperText="Minimum 6 characters"
                  />

                  <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    fullWidth
                    disabled={loading}
                  >
                    {loading ? 'Creating account...' : 'Register'}
                  </Button>

                  <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
                    Already have an account?{' '}
                    <Link href="/auth/login" style={{ color: 'inherit', textDecoration: 'none' }}>
                      <Typography
                        component="span"
                        color="primary"
                        sx={{ fontWeight: 600, '&:hover': { textDecoration: 'underline' } }}
                      >
                        Login
                      </Typography>
                    </Link>
                  </Typography>
                </Stack>
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Container>
    </Box>
  )
}
