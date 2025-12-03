'use client'

import { useState, useEffect } from 'react'
import { explainabilityAPI, chatAPI } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/components/ui/use-toast'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Brain, TrendingUp, Loader2, FileText, CheckCircle, AlertCircle, Home, Eye } from 'lucide-react'
import { formatDate, getConfidenceColor, getConfidenceLabel } from '@/lib/utils'
import { useRouter } from 'next/navigation'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'

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
  const { toast } = useToast()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [conversations, setConversations] = useState<any[]>([])
  const [selectedConversation, setSelectedConversation] = useState<string>('')
  const [explanations, setExplanations] = useState<ExplanationData[]>([])
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([])
  const [selectedExplanation, setSelectedExplanation] = useState<ExplanationData | null>(null)

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
      toast({
        title: 'Error',
        description: 'Failed to load explanations',
        variant: 'destructive',
      })
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
              <Eye className="h-6 w-6 text-primary" />
              <h1 className="text-2xl font-bold">Explainability Dashboard</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Label>Conversation:</Label>
            <Select value={selectedConversation} onValueChange={setSelectedConversation}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Select conversation" />
              </SelectTrigger>
              <SelectContent>
                {conversations.map((conv) => (
                  <SelectItem key={conv.id} value={conv.id}>
                    {conv.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Queries</CardDescription>
              <CardTitle className="text-3xl">{explanations.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Avg Confidence</CardDescription>
              <CardTitle className="text-3xl text-green-600">
                {explanations.length > 0
                  ? (
                      (explanations.reduce((sum, e) => sum + e.confidence_score, 0) /
                        explanations.length) *
                      100
                    ).toFixed(1) + '%'
                  : 'N/A'}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Agent Executions</CardDescription>
              <CardTitle className="text-3xl">{agentLogs.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Success Rate</CardDescription>
              <CardTitle className="text-3xl text-blue-600">
                {agentLogs.length > 0
                  ? (
                      (agentLogs.filter((l) => l.status === 'success').length / agentLogs.length) *
                      100
                    ).toFixed(1) + '%'
                  : 'N/A'}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="insights" className="space-y-6">
          <TabsList>
            <TabsTrigger value="insights">AI Insights</TabsTrigger>
            <TabsTrigger value="confidence">Confidence Analysis</TabsTrigger>
            <TabsTrigger value="agents">Agent Performance</TabsTrigger>
            <TabsTrigger value="reasoning">Reasoning Chains</TabsTrigger>
          </TabsList>

          {/* AI Insights Tab */}
          <TabsContent value="insights">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Query List */}
              <Card>
                <CardHeader>
                  <CardTitle>Query History</CardTitle>
                  <CardDescription>Click to view detailed explanation</CardDescription>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="flex justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                    </div>
                  ) : explanations.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <p>No explanations available</p>
                      <p className="text-sm mt-2">Start chatting to generate insights</p>
                    </div>
                  ) : (
                    <ScrollArea className="h-[500px]">
                      <div className="space-y-2">
                        {explanations.map((exp) => (
                          <div
                            key={exp.message_id}
                            className={`p-3 rounded-lg cursor-pointer transition-colors border ${
                              selectedExplanation?.message_id === exp.message_id
                                ? 'bg-primary/10 border-primary'
                                : 'hover:bg-muted'
                            }`}
                            onClick={() => setSelectedExplanation(exp)}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <Badge className={getConfidenceColor(exp.confidence_score)}>
                                {getConfidenceLabel(exp.confidence_score)}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {formatDate(exp.created_at)}
                              </span>
                            </div>
                            <p className="text-sm font-medium truncate">{exp.query}</p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {exp.sources.length} sources • {exp.reasoning_chain.length} reasoning steps
                            </p>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  )}
                </CardContent>
              </Card>

              {/* Selected Explanation Details */}
              <Card>
                <CardHeader>
                  <CardTitle>Detailed Explanation</CardTitle>
                  <CardDescription>
                    Understanding how the AI arrived at this answer
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {selectedExplanation ? (
                    <ScrollArea className="h-[500px]">
                      <div className="space-y-6">
                        {/* Query */}
                        <div>
                          <h4 className="font-semibold mb-2 flex items-center gap-2">
                            <Brain className="h-4 w-4" />
                            Query
                          </h4>
                          <p className="text-sm bg-muted p-3 rounded">{selectedExplanation.query}</p>
                        </div>

                        {/* Confidence Score */}
                        <div>
                          <h4 className="font-semibold mb-2 flex items-center gap-2">
                            <TrendingUp className="h-4 w-4" />
                            Confidence Score
                          </h4>
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                              <div
                                className={`h-full ${getConfidenceColor(selectedExplanation.confidence_score)}`}
                                style={{
                                  width: `${selectedExplanation.confidence_score * 100}%`,
                                }}
                              />
                            </div>
                            <span className="text-sm font-semibold">
                              {(selectedExplanation.confidence_score * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>

                        {/* Sources */}
                        <div>
                          <h4 className="font-semibold mb-2 flex items-center gap-2">
                            <FileText className="h-4 w-4" />
                            Sources ({selectedExplanation.sources.length})
                          </h4>
                          <div className="space-y-2">
                            {selectedExplanation.sources.map((source, idx) => (
                              <div key={idx} className="text-xs p-2 bg-muted rounded border">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="font-semibold">Source {source.source_number}</span>
                                  <Badge variant="secondary">
                                    {(source.similarity * 100).toFixed(1)}%
                                  </Badge>
                                </div>
                                <p className="text-muted-foreground">{source.content}</p>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Grounding Evidence */}
                        {selectedExplanation.grounding_evidence.length > 0 && (
                          <div>
                            <h4 className="font-semibold mb-2 flex items-center gap-2">
                              <CheckCircle className="h-4 w-4 text-green-600" />
                              Grounding Evidence
                            </h4>
                            <div className="space-y-2">
                              {selectedExplanation.grounding_evidence.map((evidence: any, idx) => (
                                <div key={idx} className="text-xs p-2 bg-green-50 rounded border border-green-200">
                                  <p className="font-semibold mb-1">{evidence.statement}</p>
                                  <p className="text-muted-foreground">
                                    Verified: {evidence.is_grounded ? 'Yes' : 'No'} (
                                    {(evidence.confidence * 100).toFixed(1)}%)
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </ScrollArea>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-[500px] text-center">
                      <Brain className="h-12 w-12 text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">Select a query to view details</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Confidence Analysis Tab */}
          <TabsContent value="confidence">
            <Card>
              <CardHeader>
                <CardTitle>Confidence Score Trend</CardTitle>
                <CardDescription>
                  Track confidence levels across queries to identify patterns
                </CardDescription>
              </CardHeader>
              <CardContent>
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
                              <div className="bg-white p-3 border rounded shadow-lg">
                                <p className="text-sm font-semibold">{payload[0].payload.query}</p>
                                <p className="text-sm text-muted-foreground">
                                  Confidence: {payload[0].value}%
                                </p>
                              </div>
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
                  <div className="flex items-center justify-center h-[400px] text-muted-foreground">
                    No data available
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Agent Performance Tab */}
          <TabsContent value="agents">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Agent Execution Stats</CardTitle>
                  <CardDescription>Performance metrics for each agent</CardDescription>
                </CardHeader>
                <CardContent>
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
                    <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                      No agent data available
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recent Agent Logs</CardTitle>
                  <CardDescription>Latest agent execution history</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[300px]">
                    <div className="space-y-2">
                      {agentLogs.slice(0, 20).map((log) => (
                        <div key={log.id} className="p-3 border rounded-lg">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-sm">{log.agent_name}</span>
                            <Badge
                              variant={log.status === 'success' ? 'default' : 'destructive'}
                            >
                              {log.status}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground mb-1">{log.action}</p>
                          <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <span>{log.execution_time.toFixed(2)}s</span>
                            <span>{formatDate(log.created_at)}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Reasoning Chains Tab */}
          <TabsContent value="reasoning">
            <Card>
              <CardHeader>
                <CardTitle>Reasoning Chain Visualization</CardTitle>
                <CardDescription>
                  Step-by-step breakdown of AI decision-making process
                </CardDescription>
              </CardHeader>
              <CardContent>
                {selectedExplanation ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 mb-4">
                      <Label>Query:</Label>
                      <Select
                        value={selectedExplanation.message_id}
                        onValueChange={(id) => {
                          const exp = explanations.find((e) => e.message_id === id)
                          if (exp) setSelectedExplanation(exp)
                        }}
                      >
                        <SelectTrigger className="flex-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {explanations.map((exp) => (
                            <SelectItem key={exp.message_id} value={exp.message_id}>
                              {exp.query}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="relative">
                      {selectedExplanation.reasoning_chain.map((step, idx) => (
                        <div key={idx} className="flex gap-4 mb-6">
                          <div className="flex flex-col items-center">
                            <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold">
                              {idx + 1}
                            </div>
                            {idx < selectedExplanation.reasoning_chain.length - 1 && (
                              <div className="w-0.5 h-full bg-primary/30 my-2" />
                            )}
                          </div>
                          <div className="flex-1 pb-4">
                            <div className="bg-muted p-4 rounded-lg">
                              <p className="text-sm">{step}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {selectedExplanation.agent_decisions.length > 0 && (
                      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <h4 className="font-semibold mb-3 flex items-center gap-2">
                          <Brain className="h-4 w-4 text-blue-600" />
                          Agent Decisions
                        </h4>
                        <div className="space-y-2">
                          {selectedExplanation.agent_decisions.map((decision: any, idx) => (
                            <div key={idx} className="text-sm bg-white p-3 rounded border">
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-semibold">{decision.agent}</span>
                                <Badge variant="secondary">{decision.decision}</Badge>
                              </div>
                              <p className="text-muted-foreground">{decision.reasoning}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <Brain className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">Select a query from Insights tab</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
