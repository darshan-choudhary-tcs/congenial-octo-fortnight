'use client'

import { useState, useEffect, useRef } from 'react'
import { useAuth } from '@/lib/auth-context'
import { chatAPI, documentsAPI } from '@/lib/api'
import { useSnackbar } from '@/components/SnackbarProvider'
import { ThemeToggle } from '@/components/ThemeToggle'
import { formatDate, getConfidenceColor, getConfidenceLabel } from '@/lib/utils'
import ReactMarkdown from 'react-markdown'
import { useRouter } from 'next/navigation'
import {
  Box,
  Button,
  TextField,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  IconButton,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Checkbox,
  FormControlLabel,
  CircularProgress,
  Divider,
  AppBar,
  Toolbar,
  Container,
  Popover,
  Avatar,
  Tooltip,
  Stepper,
  Step,
  StepLabel,
  Badge,
} from '@mui/material'
import {
  Chat as MessageSquareIcon,
  Send as SendIcon,
  Upload as UploadIcon,
  Home as HomeIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Psychology as BrainIcon,
  Lightbulb as LightbulbIcon,
  Shield as ShieldIcon,
  CheckCircle as CheckCircleIcon,
  ExpandMore as ExpandMoreIcon,
  Description as FileTextIcon,
  Add as AddIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  Close as CloseIcon,
  Person as PersonIcon,
  SmartToy as SmartToyIcon,
  Verified as VerifiedIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: any[]
  confidence_score?: number
  low_confidence_warning?: boolean
  created_at: string
}

interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

interface AgentStatus {
  agent: string
  action: string
  status: 'started' | 'completed' | 'failed'
  message: string
  timestamp: string
  result?: any
}

interface StreamingState {
  isStreaming: boolean
  currentAgent: string | null
  agentStatuses: AgentStatus[]
  accumulatedResponse: string
}

export default function ChatPage() {
  const { user } = useAuth()
  const { showSnackbar } = useSnackbar()
  const router = useRouter()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversation, setCurrentConversation] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingConversations, setLoadingConversations] = useState(true)
  const [provider, setProvider] = useState(user?.preferred_llm || 'ollama')
  const [includeGrounding, setIncludeGrounding] = useState(true)
  const [uploadingDoc, setUploadingDoc] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [streamingState, setStreamingState] = useState<StreamingState>({
    isStreaming: false,
    currentAgent: null,
    agentStatuses: [],
    accumulatedResponse: ''
  })
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    loadConversations()
  }, [])

  useEffect(() => {
    if (currentConversation) {
      loadMessages(currentConversation)
    }
  }, [currentConversation])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const handleKeyboard = (e: KeyboardEvent) => {
      // Cmd+K or Ctrl+K for new conversation
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        handleNewConversation()
      }
    }
    window.addEventListener('keydown', handleKeyboard)
    return () => window.removeEventListener('keydown', handleKeyboard)
  }, [])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadConversations = async () => {
    try {
      const response = await chatAPI.getConversations()
      setConversations(response.data)
      if (response.data.length > 0 && !currentConversation) {
        setCurrentConversation(response.data[0].id)
      }
    } catch (error) {
      console.error('Failed to load conversations:', error)
    } finally {
      setLoadingConversations(false)
    }
  }

  const filteredConversations = conversations.filter(conv =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const loadMessages = async (conversationId: string) => {
    try {
      const response = await chatAPI.getMessages(conversationId)
      setMessages(response.data)
    } catch (error) {
      console.error('Failed to load messages:', error)
      showSnackbar('Failed to load messages', 'error')
    }
  }

  const handleSendMessageStream = async () => {
    if (!input.trim() || loading || streamingState.isStreaming) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    // Add user message optimistically
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, tempUserMsg])

    // Initialize streaming state
    setStreamingState({
      isStreaming: true,
      currentAgent: null,
      agentStatuses: [],
      accumulatedResponse: ''
    })

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController()

    try {
      const token = localStorage.getItem('token')
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      const response = await fetch(`${API_URL}/api/v1/chat/message/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_id: currentConversation || undefined,
          provider,
          include_grounding: includeGrounding,
        }),
        signal: abortControllerRef.current.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body reader')
      }

      let buffer = ''
      let finalResult: any = null
      let conversationId: string | null = null
      let messageId: string | null = null

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue

          if (line.startsWith('event:')) {
            const eventType = line.substring(6).trim()
            continue
          }

          if (line.startsWith('data:')) {
            const data = line.substring(5).trim()

            try {
              const eventData = JSON.parse(data)

              // Handle different event types
              if (eventData.conversation_id) {
                conversationId = eventData.conversation_id
                if (!currentConversation) {
                  setCurrentConversation(conversationId)
                }
              }

              if (eventData.message_id) {
                messageId = eventData.message_id
              }

              // Agent status events
              if (eventData.agent && eventData.status) {
                const agentStatus: AgentStatus = {
                  agent: eventData.agent,
                  action: eventData.action || '',
                  status: eventData.status,
                  message: eventData.message || '',
                  timestamp: eventData.timestamp || new Date().toISOString(),
                  result: eventData.result
                }

                setStreamingState(prev => ({
                  ...prev,
                  currentAgent: eventData.status === 'started' ? eventData.agent : null,
                  agentStatuses: [...prev.agentStatuses, agentStatus]
                }))
              }

              // Final complete event
              if (eventData.response !== undefined) {
                finalResult = eventData
                setStreamingState(prev => ({
                  ...prev,
                  accumulatedResponse: eventData.response
                }))
              }

              // Error event
              if (eventData.error) {
                throw new Error(eventData.error)
              }

            } catch (parseError) {
              console.error('Error parsing SSE data:', parseError)
            }
          }
        }
      }

      // Add assistant message with final result
      if (finalResult) {
        const assistantMsg: Message = {
          id: messageId || `msg-${Date.now()}`,
          role: 'assistant',
          content: finalResult.response,
          sources: finalResult.sources || [],
          confidence_score: finalResult.confidence_score,
          low_confidence_warning: finalResult.low_confidence_warning || false,
          created_at: new Date().toISOString(),
        }

        setMessages((prev) => [...prev.filter((m) => m.id !== tempUserMsg.id), tempUserMsg, assistantMsg])

        showSnackbar(
          finalResult.low_confidence_warning
            ? `⚠️ Low Confidence Response - No relevant knowledge base content found (${(finalResult.confidence_score * 100).toFixed(1)}% confidence). Response is from AI without document context.`
            : `Response Generated - Confidence: ${getConfidenceLabel(finalResult.confidence_score)} (${(finalResult.confidence_score * 100).toFixed(1)}%)`,
          finalResult.low_confidence_warning ? 'warning' : 'success'
        )

        // Reload conversations if new
        if (conversationId && !currentConversation) {
          await loadConversations()
        }
      }

    } catch (error: any) {
      if (error.name === 'AbortError') {
        showSnackbar('Message sending was cancelled', 'info')
      } else {
        showSnackbar(error.message || 'Failed to send message', 'error')
      }
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id))
    } finally {
      setLoading(false)
      setStreamingState({
        isStreaming: false,
        currentAgent: null,
        agentStatuses: [],
        accumulatedResponse: ''
      })
      abortControllerRef.current = null
    }
  }

  const handleSendMessage = handleSendMessageStream

  const handleNewConversation = () => {
    setCurrentConversation(null)
    setMessages([])
  }

  const handleDeleteConversation = async (conversationId: string, event: React.MouseEvent) => {
    event.stopPropagation() // Prevent selecting the conversation when clicking delete

    if (!confirm('Are you sure you want to delete this conversation?')) {
      return
    }

    try {
      await chatAPI.deleteConversation(conversationId)

      showSnackbar('Conversation deleted successfully', 'success')

      // If the deleted conversation was the current one, clear it
      if (currentConversation === conversationId) {
        setCurrentConversation(null)
        setMessages([])
      }

      // Reload conversations list
      await loadConversations()
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to delete conversation', 'error')
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploadingDoc(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('provider', provider)

    try {
      await documentsAPI.upload(formData, provider)
      showSnackbar(`${file.name} has been processed and added to the knowledge base`, 'success')
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to upload document', 'error')
    } finally {
      setUploadingDoc(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper sx={{ borderRadius: 0, borderBottom: 1, borderColor: 'divider', zIndex: (theme) => theme.zIndex.drawer + 1 }} elevation={1}>
        <Container maxWidth="xl">
          <Box sx={{ py: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <IconButton
                onClick={() => setDrawerOpen(!drawerOpen)}
              >
                {drawerOpen ? <CloseIcon /> : <MenuIcon />}
              </IconButton>
              <Button
                variant="text"
                startIcon={<HomeIcon />}
                onClick={() => router.push('/dashboard')}
              >
                Dashboard
              </Button>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <MessageSquareIcon color="primary" />
                <Typography variant="h5" fontWeight="bold">
                  RAG Chat
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <FormControl size="small" sx={{ minWidth: 140 }}>
                <InputLabel>LLM Provider</InputLabel>
                <Select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  disabled={loading}
                  label="LLM Provider"
                >
                  <MenuItem value="custom">Custom API</MenuItem>
                  <MenuItem value="ollama">Ollama</MenuItem>
                </Select>
              </FormControl>
              <ThemeToggle />
              <Button
                variant="contained"
                startIcon={uploadingDoc ? <CircularProgress size={20} color="inherit" /> : <UploadIcon />}
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadingDoc}
              >
                Upload Doc
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                style={{ display: 'none' }}
                accept=".pdf,.txt,.csv,.docx"
                onChange={handleFileUpload}
              />
            </Box>
          </Box>
        </Container>
      </Paper>

      <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 }, flex: 1, display: 'flex', overflow: 'hidden' }}>
        <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden', gap: { xs: 0, md: 3 }, width: '100%' }}>
          {/* Sidebar - Conversations */}
          <Drawer
            variant={drawerOpen ? "persistent" : "temporary"}
            anchor="left"
            open={drawerOpen}
            onClose={() => setDrawerOpen(false)}
            sx={{
              width: { xs: 280, sm: 320 },
              flexShrink: 0,
              '& .MuiDrawer-paper': {
                width: { xs: 280, sm: 320 },
                boxSizing: 'border-box',
                position: 'relative',
                height: 'calc(100vh - 140px)',
                border: 'none',
                bgcolor: 'background.default',
            },
          }}
        >
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" fontWeight="bold">Conversations</Typography>
            <Tooltip title="New conversation (⌘K)">
              <Button
                variant="contained"
                size="small"
                startIcon={<AddIcon />}
                onClick={handleNewConversation}
              >
                New
              </Button>
            </Tooltip>
          </Box>
          <Box sx={{ px: 2, pb: 2 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} fontSize="small" />,
              }}
            />
          </Box>
          <Divider />
          <Box sx={{ overflow: 'auto', flexGrow: 1 }}>
            {loadingConversations ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : filteredConversations.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4, px: 2, color: 'text.secondary' }}>
                <Typography variant="body2">
                  {searchQuery ? 'No conversations found' : 'No conversations yet'}
                </Typography>
                {!searchQuery && (
                  <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                    Start chatting to create one
                  </Typography>
                )}
              </Box>
            ) : (
              <List sx={{ py: 0 }}>
                {filteredConversations.map((conv) => (
                  <ListItem
                    key={conv.id}
                    disablePadding
                    secondaryAction={
                      <IconButton
                        edge="end"
                        onClick={(e) => handleDeleteConversation(conv.id, e)}
                        size="small"
                        sx={{ opacity: 0.7, '&:hover': { opacity: 1 } }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    }
                  >
                    <ListItemButton
                      selected={currentConversation === conv.id}
                      onClick={() => setCurrentConversation(conv.id)}
                      sx={{
                        borderRadius: 2,
                        mx: 1,
                        my: 0.5,
                        '&.Mui-selected': {
                          bgcolor: 'primary.light',
                          '&:hover': {
                            bgcolor: 'primary.light',
                          }
                        }
                      }}
                    >
                      <ListItemText
                        primary={conv.title}
                        secondary={`${conv.message_count} messages • ${formatDate(conv.updated_at)}`}
                        primaryTypographyProps={{ noWrap: true, fontWeight: currentConversation === conv.id ? 600 : 400 }}
                        secondaryTypographyProps={{
                          variant: 'caption',
                          fontSize: '0.7rem',
                          sx: {
                            color: currentConversation === conv.id ? 'rgba(255, 255, 255, 0.9)' : 'text.secondary',
                            fontWeight: 500
                          }
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        </Drawer>

        {/* Main Chat Area */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            display: 'flex',
            flexDirection: 'column',
            height: 'calc(100vh - 140px)',
            overflow: 'hidden',
          }}
        >
          {/* Messages */}
          <Paper
            elevation={2}
            sx={{
              flexGrow: 1,
              mb: 2,
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <Box
              sx={{
                flexGrow: 1,
                overflow: 'auto',
                p: 3,
              }}
            >
              {messages.length === 0 ? (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    textAlign: 'center',
                  }}
                >
                  <BrainIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Start a Conversation
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 500 }}>
                    Ask questions about your documents using RAG and multi-agent AI system.
                    Responses include source citations and confidence scores.
                  </Typography>
                </Box>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  {messages.map((message) => (
                    <Box
                      key={message.id}
                      sx={{
                        display: 'flex',
                        gap: 2,
                        flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                        alignItems: 'flex-start',
                        ml: message.role === 'user' ? 0 : 2,
                        mr: message.role === 'user' ? 2 : 0,
                      }}
                    >
                      {/* Avatar */}
                      <Avatar
                        sx={{
                          bgcolor: message.role === 'user' ? 'primary.main' : 'success.main',
                          width: 40,
                          height: 40,
                          color: 'white',
                        }}
                      >
                        {message.role === 'user' ? <PersonIcon /> : <SmartToyIcon />}
                      </Avatar>

                      {/* Message Content */}
                      <Box sx={{ flexGrow: 1, maxWidth: { xs: 'calc(100% - 56px)', md: '50%' } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                          <Typography variant="subtitle2" fontWeight="bold">
                            {message.role === 'user' ? 'You' : 'AI Assistant'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatDate(message.created_at)}
                          </Typography>
                          {message.confidence_score !== undefined && (
                            <Tooltip title={`Confidence: ${(message.confidence_score * 100).toFixed(1)}%`}>
                              <Chip
                                icon={<VerifiedIcon sx={{ fontSize: 14 }} />}
                                label={getConfidenceLabel(message.confidence_score)}
                                size="small"
                                color={message.confidence_score >= 0.7 ? 'success' : 'warning'}
                                variant="filled"
                                sx={{ height: 22, fontSize: '0.75rem', fontWeight: 500 }}
                              />
                            </Tooltip>
                          )}
                          {message.low_confidence_warning && (
                            <Tooltip title="Response may not be well-grounded in the knowledge base">
                              <Chip
                                icon={<WarningIcon sx={{ fontSize: 14 }} />}
                                label="Low Match"
                                size="small"
                                color="warning"
                                variant="filled"
                                sx={{ height: 22, fontSize: '0.75rem', fontWeight: 500 }}
                              />
                            </Tooltip>
                          )}
                        </Box>
                        <Paper
                          elevation={message.role === 'user' ? 0 : 1}
                          sx={{
                            p: 2.5,
                            bgcolor: message.role === 'user' ? 'primary.main' : 'background.paper',
                            color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                            border: message.role === 'user' ? 'none' : 1,
                            borderColor: 'divider',
                            borderRadius: 3,
                          }}
                        >
                          <Box sx={{
                            '& p': { m: 0, lineHeight: 1.7, fontSize: '0.95rem' },
                            '& pre': { overflowX: 'auto', borderRadius: 1, p: 1, bgcolor: message.role === 'user' ? 'rgba(0,0,0,0.1)' : 'background.default' },
                            '& code': { fontSize: '0.9rem' }
                          }}>
                            <ReactMarkdown>{message.content}</ReactMarkdown>
                          </Box>

                          {/* Inline Source Chips */}
                          {message.sources && message.sources.length > 0 && (
                            <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                              {message.sources.map((source, idx) => (
                                <Tooltip
                                  key={idx}
                                  title={
                                    <Box>
                                      <Typography variant="caption" fontWeight="bold" display="block">
                                        {source.metadata?.document_title || `Source ${source.source_number}`}
                                      </Typography>
                                      <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                                        {source.content.substring(0, 150)}...
                                      </Typography>
                                      <Typography variant="caption" display="block" sx={{ mt: 0.5, color: 'primary.light' }}>
                                        Match: {(source.similarity * 100).toFixed(1)}%
                                      </Typography>
                                    </Box>
                                  }
                                  arrow
                                >
                                  <Chip
                                    icon={<FileTextIcon sx={{ fontSize: 14 }} />}
                                    label={`Source ${source.source_number}`}
                                    size="small"
                                    variant={message.role === 'user' ? 'filled' : 'outlined'}
                                    sx={{
                                      height: 24,
                                      fontSize: '0.75rem',
                                      cursor: 'pointer',
                                      bgcolor: message.role === 'user' ? 'rgba(255, 255, 255, 0.2)' : 'background.default',
                                      color: message.role === 'user' ? 'white' : 'text.primary',
                                      borderColor: message.role === 'user' ? 'rgba(255, 255, 255, 0.4)' : 'divider',
                                      '& .MuiChip-icon': {
                                        color: message.role === 'user' ? 'white' : 'inherit',
                                      },
                                      '&:hover': {
                                        bgcolor: message.role === 'user' ? 'rgba(255, 255, 255, 0.3)' : 'action.hover',
                                      }
                                    }}
                                  />
                                </Tooltip>
                              ))}
                            </Box>
                          )}
                        </Paper>
                      </Box>
                    </Box>
                  ))}
                  {streamingState.isStreaming && (
                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start', ml: 2 }}>
                      {/* Avatar */}
                      <Avatar sx={{ bgcolor: 'success.main', width: 40, height: 40, color: 'white' }}>
                        <SmartToyIcon />
                      </Avatar>

                      {/* Streaming Content */}
                      <Box sx={{ flexGrow: 1, maxWidth: { xs: 'calc(100% - 56px)', md: '50%' } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                          <Typography variant="subtitle2" fontWeight="bold">
                            AI Assistant
                          </Typography>
                          <Chip
                            icon={<CircularProgress size={12} color="inherit" />}
                            label="Processing"
                            size="small"
                            color="primary"
                            sx={{ height: 22, fontSize: '0.75rem' }}
                          />
                        </Box>
                        <Paper
                          elevation={1}
                          sx={{
                            p: 2,
                            bgcolor: 'background.paper',
                            border: 1,
                            borderColor: 'divider',
                            borderRadius: 3,
                          }}
                        >
                          {/* Compact Agent Stepper */}
                          <Box sx={{ mb: 2 }}>
                            <Stepper activeStep={streamingState.agentStatuses.length} alternativeLabel sx={{ pt: 1, pb: 0 }}>
                              {['Research', 'Generate', 'Verify', 'Explain'].map((label, index) => {
                                const agentNames = ['ResearchAgent', 'RAGGenerator', 'GroundingAgent', 'ExplainabilityAgent']
                                const agentStatus = streamingState.agentStatuses.find(s => s.agent === agentNames[index])
                                const isActive = streamingState.currentAgent === agentNames[index]
                                const isCompleted = agentStatus?.status === 'completed'

                                return (
                                  <Step key={label} completed={isCompleted} active={isActive}>
                                    <StepLabel
                                      StepIconProps={{
                                        sx: {
                                          fontSize: { xs: 20, sm: 28 },
                                          color: isCompleted ? 'success.main' : isActive ? 'primary.main' : 'action.disabled'
                                        }
                                      }}
                                    >
                                      <Typography variant="caption" sx={{ display: { xs: 'none', sm: 'block' } }}>
                                        {label}
                                      </Typography>
                                    </StepLabel>
                                  </Step>
                                )
                              })}
                            </Stepper>
                          </Box>

                          {/* Preview of Response */}
                          {streamingState.accumulatedResponse && (
                            <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                              <Box sx={{
                                '& p': { m: 0, lineHeight: 1.6 },
                                '& pre': { overflowX: 'auto', borderRadius: 1, p: 1 },
                                opacity: 0.8,
                                fontStyle: 'italic'
                              }}>
                                <ReactMarkdown>
                                  {streamingState.accumulatedResponse.substring(0, 300) +
                                    (streamingState.accumulatedResponse.length > 300 ? '...' : '')}
                                </ReactMarkdown>
                              </Box>
                            </Box>
                          )}
                        </Paper>
                      </Box>
                    </Box>
                  )}
                  {loading && !streamingState.isStreaming && (
                    <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                      <Paper elevation={1} sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CircularProgress size={16} />
                        <Typography variant="body2">AI is thinking...</Typography>
                      </Paper>
                    </Box>
                  )}
                  <div ref={messagesEndRef} />
                </Box>
              )}
            </Box>
          </Paper>

          {/* Input Area */}
          <Paper
            elevation={3}
            sx={{
              p: { xs: 2, sm: 2.5 },
              borderRadius: 3,
              border: 1,
              borderColor: 'divider',
            }}
          >
            <Box sx={{ display: 'flex', gap: { xs: 1, sm: 2 }, alignItems: 'flex-end' }}>
              <TextField
                fullWidth
                multiline
                maxRows={4}
                placeholder="Ask a question about your documents..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSendMessage()
                  }
                }}
                disabled={loading}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    bgcolor: 'background.paper',
                  }
                }}
              />
              <Button
                variant="contained"
                onClick={handleSendMessage}
                disabled={loading || !input.trim()}
                endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
                sx={{
                  minWidth: { xs: 80, sm: 120 },
                  height: 56,
                  borderRadius: 2,
                  textTransform: 'none',
                  fontSize: '1rem',
                  fontWeight: 600,
                  boxShadow: 2,
                  '&:hover': {
                    boxShadow: 4,
                  },
                }}
              >
                <Box sx={{ display: { xs: 'none', sm: 'block' } }}>Send</Box>
              </Button>
            </Box>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ mt: 1, display: 'block', textAlign: 'center' }}
            >
              Press Enter to send, Shift+Enter for new line • ⌘K for new conversation
            </Typography>
          </Paper>
        </Box>
      </Box>
      </Container>
    </Box>
  )
}
