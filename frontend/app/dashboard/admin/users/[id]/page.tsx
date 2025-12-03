'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { adminAPI } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/components/ui/use-toast'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ArrowLeft, Save, Loader2, User as UserIcon, Mail, Shield, Calendar, Activity } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { useRouter, useParams } from 'next/navigation'

interface User {
  id: string
  username: string
  email: string
  full_name: string
  role: string
  roles?: string[]
  is_active: boolean
  created_at: string
  last_login?: string
  preferred_llm?: string
  explainability_level?: string
}

interface Role {
  id: string
  name: string
  description: string
  permissions: string[]
}

export default function EditUserPage() {
  const { user: currentUser } = useAuth()
  const { toast } = useToast()
  const router = useRouter()
  const params = useParams()
  const userId = params.id as string

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [user, setUser] = useState<User | null>(null)
  const [roles, setRoles] = useState<Role[]>([])
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    role: '',
    is_active: true,
  })

  useEffect(() => {
    // Check admin permission
    if (currentUser && !currentUser.roles.includes('admin')) {
      toast({
        title: 'Access Denied',
        description: 'You do not have permission to access this page',
        variant: 'destructive',
      })
      router.push('/dashboard')
      return
    }

    if (currentUser) {
      loadData()
    }
  }, [currentUser, userId])

  const loadData = async () => {
    try {
      setLoading(true)
      const [userRes, rolesRes] = await Promise.all([
        adminAPI.getUser(userId),
        adminAPI.getRoles(),
      ])

      const userData = userRes.data
      if (!userData) {
        toast({
          title: 'Error',
          description: 'User not found',
          variant: 'destructive',
        })
        router.push('/dashboard/admin')
        return
      }

      setUser(userData)
      setRoles(rolesRes.data)

      // Initialize form data
      setFormData({
        email: userData.email || '',
        full_name: userData.full_name || '',
        role: userData.role || (userData.roles && userData.roles[0]) || 'viewer',
        is_active: userData.is_active ?? true,
      })
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to load user data',
        variant: 'destructive',
      })
      router.push('/dashboard/admin')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      await adminAPI.updateUser(userId, {
        email: formData.email,
        full_name: formData.full_name,
        roles: [formData.role],
        is_active: formData.is_active,
      })

      toast({
        title: 'Success',
        description: 'User updated successfully',
      })

      router.push('/dashboard/admin')
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update user',
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }

  const getRoleBadgeColor = (roleName: string) => {
    switch (roleName) {
      case 'admin':
        return 'bg-red-500'
      case 'analyst':
        return 'bg-blue-500'
      case 'viewer':
        return 'bg-green-500'
      default:
        return 'bg-gray-500'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => router.push('/dashboard/admin')}
          className="mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Admin
        </Button>
        <h1 className="text-3xl font-bold">Edit User</h1>
        <p className="text-muted-foreground">Update user information and permissions</p>
      </div>

      <div className="grid gap-6">
        {/* User Info Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserIcon className="h-5 w-5" />
              User Information
            </CardTitle>
            <CardDescription>
              View and edit basic user information
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Username (Read-only) */}
            <div>
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                value={user.username}
                disabled
                className="bg-muted"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Username cannot be changed
              </p>
            </div>

            {/* Email */}
            <div>
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="pl-10"
                  placeholder="user@example.com"
                />
              </div>
            </div>

            {/* Full Name */}
            <div>
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                placeholder="John Doe"
              />
            </div>
          </CardContent>
        </Card>

        {/* Role & Permissions Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Role & Permissions
            </CardTitle>
            <CardDescription>
              Assign user role and manage access permissions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Role Selection */}
            <div>
              <Label htmlFor="role">Role</Label>
              <Select
                value={formData.role}
                onValueChange={(value) => setFormData({ ...formData, role: value })}
              >
                <SelectTrigger id="role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {roles.map((role) => (
                    <SelectItem key={role.id} value={role.name}>
                      <div className="flex items-center gap-2">
                        <Badge className={getRoleBadgeColor(role.name)}>
                          {role.name}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          - {role.description}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Show permissions for selected role */}
            {formData.role && (
              <div>
                <Label>Permissions</Label>
                <div className="mt-2 p-4 border rounded-lg bg-muted/50">
                  <div className="flex flex-wrap gap-2">
                    {roles
                      .find((r) => r.name === formData.role)
                      ?.permissions.map((permission) => (
                        <Badge key={permission} variant="secondary">
                          {permission}
                        </Badge>
                      ))}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Account Status Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Account Status
            </CardTitle>
            <CardDescription>
              Manage user account status and activity
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Active Status */}
            <div className="flex items-center justify-between">
              <div>
                <Label>Account Status</Label>
                <p className="text-sm text-muted-foreground">
                  {formData.is_active ? 'Active - User can log in' : 'Inactive - User cannot log in'}
                </p>
              </div>
              <Button
                variant={formData.is_active ? 'destructive' : 'default'}
                onClick={() => setFormData({ ...formData, is_active: !formData.is_active })}
              >
                {formData.is_active ? 'Deactivate' : 'Activate'}
              </Button>
            </div>

            {/* Account Info */}
            <div className="space-y-2 pt-4 border-t">
              <div className="flex items-center gap-2 text-sm">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Created:</span>
                <span className="font-medium">{formatDate(user.created_at)}</span>
              </div>
              {user.last_login && (
                <div className="flex items-center gap-2 text-sm">
                  <Activity className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Last Login:</span>
                  <span className="font-medium">{formatDate(user.last_login)}</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <Button
            onClick={handleSave}
            disabled={saving || user.username === currentUser?.username}
            className="flex-1"
          >
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
          <Button
            variant="outline"
            onClick={() => router.push('/dashboard/admin')}
            disabled={saving}
          >
            Cancel
          </Button>
        </div>

        {user.username === currentUser?.username && (
          <p className="text-sm text-amber-600 dark:text-amber-500 text-center">
            ⚠️ You cannot modify your own account. Ask another admin for assistance.
          </p>
        )}
      </div>
    </div>
  )
}
