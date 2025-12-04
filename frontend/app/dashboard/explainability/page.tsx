'use client'

import { useState, useEffect } from 'react'
import { explainabilityAPI, chatAPI } from '@/lib/api'
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Chip,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Paper,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
} from '@mui/material'
import {
  Psychology as BrainIcon,
  TrendingUp as TrendingUpIcon,
  Description as FileTextIcon,
  CheckCircle as CheckCircleIcon,
  Error as AlertCircleIcon,
  Home as HomeIcon,
  Visibility as EyeIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material'
import { formatDate, getConfidenceColor, getConfidenceLabel } from '@/lib/utils'
import { useRouter } from 'next/navigation'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { useSnackbar } from '@/components/SnackbarProvider'
import { ThemeToggle } from '@/components/ThemeToggle'

interface ExplanationData {
  message_id: string
  conversation_id: string
  query: string
  response: string
  confidence_score: number
  reasoning_chain: string[]
  sources: any[]
  grounding_evidence: any[]
  agent_decisions: any[]
  created_at: string
}

interface AgentLog {
  id: string
  agent_name: string
  action: string
  status: string
  execution_time: number
  result_summary: string
  created_at: string
}

export default function ExplainabilityPage() {
  const { showSnackbar } = useSnackbar()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [conversations, setConversations] = useState<any[]>([])
  const [selectedConversation, setSelectedConversation] = useState<string>('')
  const [explanations, setExplanations] = useState<ExplanationData[]>([])
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([])
  const [selectedExplanation, setSelectedExplanation] = useState<ExplanationData | null>(null)
  const [activeTab, setActiveTab] = useState(0)

  useEffect(() => {
    loadConversations()
    loadAgentLogs()
  }, [])

  useEffect(() => {
    if (selectedConversation) {
      loadExplanations(selectedConversation)
    }
  }, [selectedConversation])

  const loadConversations = async () => {
    try {
      const response = await chatAPI.getConversations()
      setConversations(response.data)
      if (response.data.length > 0) {
        setSelectedConversation(response.data[0].id)
      }
    } catch (error) {
      console.error('Failed to load conversations:', error)
    }
  }

  const loadExplanations = async (conversationId: string) => {
    try {
      setLoading(true)
      const response = await explainabilityAPI.getExplanations(conversationId)
      setExplanations(response.data)
      if (response.data.length > 0) {
        setSelectedExplanation(response.data[0])
      }
    } catch (error: any) {
      showSnackbar('Failed to load explanations', 'error')
    } finally {
      setLoading(false)
    }
  }

  const loadAgentLogs = async () => {
    try {
      const response = await explainabilityAPI.getAgentLogs()
      setAgentLogs(response.data)
    } catch (error) {
      console.error('Failed to load agent logs:', error)
    }
  }

  const confidenceData = explanations.map((exp, idx) => ({
    name: `Q${idx + 1}`,
    confidence: (exp.confidence_score * 100).toFixed(1),
    query: exp.query.substring(0, 30) + '...',
  }))

  const agentPerformanceData = agentLogs.reduce((acc: any[], log) => {
    const existing = acc.find((a) => a.name === log.agent_name)
    if (existing) {
      existing.executions += 1
      existing.avgTime = (existing.avgTime + log.execution_time) / 2
      if (log.status === 'success') existing.success += 1
      if (log.status === 'failed') existing.failed += 1
    } else {
      acc.push({
        name: log.agent_name,
        executions: 1,
        avgTime: log.execution_time,
        success: log.status === 'success' ? 1 : 0,
        failed: log.status === 'failed' ? 1 : 0,
      })
    }
    return acc
  }, [])

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper elevation={0} sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Container maxWidth="xl">
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 2, flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<HomeIcon />}
                onClick={() => router.push('/dashboard')}
              >
                Dashboard
              </Button>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <EyeIcon color="primary" sx={{ fontSize: 32 }} />
                <Typography variant="h5" sx={{ fontWeight: 700 }}>
                  Explainability Dashboard
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <ThemeToggle />
              <FormControl sx={{ minWidth: 250 }} size="small">
                <InputLabel>Conversation</InputLabel>
                <Select
                  value={selectedConversation}
                  label="Conversation"
                  onChange={(e) => setSelectedConversation(e.target.value)}
                >
                  {conversations.map((conv) => (
                    <MenuItem key={conv.id} value={conv.id}>
                      {conv.title}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          </Box>
        </Container>
      </Paper>

      <Container maxWidth="xl">
        {/* Stats Cards */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: 'repeat(4, 1fr)' }, gap: 2, mb: 4 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Total Queries
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {explanations.length}
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Avg Confidence
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700, color: 'success.main' }}>
                {explanations.length > 0
                  ? (
                      (explanations.reduce((sum, e) => sum + e.confidence_score, 0) /
                        explanations.length) *
                      100
                    ).toFixed(1) + '%'
                  : 'N/A'}
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Agent Executions
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {agentLogs.length}
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Success Rate
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
                {agentLogs.length > 0
                  ? (
                      (agentLogs.filter((l) => l.status === 'success').length / agentLogs.length) *
                      100
                    ).toFixed(1) + '%'
                  : 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Box>

        <Paper sx={{ mb: 3 }}>
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            variant="fullWidth"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="AI Insights" />
            <Tab label="Confidence Analysis" />
            <Tab label="Agent Performance" />
            <Tab label="Reasoning Chains" />
          </Tabs>
        </Paper>

        {/* AI Insights Tab */}
        {activeTab === 0 && (
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3 }}>
            {/* Query List */}
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 1 }}>
                  Query History
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Click to view detailed explanation
                </Typography>
                {loading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                    <CircularProgress />
                  </Box>
                ) : explanations.length === 0 ? (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography color="text.secondary">No explanations available</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      Start chatting to generate insights
                    </Typography>
                  </Box>
                ) : (
                  <Box sx={{ maxHeight: 500, overflow: 'auto' }}>
                    <List>
                      {explanations.map((exp) => (
                        <ListItem
                          key={exp.message_id}
                          onClick={() => setSelectedExplanation(exp)}
                          sx={{
                            cursor: 'pointer',
                            borderRadius: 1,
                            mb: 1,
                            border: 1,
                            borderColor: selectedExplanation?.message_id === exp.message_id ? 'primary.main' : 'divider',
                            bgcolor: selectedExplanation?.message_id === exp.message_id ? 'action.selected' : 'transparent',
                            '&:hover': { bgcolor: 'action.hover' },
                          }}
                        >
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                                <Chip
                                  label={getConfidenceLabel(exp.confidence_score)}
                                  size="small"
                                  color={exp.confidence_score >= 0.8 ? 'success' : exp.confidence_score >= 0.6 ? 'warning' : 'error'}
                                />
                                <Typography variant="caption" color="text.secondary">
                                  {formatDate(exp.created_at)}
                                </Typography>
                              </Box>
                            }
                            secondary={
                              <>
                                <Typography variant="body2" sx={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                  {exp.query}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {exp.sources.length} sources • {exp.reasoning_chain.length} reasoning steps
                                </Typography>
                              </>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </CardContent>
            </Card>

            {/* Selected Explanation Details */}
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 1 }}>
                  Detailed Explanation
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Understanding how the AI arrived at this answer
                </Typography>
                {selectedExplanation ? (
                  <Box sx={{ maxHeight: 500, overflow: 'auto' }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                      {/* Query */}
                      <Box>
                        <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, fontWeight: 600 }}>
                          <BrainIcon fontSize="small" />
                          Query
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 1.5, bgcolor: 'action.hover' }}>
                          <Typography variant="body2">{selectedExplanation.query}</Typography>
                        </Paper>
                      </Box>

                      {/* Confidence Score */}
                      <Box>
                        <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, fontWeight: 600 }}>
                          <TrendingUpIcon fontSize="small" />
                          Confidence Score
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ flex: 1, position: 'relative', height: 8, bgcolor: 'action.hover', borderRadius: 1, overflow: 'hidden' }}>
                            <Box
                              sx={{
                                position: 'absolute',
                                left: 0,
                                top: 0,
                                bottom: 0,
                                width: `${selectedExplanation.confidence_score * 100}%`,
                                bgcolor: selectedExplanation.confidence_score >= 0.8 ? 'success.main' : selectedExplanation.confidence_score >= 0.6 ? 'warning.main' : 'error.main',
                              }}
                            />
                          </Box>
                          <Typography variant="body2" sx={{ fontWeight: 600, minWidth: 45 }}>
                            {(selectedExplanation.confidence_score * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                      </Box>

                      {/* Sources */}
                      <Box>
                        <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, fontWeight: 600 }}>
                          <FileTextIcon fontSize="small" />
                          Sources ({selectedExplanation.sources.length})
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                          {selectedExplanation.sources.map((source, idx) => (
                            <Paper key={idx} variant="outlined" sx={{ p: 1.5 }}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                                <Typography variant="caption" sx={{ fontWeight: 600 }}>
                                  Source {source.source_number}
                                </Typography>
                                <Chip label={`${(source.similarity * 100).toFixed(1)}%`} size="small" />
                              </Box>
                              <Typography variant="caption" color="text.secondary">
                                {source.content}
                              </Typography>
                            </Paper>
                          ))}
                        </Box>
                      </Box>

                      {/* Grounding Evidence */}
                      {selectedExplanation.grounding_evidence.length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, fontWeight: 600 }}>
                            <CheckCircleIcon fontSize="small" color="success" />
                            Grounding Evidence
                          </Typography>
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            {selectedExplanation.grounding_evidence.map((evidence: any, idx) => (
                              <Paper key={idx} variant="outlined" sx={{ p: 1.5, bgcolor: 'success.50', borderColor: 'success.light' }}>
                                <Typography variant="caption" sx={{ fontWeight: 600, display: 'block', mb: 0.5 }}>
                                  {evidence.statement}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  Verified: {evidence.is_grounded ? 'Yes' : 'No'} (
                                  {(evidence.confidence * 100).toFixed(1)}%)
                                </Typography>
                              </Paper>
                            ))}
                          </Box>
                        </Box>
                      )}
                    </Box>
                  </Box>
                ) : (
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 500, textAlign: 'center' }}>
                    <BrainIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                    <Typography color="text.secondary">Select a query to view details</Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        )}

        {/* Confidence Analysis Tab */}
        {activeTab === 1 && (
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1 }}>
                Confidence Score Trend
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Track confidence levels across queries to identify patterns
              </Typography>
              {confidenceData.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={confidenceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          return (
                            <Paper sx={{ p: 1.5, boxShadow: 3 }}>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                {payload[0].payload.query}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                Confidence: {payload[0].value}%
                              </Typography>
                            </Paper>
                          )
                        }
                        return null
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="confidence"
                      stroke="#10b981"
                      strokeWidth={2}
                      name="Confidence %"
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 400 }}>
                  <Typography color="text.secondary">No data available</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        )}

        {/* Agent Performance Tab */}
        {activeTab === 2 && (
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 1 }}>
                  Agent Execution Stats
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Performance metrics for each agent
                </Typography>
                {agentPerformanceData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={agentPerformanceData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="success" fill="#10b981" name="Success" />
                      <Bar dataKey="failed" fill="#ef4444" name="Failed" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 300 }}>
                    <Typography color="text.secondary">No agent data available</Typography>
                  </Box>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 1 }}>
                  Recent Agent Logs
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Latest agent execution history
                </Typography>
                <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                  <List>
                    {agentLogs.slice(0, 20).map((log) => (
                      <ListItem key={log.id} sx={{ p: 1.5, mb: 1, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                {log.agent_name}
                              </Typography>
                              <Chip
                                label={log.status}
                                size="small"
                                color={log.status === 'success' ? 'success' : 'error'}
                              />
                            </Box>
                          }
                          secondary={
                            <>
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                                {log.action}
                              </Typography>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="caption" color="text.secondary">
                                  {log.execution_time.toFixed(2)}s
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {formatDate(log.created_at)}
                                </Typography>
                              </Box>
                            </>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              </CardContent>
            </Card>
          </Box>
        )}

        {/* Reasoning Chains Tab */}
        {activeTab === 3 && (
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1 }}>
                Reasoning Chain Visualization
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Step-by-step breakdown of AI decision-making process
              </Typography>
              {selectedExplanation ? (
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                    <Typography variant="body2" sx={{ minWidth: 60 }}>Query:</Typography>
                    <FormControl fullWidth size="small">
                      <Select
                        value={selectedExplanation.message_id}
                        onChange={(e) => {
                          const exp = explanations.find((exp) => exp.message_id === e.target.value)
                          if (exp) setSelectedExplanation(exp)
                        }}
                      >
                        {explanations.map((exp) => (
                          <MenuItem key={exp.message_id} value={exp.message_id}>
                            {exp.query}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Box>

                  <Box sx={{ position: 'relative' }}>
                    {selectedExplanation.reasoning_chain.map((step, idx) => (
                      <Box key={idx} sx={{ display: 'flex', gap: 2, mb: 3 }}>
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                          <Box
                            sx={{
                              width: 32,
                              height: 32,
                              borderRadius: '50%',
                              bgcolor: 'primary.main',
                              color: 'primary.contrastText',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontWeight: 600,
                            }}
                          >
                            {idx + 1}
                          </Box>
                          {idx < selectedExplanation.reasoning_chain.length - 1 && (
                            <Box sx={{ width: 2, flex: 1, bgcolor: 'primary.light', my: 1, minHeight: 20 }} />
                          )}
                        </Box>
                        <Box sx={{ flex: 1, pb: 2 }}>
                          <Paper variant="outlined" sx={{ p: 2, bgcolor: 'action.hover' }}>
                            <Typography variant="body2">{step}</Typography>
                          </Paper>
                        </Box>
                      </Box>
                    ))}
                  </Box>

                  {selectedExplanation.agent_decisions.length > 0 && (
                    <Paper sx={{ mt: 3, p: 2, bgcolor: 'info.50', border: 1, borderColor: 'info.light' }}>
                      <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2, fontWeight: 600 }}>
                        <BrainIcon fontSize="small" color="info" />
                        Agent Decisions
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        {selectedExplanation.agent_decisions.map((decision: any, idx) => (
                          <Paper key={idx} variant="outlined" sx={{ p: 1.5, bgcolor: 'background.paper' }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                {decision.agent}
                              </Typography>
                              <Chip label={decision.decision} size="small" />
                            </Box>
                            <Typography variant="body2" color="text.secondary">
                              {decision.reasoning}
                            </Typography>
                          </Paper>
                        ))}
                      </Box>
                    </Paper>
                  )}
                </Box>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 6, textAlign: 'center' }}>
                  <BrainIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography color="text.secondary">Select a query from Insights tab</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        )}
      </Container>
    </Box>
  )
}
