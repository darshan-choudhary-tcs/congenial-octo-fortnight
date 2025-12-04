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
  Stack,
  Paper
} from '@mui/material'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Psychology as BrainIcon } from '@mui/icons-material'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const { login } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(username, password)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
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
              AI RAG Platform
            </Typography>
          </Box>
          <Stack direction="row" spacing={2} alignItems="center">
            <ThemeToggle />
            <Button
              variant="text"
              onClick={() => router.push('/auth/register')}
            >
              Register
            </Button>
          </Stack>
        </Toolbar>
      </AppBar>

      {/* Login Form */}
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
                Login
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
                Enter your credentials to access the RAG & Multi-Agent System
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
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    disabled={loading}
                    autoComplete="username"
                  />

                  <TextField
                    fullWidth
                    label="Password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={loading}
                    autoComplete="current-password"
                  />

                  <Paper
                    variant="outlined"
                    sx={{ p: 2, bgcolor: 'action.hover' }}
                  >
                    <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                      Demo Accounts:
                    </Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                      Admin: admin / admin123
                    </Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                      Analyst: analyst1 / analyst123
                    </Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                      Viewer: viewer1 / viewer123
                    </Typography>
                  </Paper>

                  <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    fullWidth
                    disabled={loading}
                  >
                    {loading ? 'Logging in...' : 'Login'}
                  </Button>

                  <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
                    Don't have an account?{' '}
                    <Link href="/auth/register" style={{ color: 'inherit', textDecoration: 'none' }}>
                      <Typography
                        component="span"
                        color="primary"
                        sx={{ fontWeight: 600, '&:hover': { textDecoration: 'underline' } }}
                      >
                        Register
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
