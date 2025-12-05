'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import {
  Box,
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  AppBar,
  Toolbar,
  Stack,
  Paper,
  CircularProgress
} from '@mui/material'
import { useSnackbar } from '@/components/SnackbarProvider'
import { ThemeToggle } from '@/components/ThemeToggle'
import {
  Psychology as BrainIcon,
  Description as FileTextIcon,
  Chat as MessageSquareIcon,
  Group as UsersIcon,
  BarChart as BarChart3Icon,
  Logout as LogOutIcon,
  Code as CodeIcon,
  Home as HomeIcon
} from '@mui/icons-material'
import { authAPI } from '@/lib/api'

export default function DashboardPage() {
  const { user, logout, hasPermission, hasRole, refreshUser } = useAuth()
  const router = useRouter()
  const { showSnackbar } = useSnackbar()
  const [updatingProvider, setUpdatingProvider] = useState(false)
  const [updatingExplainability, setUpdatingExplainability] = useState(false)

  const features = [
    {
      title: 'Chat',
      description: 'Interact with AI using RAG and multi-agent system',
      icon: MessageSquareIcon,
      href: '/dashboard/chat',
      permission: 'chat:use',
      color: 'primary.main',
    },
    {
      title: 'Council of Agents',
      description: 'Multi-agent consensus with diverse AI perspectives',
      icon: BrainIcon,
      href: '/dashboard/council',
      permission: 'chat:use',
      color: 'secondary.main',
    },
    {
      title: 'Documents',
      description: 'Upload and manage knowledge base documents',
      icon: FileTextIcon,
      href: '/dashboard/documents',
      permission: 'documents:read',
      color: 'success.main',
    },
    {
      title: 'OCR',
      description: 'Extract text from images and PDFs using AI vision',
      icon: BrainIcon,
      href: '/dashboard/ocr',
      permission: 'documents:create',
      color: 'info.main',
    },
    {
      title: 'Explainability',
      description: 'View AI reasoning and confidence scores',
      icon: BarChart3Icon,
      href: '/dashboard/explainability',
      permission: 'explain:view',
      color: 'warning.main',
    },
    {
      title: 'Utilities',
      description: 'Tables, forms, charts and other UI components',
      icon: CodeIcon,
      href: '/dashboard/utilities',
      color: 'info.main',
    },
    {
      title: 'Admin',
      description: 'Manage users, roles, and system settings',
      icon: UsersIcon,
      href: '/dashboard/admin',
      role: 'admin',
      color: 'error.main',
    },
  ]

  const accessibleFeatures = features.filter((feature) => {
    if (feature.role) return hasRole(feature.role)
    if (feature.permission) return hasPermission(feature.permission)
    return true
  })

  const handleUpdateProvider = async (value: string) => {
    setUpdatingProvider(true)
    try {
      await authAPI.updateProfile({ preferred_llm: value })
      await refreshUser()
      showSnackbar(`LLM provider changed to ${value}`, 'success')
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to update provider', 'error')
    } finally {
      setUpdatingProvider(false)
    }
  }

  const handleUpdateExplainability = async (value: string) => {
    setUpdatingExplainability(true)
    try {
      await authAPI.updateProfile({ explainability_level: value })
      await refreshUser()
      showSnackbar(`Detail level changed to ${value}`, 'success')
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to update explainability level', 'error')
    } finally {
      setUpdatingExplainability(false)
    }
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper sx={{ borderRadius: 0, borderBottom: 1, borderColor: 'divider' }} elevation={1}>
        <Container maxWidth="xl">
          <Box sx={{ py: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <HomeIcon color="primary" />
                <Typography variant="h5" fontWeight="bold">
                  Dashboard
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ textAlign: 'right' }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {user?.full_name || user?.username}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'capitalize' }}>
                  {user?.roles.join(', ')}
                </Typography>
              </Box>
              <ThemeToggle />
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

      {/* Main Content */}
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ mb: 6 }}>
          <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
            Welcome back!
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Choose a feature to get started with AI-powered capabilities
          </Typography>
        </Box>

        {/* Feature Grid */}
        <Grid container spacing={3}>
          {accessibleFeatures.map((feature) => {
            const Icon = feature.icon
            return (
              <Grid item xs={12} md={6} lg={4} key={feature.href}>
                <Card
                  sx={{
                    height: '100%',
                    cursor: 'pointer',
                    transition: 'box-shadow 0.3s',
                    '&:hover': {
                      boxShadow: 6
                    }
                  }}
                  onClick={() => router.push(feature.href)}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Paper
                        elevation={0}
                        sx={{
                          p: 1.5,
                          bgcolor: 'action.hover',
                          borderRadius: 2
                        }}
                      >
                        <Icon sx={{ fontSize: 28, color: feature.color }} />
                      </Paper>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {feature.title}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {feature.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            )
          })}
        </Grid>

        {/* Info Cards */}
        <Grid container spacing={3} sx={{ mt: 4 }}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  LLM Provider
                </Typography>
                <FormControl fullWidth disabled={updatingProvider}>
                  <InputLabel>Provider</InputLabel>
                  <Select
                    value={user?.preferred_llm || 'custom'}
                    onChange={(e) => handleUpdateProvider(e.target.value)}
                    label="Provider"
                  >
                    <MenuItem value="custom">Custom API</MenuItem>
                    <MenuItem value="ollama">Ollama</MenuItem>
                  </Select>
                </FormControl>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Current selection
                </Typography>
                {updatingProvider && <CircularProgress size={20} sx={{ mt: 1 }} />}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  Explainability Level
                </Typography>
                <FormControl fullWidth disabled={updatingExplainability}>
                  <InputLabel>Level</InputLabel>
                  <Select
                    value={user?.explainability_level || 'basic'}
                    onChange={(e) => handleUpdateExplainability(e.target.value)}
                    label="Level"
                  >
                    <MenuItem value="basic">Basic</MenuItem>
                    <MenuItem value="detailed">Detailed</MenuItem>
                    <MenuItem value="debug">Debug</MenuItem>
                  </Select>
                </FormControl>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Detail level
                </Typography>
                {updatingExplainability && <CircularProgress size={20} sx={{ mt: 1 }} />}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  Permissions
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
                  {user?.permissions.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Access rights
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  )
}
