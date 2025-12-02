'use client'

import { useState, useEffect, useRef } from 'react'
import { useAuth } from '@/lib/auth-context'
import { chatAPI, documentsAPI } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/components/ui/use-toast'
import { MessageSquare, Send, Loader2, FileText, Brain, TrendingUp, CheckCircle, Upload, Home, Trash2 } from 'lucide-react'
import { formatDate, getConfidenceColor, getConfidenceLabel } from '@/lib/utils'
import ReactMarkdown from 'react-markdown'
import { useRouter } from 'next/navigation'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: any[]
  confidence_score?: number
  created_at: string
}

interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export default function ChatPage() {
  const { user } = useAuth()
  const { toast } = useToast()
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
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

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

  const loadMessages = async (conversationId: string) => {
    try {
      const response = await chatAPI.getMessages(conversationId)
      setMessages(response.data)
    } catch (error) {
      console.error('Failed to load messages:', error)
      toast({
        title: 'Error',
        description: 'Failed to load messages',
        variant: 'destructive',
      })
    }
  }

  const handleSendMessage = async () => {
    if (!input.trim() || loading) return

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

    try {
      const response = await chatAPI.sendMessage({
        message: userMessage,
        conversation_id: currentConversation || undefined,
        provider,
        include_grounding: includeGrounding,
      })

      // Update conversation ID if new
      if (!currentConversation) {
        setCurrentConversation(response.data.conversation_id)
        await loadConversations()
      }

      // Add assistant message
      const assistantMsg: Message = {
        id: response.data.message_id,
        role: 'assistant',
        content: response.data.response,
        sources: response.data.sources,
        confidence_score: response.data.confidence_score,
        created_at: new Date().toISOString(),
      }

      setMessages((prev) => [...prev.filter((m) => m.id !== tempUserMsg.id), tempUserMsg, assistantMsg])

      toast({
        title: 'Response Generated',
        description: `Confidence: ${getConfidenceLabel(response.data.confidence_score)} (${(response.data.confidence_score * 100).toFixed(1)}%)`,
      })
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to send message',
        variant: 'destructive',
      })
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id))
    } finally {
      setLoading(false)
    }
  }

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

      toast({
        title: 'Conversation Deleted',
        description: 'The conversation has been successfully deleted',
      })

      // If the deleted conversation was the current one, clear it
      if (currentConversation === conversationId) {
        setCurrentConversation(null)
        setMessages([])
      }

      // Reload conversations list
      await loadConversations()
    } catch (error: any) {
      toast({
        title: 'Delete Failed',
        description: error.response?.data?.detail || 'Failed to delete conversation',
        variant: 'destructive',
      })
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
      toast({
        title: 'Document Uploaded',
        description: `${file.name} has been processed and added to the knowledge base`,
      })
    } catch (error: any) {
      toast({
        title: 'Upload Failed',
        description: error.response?.data?.detail || 'Failed to upload document',
        variant: 'destructive',
      })
    } finally {
      setUploadingDoc(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard')}>
              <Home className="h-4 w-4 mr-2" />
              Dashboard
            </Button>
            <Separator orientation="vertical" className="h-6" />
            <div className="flex items-center gap-2">
              <MessageSquare className="h-6 w-6 text-primary" />
              <h1 className="text-2xl font-bold">RAG Chat</h1>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Label htmlFor="provider">LLM Provider:</Label>
              <Select value={provider} onValueChange={setProvider} disabled={loading}>
                <SelectTrigger id="provider" className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="custom">Custom API</SelectItem>
                  <SelectItem value="ollama">Ollama</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadingDoc}
            >
              {uploadingDoc ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Upload className="h-4 w-4 mr-2" />
              )}
              Upload Doc
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".pdf,.txt,.csv,.docx"
              onChange={handleFileUpload}
            />
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6 h-[calc(100vh-88px)]">
        <div className="grid grid-cols-12 gap-6 h-full">
          {/* Sidebar - Conversations */}
          <div className="col-span-3">
            <Card className="h-full flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Conversations</span>
                  <Button size="sm" onClick={handleNewConversation}>
                    New
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 p-0">
                <ScrollArea className="h-full">
                  {loadingConversations ? (
                    <div className="flex justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                    </div>
                  ) : conversations.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <p>No conversations yet</p>
                      <p className="text-sm mt-2">Start chatting to create one</p>
                    </div>
                  ) : (
                    <div className="space-y-1 p-4">
                      {conversations.map((conv) => (
                        <div
                          key={conv.id}
                          className={`p-3 rounded-lg cursor-pointer transition-colors group relative ${
                            currentConversation === conv.id
                              ? 'bg-primary text-primary-foreground'
                              : 'hover:bg-muted'
                          }`}
                          onClick={() => setCurrentConversation(conv.id)}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <p className="font-medium truncate">{conv.title}</p>
                              <p className={`text-xs mt-1 ${
                                currentConversation === conv.id ? 'opacity-70' : 'text-muted-foreground'
                              }`}>
                                {conv.message_count} messages • {formatDate(conv.updated_at)}
                              </p>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              className={`h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity ${
                                currentConversation === conv.id
                                  ? 'hover:bg-primary-foreground/20 text-primary-foreground'
                                  : 'hover:bg-destructive hover:text-destructive-foreground'
                              }`}
                              onClick={(e) => handleDeleteConversation(conv.id, e)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </div>

          {/* Main Chat Area */}
          <div className="col-span-9 flex flex-col gap-4 h-full overflow-hidden">
            {/* Messages */}
            <Card className="flex-1 flex flex-col overflow-hidden">
              <CardContent className="flex-1 p-0 overflow-hidden">
                <ScrollArea className="h-full p-6">
                  {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center">
                      <Brain className="h-16 w-16 text-muted-foreground mb-4" />
                      <h3 className="text-lg font-semibold mb-2">Start a Conversation</h3>
                      <p className="text-muted-foreground max-w-md">
                        Ask questions about your documents using RAG and multi-agent AI system.
                        Responses include source citations and confidence scores.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {messages.map((message) => (
                        <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[80%] ${message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'} rounded-lg p-4`}>
                            <div className="flex items-center gap-2 mb-2">
                              <span className="font-semibold text-sm">
                                {message.role === 'user' ? 'You' : 'AI Assistant'}
                              </span>
                              {message.confidence_score !== undefined && (
                                <Badge variant="outline" className={getConfidenceColor(message.confidence_score)}>
                                  {getConfidenceLabel(message.confidence_score)}
                                </Badge>
                              )}
                            </div>
                            <div className="prose prose-sm max-w-none dark:prose-invert">
                              <ReactMarkdown>{message.content}</ReactMarkdown>
                            </div>
                            {message.sources && message.sources.length > 0 && (
                              <div className="mt-4 pt-4 border-t border-border">
                                <Accordion type="single" collapsible>
                                  <AccordionItem value="sources">
                                    <AccordionTrigger className="text-sm">
                                      <div className="flex items-center gap-2">
                                        <FileText className="h-4 w-4" />
                                        Sources ({message.sources.length})
                                      </div>
                                    </AccordionTrigger>
                                    <AccordionContent>
                                      <div className="space-y-2">
                                        {message.sources.map((source, idx) => (
                                          <div key={idx} className="text-xs p-2 bg-background rounded border">
                                            <div className="flex items-center justify-between mb-1">
                                              <span className="font-semibold">Source {source.source_number}</span>
                                              <Badge variant="secondary">
                                                {(source.similarity * 100).toFixed(1)}% match
                                              </Badge>
                                            </div>
                                            <p className="text-muted-foreground">{source.content}</p>
                                            {source.metadata && (
                                              <p className="mt-1 text-muted-foreground">
                                                {source.metadata.document_title}
                                              </p>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    </AccordionContent>
                                  </AccordionItem>
                                </Accordion>
                              </div>
                            )}
                            <p className="text-xs opacity-70 mt-2">{formatDate(message.created_at)}</p>
                          </div>
                        </div>
                      ))}
                      {loading && (
                        <div className="flex justify-start">
                          <div className="bg-muted rounded-lg p-4 flex items-center gap-2">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span className="text-sm">AI is thinking...</span>
                          </div>
                        </div>
                      )}
                      <div ref={messagesEndRef} />
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Input Area */}
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={includeGrounding}
                      onChange={(e) => setIncludeGrounding(e.target.checked)}
                      className="rounded"
                    />
                    <span>Include Grounding Verification</span>
                  </label>
                </div>
                <div className="flex gap-2">
                  <Input
                    placeholder="Ask a question about your documents..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                    disabled={loading}
                    className="flex-1"
                  />
                  <Button onClick={handleSendMessage} disabled={loading || !input.trim()}>
                    {loading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
