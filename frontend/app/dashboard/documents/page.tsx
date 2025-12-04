'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { documentsAPI } from '@/lib/api'
import {
  Box,
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  AppBar,
  Toolbar,
  Stack,
  Grid,
  Paper,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Divider
} from '@mui/material'
import { useSnackbar } from '@/components/SnackbarProvider'
import { ThemeToggle } from '@/components/ThemeToggle'
import {
  Description as FileTextIcon,
  CloudUpload as UploadIcon,
  Delete as Trash2Icon,
  CheckCircle as CheckCircleIcon,
  Error as AlertCircleIcon,
  Schedule as ClockIcon,
  Home as HomeIcon,
  Public as GlobeIcon,
  Person as UserIcon,
  Info as InfoIcon
} from '@mui/icons-material'
import { formatDate, formatFileSize } from '@/lib/utils'
import { useRouter } from 'next/navigation'

interface Document {
  id: string
  filename: string
  file_type: string
  file_size: number
  title: string
  is_processed: boolean
  processing_status: string
  num_chunks: number
  uploaded_at: string
  scope?: string  // 'global' or 'user'
}

export default function DocumentsPage() {
  const { user } = useAuth()
  const { showSnackbar } = useSnackbar()
  const router = useRouter()
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [provider, setProvider] = useState(user?.preferred_llm || 'ollama')
  const [uploadScope, setUploadScope] = useState<'user' | 'global'>('user')
  const isAdmin = user?.roles?.includes('admin') || false

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      const response = await documentsAPI.list()
      setDocuments(response.data)
    } catch (error) {
      showSnackbar('Failed to load documents', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', file.name)
    formData.append('provider', provider)

    try {
      if (uploadScope === 'global' && isAdmin) {
        await documentsAPI.uploadGlobal(formData, provider)
        showSnackbar(`${file.name} uploaded to global knowledge base`, 'success')
      } else {
        await documentsAPI.upload(formData, provider)
        showSnackbar(`${file.name} uploaded and processed successfully`, 'success')
      }
      await loadDocuments()
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to upload document', 'error')
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const handleDelete = async (documentId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) return

    try {
      await documentsAPI.delete(documentId, provider)
      showSnackbar('Document deleted successfully', 'success')
      await loadDocuments()
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to delete document', 'error')
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon sx={{ fontSize: 20, color: 'success.main' }} />
      case 'processing':
        return <CircularProgress size={16} sx={{ color: 'info.main' }} />
      case 'failed':
        return <AlertCircleIcon sx={{ fontSize: 20, color: 'error.main' }} />
      default:
        return <ClockIcon sx={{ fontSize: 20, color: 'warning.main' }} />
    }
  }

  const getStatusBadge = (status: string) => {
    const colors: Record<string, any> = {
      completed: 'success',
      processing: 'info',
      failed: 'error',
      pending: 'warning',
    }
    return <Chip label={status} color={colors[status] || 'default'} size="small" />
  }

  const getScopeBadge = (scope?: string) => {
    if (scope === 'global') {
      return (
        <Chip
          icon={<GlobeIcon />}
          label="Global"
          size="small"
          sx={{ bgcolor: 'secondary.main', color: 'white' }}
        />
      )
    }
    return (
      <Chip
        icon={<UserIcon />}
        label="Personal"
        variant="outlined"
        size="small"
      />
    )
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar>
          <Button
            startIcon={<HomeIcon />}
            onClick={() => router.push('/dashboard')}
            sx={{ mr: 3 }}
          >
            Dashboard
          </Button>
          <FileTextIcon sx={{ fontSize: 28, color: 'primary.main', mr: 1 }} />
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>
            Document Management
          </Typography>
          <Stack direction="row" spacing={2} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel>Vector Store</InputLabel>
              <Select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                label="Vector Store"
              >
                <MenuItem value="custom">Custom API</MenuItem>
                <MenuItem value="ollama">Ollama</MenuItem>
              </Select>
            </FormControl>
            {isAdmin && (
              <FormControl size="small" sx={{ minWidth: 140 }}>
                <InputLabel>Upload To</InputLabel>
                <Select
                  value={uploadScope}
                  onChange={(e) => setUploadScope(e.target.value as 'user' | 'global')}
                  label="Upload To"
                >
                  <MenuItem value="user">Personal</MenuItem>
                  <MenuItem value="global">Global KB</MenuItem>
                </Select>
              </FormControl>
            )}
            <ThemeToggle />
            <Box>
              <input
                id="file-upload"
                type="file"
                style={{ display: 'none' }}
                accept=".pdf,.txt,.csv,.docx"
                onChange={handleUpload}
                disabled={uploading}
              />
              <Button
                component="label"
                htmlFor="file-upload"
                variant="contained"
                startIcon={uploading ? <CircularProgress size={16} color="inherit" /> : <UploadIcon />}
                disabled={uploading}
              >
                {uploading ? 'Uploading...' : (uploadScope === 'global' && isAdmin ? 'Upload to Global KB' : 'Upload Document')}
              </Button>
            </Box>
          </Stack>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Info Banner for Admins */}
        {isAdmin && (
          <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
              Global Knowledge Base
            </Typography>
            <Typography variant="body2">
              As an admin, you can upload documents to the <strong>Global Knowledge Base</strong> which will be accessible to all users when they search.
              Use this for company policies, shared resources, or common documentation.
            </Typography>
          </Alert>
        )}

        {/* Stats */}
        <Grid container spacing={2} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Total Documents
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {documents.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Personal Docs
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
                  {documents.filter((d) => d.scope !== 'global').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Global Docs
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700, color: 'secondary.main' }}>
                  {documents.filter((d) => d.scope === 'global').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Total Chunks
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {documents.reduce((sum, d) => sum + d.num_chunks, 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Total Size
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {formatFileSize(documents.reduce((sum, d) => sum + d.file_size, 0))}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Document List */}
        <Card>
          <CardContent sx={{ p: 0 }}>
            <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                Documents
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {isAdmin
                  ? 'Upload to your personal knowledge base or the global knowledge base (shared with all users)'
                  : 'Upload PDF, TXT, CSV, or DOCX files to your personal knowledge base. Global documents are shared by admins.'}
              </Typography>
            </Box>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 12 }}>
                <CircularProgress size={48} />
              </Box>
            ) : documents.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 12 }}>
                <FileTextIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                  No documents yet
                </Typography>
                <Typography color="text.secondary">
                  Upload your first document to get started
                </Typography>
              </Box>
            ) : (
              <List sx={{ maxHeight: 600, overflow: 'auto' }}>
                {documents.map((doc) => (
                  <ListItem
                    key={doc.id}
                    sx={{
                      py: 2,
                      px: 3,
                      borderBottom: 1,
                      borderColor: 'divider',
                      '&:hover': { bgcolor: 'action.hover' },
                      '&:last-child': { borderBottom: 0 },
                    }}
                    secondaryAction={
                      <IconButton
                        edge="end"
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        color="error"
                      >
                        <Trash2Icon />
                      </IconButton>
                    }
                  >
                    <ListItemIcon>
                      <Box
                        sx={{
                          p: 1.5,
                          bgcolor: 'primary.main',
                          color: 'primary.contrastText',
                          borderRadius: 2,
                          display: 'flex',
                          opacity: 0.9,
                        }}
                      >
                        <FileTextIcon />
                      </Box>
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {doc.title}
                          </Typography>
                          {getStatusBadge(doc.processing_status)}
                          {getScopeBadge(doc.scope)}
                        </Box>
                      }
                      secondary={
                        <>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                            {getStatusIcon(doc.processing_status)}
                            <Typography variant="body2" color="text.secondary" component="span">
                              {doc.filename}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" component="span">
                              • {doc.file_type.toUpperCase()} • {formatFileSize(doc.file_size)}
                              {doc.num_chunks > 0 && ` • ${doc.num_chunks} chunks`}
                            </Typography>
                          </Box>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                            Uploaded {formatDate(doc.uploaded_at)}
                          </Typography>
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </CardContent>
        </Card>
      </Container>
    </Box>
  )
}
