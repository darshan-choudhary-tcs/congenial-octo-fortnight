'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { documentsAPI } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/components/ui/use-toast'
import { ThemeToggle } from '@/components/ThemeToggle'
import { FileText, Upload, Loader2, Trash2, CheckCircle, AlertCircle, Clock, Home, Globe, User, Info } from 'lucide-react'
import { formatDate, formatFileSize } from '@/lib/utils'
import { useRouter } from 'next/navigation'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'

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
  const { toast } = useToast()
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
      toast({
        title: 'Error',
        description: 'Failed to load documents',
        variant: 'destructive',
      })
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
      // Use appropriate endpoint based on scope
      if (uploadScope === 'global' && isAdmin) {
        await documentsAPI.uploadGlobal(formData, provider)
        toast({
          title: 'Success',
          description: `${file.name} uploaded to global knowledge base`,
        })
      } else {
        await documentsAPI.upload(formData, provider)
        toast({
          title: 'Success',
          description: `${file.name} uploaded and processed successfully`,
        })
      }
      await loadDocuments()
    } catch (error: any) {
      toast({
        title: 'Upload Failed',
        description: error.response?.data?.detail || 'Failed to upload document',
        variant: 'destructive',
      })
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const handleDelete = async (documentId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) return

    try {
      await documentsAPI.delete(documentId, provider)
      toast({
        title: 'Success',
        description: 'Document deleted successfully',
      })
      await loadDocuments()
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete document',
        variant: 'destructive',
      })
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      default:
        return <Clock className="h-4 w-4 text-yellow-600" />
    }
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive'> = {
      completed: 'default',
      processing: 'secondary',
      failed: 'destructive',
      pending: 'secondary',
    }
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>
  }

  const getScopeBadge = (scope?: string) => {
    if (scope === 'global') {
      return (
        <Badge variant="default" className="bg-purple-600 hover:bg-purple-700">
          <Globe className="h-3 w-3 mr-1" />
          Global
        </Badge>
      )
    }
    return (
      <Badge variant="outline">
        <User className="h-3 w-3 mr-1" />
        Personal
      </Badge>
    )
  }

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
              <FileText className="h-6 w-6 text-primary" />
              <h1 className="text-2xl font-bold">Document Management</h1>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Label htmlFor="provider">Vector Store:</Label>
              <Select value={provider} onValueChange={setProvider}>
                <SelectTrigger id="provider" className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="custom">Custom API</SelectItem>
                  <SelectItem value="ollama">Ollama</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {isAdmin && (
              <div className="flex items-center gap-2">
                <Label htmlFor="uploadScope">Upload To:</Label>
                <Select value={uploadScope} onValueChange={(value: 'user' | 'global') => setUploadScope(value)}>
                  <SelectTrigger id="uploadScope" className="w-36">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="user">Personal</SelectItem>
                    <SelectItem value="global">Global KB</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
            <ThemeToggle />
            <div>
              <input
                id="file-upload"
                type="file"
                className="hidden"
                accept=".pdf,.txt,.csv,.docx"
                onChange={handleUpload}
                disabled={uploading}
              />
              <Button asChild disabled={uploading}>
                <label htmlFor="file-upload" className="cursor-pointer">
                  {uploading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      {uploadScope === 'global' && isAdmin ? 'Upload to Global KB' : 'Upload Document'}
                    </>
                  )}
                </label>
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Info Banner for Admins */}
        {isAdmin && (
          <Card className="mb-6 bg-purple-50 dark:bg-purple-950 border-purple-200 dark:border-purple-800">
            <CardContent className="pt-6">
              <div className="flex gap-3">
                <Info className="h-5 w-5 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-purple-900 dark:text-purple-100 mb-1">
                    Global Knowledge Base
                  </h3>
                  <p className="text-sm text-purple-700 dark:text-purple-300">
                    As an admin, you can upload documents to the <strong>Global Knowledge Base</strong> which will be accessible to all users when they search.
                    Use this for company policies, shared resources, or common documentation.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Documents</CardDescription>
              <CardTitle className="text-3xl">{documents.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Personal Docs</CardDescription>
              <CardTitle className="text-3xl text-blue-600">
                {documents.filter((d) => d.scope !== 'global').length}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Global Docs</CardDescription>
              <CardTitle className="text-3xl text-purple-600">
                {documents.filter((d) => d.scope === 'global').length}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Chunks</CardDescription>
              <CardTitle className="text-3xl">
                {documents.reduce((sum, d) => sum + d.num_chunks, 0)}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Size</CardDescription>
              <CardTitle className="text-3xl">
                {formatFileSize(documents.reduce((sum, d) => sum + d.file_size, 0))}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Document List */}
        <Card>
          <CardHeader>
            <CardTitle>Documents</CardTitle>
            <CardDescription>
              {isAdmin
                ? 'Upload to your personal knowledge base or the global knowledge base (shared with all users)'
                : 'Upload PDF, TXT, CSV, or DOCX files to your personal knowledge base. Global documents are shared by admins.'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No documents yet</h3>
                <p className="text-muted-foreground mb-4">
                  Upload your first document to get started
                </p>
              </div>
            ) : (
              <ScrollArea className="h-[600px]">
                <div className="space-y-4">
                  {documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-4 flex-1">
                        <div className="p-3 bg-primary/10 rounded-lg">
                          <FileText className="h-6 w-6 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold truncate">{doc.title}</h3>
                            {getStatusBadge(doc.processing_status)}
                            {getScopeBadge(doc.scope)}
                          </div>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <span className="flex items-center gap-1">
                              {getStatusIcon(doc.processing_status)}
                              {doc.filename}
                            </span>
                            <span>•</span>
                            <span>{doc.file_type.toUpperCase()}</span>
                            <span>•</span>
                            <span>{formatFileSize(doc.file_size)}</span>
                            {doc.num_chunks > 0 && (
                              <>
                                <span>•</span>
                                <span>{doc.num_chunks} chunks</span>
                              </>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">
                            Uploaded {formatDate(doc.uploaded_at)}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(doc.id, doc.filename)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
