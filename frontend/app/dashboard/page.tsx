'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/components/ui/use-toast'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Brain, FileText, MessageSquare, Settings, Users, BarChart3, LogOut, Code } from 'lucide-react'
import { authAPI } from '@/lib/api'

export default function DashboardPage() {
  const { user, logout, hasPermission, hasRole, refreshUser } = useAuth()
  const router = useRouter()
  const { toast } = useToast()
  const [updatingProvider, setUpdatingProvider] = useState(false)
  const [updatingExplainability, setUpdatingExplainability] = useState(false)

  const features = [
    {
      title: 'Chat',
      description: 'Interact with AI using RAG and multi-agent system',
      icon: MessageSquare,
      href: '/dashboard/chat',
      permission: 'chat:use',
      gradient: 'from-blue-500 to-cyan-500',
    },
    {
      title: 'Documents',
      description: 'Upload and manage knowledge base documents',
      icon: FileText,
      href: '/dashboard/documents',
      permission: 'documents:read',
      gradient: 'from-green-500 to-emerald-500',
    },
    {
      title: 'Explainability',
      description: 'View AI reasoning and confidence scores',
      icon: BarChart3,
      href: '/dashboard/explainability',
      permission: 'explain:view',
      gradient: 'from-purple-500 to-pink-500',
    },
    {
      title: 'Utilities',
      description: 'Tables, forms, charts and other UI components',
      icon: Code,
      href: '/dashboard/utilities',
      gradient: 'from-orange-500 to-red-500',
    },
    {
      title: 'Admin',
      description: 'Manage users, roles, and system settings',
      icon: Users,
      href: '/dashboard/admin',
      role: 'admin',
      gradient: 'from-red-500 to-orange-500',
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
      toast({
        title: 'Provider Updated',
        description: `LLM provider changed to ${value}`,
      })
    } catch (error: any) {
      toast({
        title: 'Update Failed',
        description: error.response?.data?.detail || 'Failed to update provider',
        variant: 'destructive',
      })
    } finally {
      setUpdatingProvider(false)
    }
  }

  const handleUpdateExplainability = async (value: string) => {
    setUpdatingExplainability(true)
    try {
      await authAPI.updateProfile({ explainability_level: value })
      await refreshUser()
      toast({
        title: 'Explainability Updated',
        description: `Detail level changed to ${value}`,
      })
    } catch (error: any) {
      toast({
        title: 'Update Failed',
        description: error.response?.data?.detail || 'Failed to update explainability level',
        variant: 'destructive',
      })
    } finally {
      setUpdatingExplainability(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <div className="bg-white dark:bg-gray-950 border-b shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-primary">RAG & Multi-Agent System</h1>
            <p className="text-sm text-muted-foreground">Advanced AI with Explainability</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="font-medium">{user?.full_name || user?.username}</p>
              <p className="text-sm text-muted-foreground capitalize">{user?.roles.join(', ')}</p>
            </div>
            <ThemeToggle />
            <Button variant="outline" size="sm" onClick={logout}>
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">Welcome back!</h2>
          <p className="text-muted-foreground">
            Choose a feature to get started with AI-powered capabilities
          </p>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accessibleFeatures.map((feature) => {
            const Icon = feature.icon
            return (
              <Card
                key={feature.href}
                className="cursor-pointer hover:shadow-lg transition-shadow"
                onClick={() => router.push(feature.href)}
              >
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <Icon className="h-6 w-6 text-primary" />
                    </div>
                    <CardTitle>{feature.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <CardDescription>{feature.description}</CardDescription>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Info Cards */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">LLM Provider</CardTitle>
            </CardHeader>
            <CardContent>
              <Select
                value={user?.preferred_llm}
                onValueChange={handleUpdateProvider}
                disabled={updatingProvider}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="custom">Custom API</SelectItem>
                  <SelectItem value="ollama">Ollama</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground mt-2">Current selection</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Explainability Level</CardTitle>
            </CardHeader>
            <CardContent>
              <Select
                value={user?.explainability_level}
                onValueChange={handleUpdateExplainability}
                disabled={updatingExplainability}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="basic">Basic</SelectItem>
                  <SelectItem value="detailed">Detailed</SelectItem>
                  <SelectItem value="debug">Debug</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground mt-2">Detail level</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Permissions</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{user?.permissions.length}</p>
              <p className="text-sm text-muted-foreground">Access rights</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
