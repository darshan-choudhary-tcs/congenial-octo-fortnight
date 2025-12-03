'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from './api'

interface User {
  id: number
  username: string
  email: string
  full_name: string | null
  roles: string[]
  permissions: string[]
  preferred_llm: string
  explainability_level: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  register: (data: any) => Promise<void>
  refreshUser: () => Promise<void>
  hasPermission: (permission: string) => boolean
  hasRole: (role: string) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('token')
      if (token) {
        const response = await authAPI.getCurrentUser()
        setUser(response.data)
      }
    } catch (error) {
      localStorage.removeItem('token')
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    const response = await authAPI.login(username, password)
    localStorage.setItem('token', response.data.access_token)
    await checkAuth()
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
    window.location.href = '/auth/login'
  }

  const register = async (data: any) => {
    const response = await authAPI.register(data)
    // Auto-login after registration
    await login(data.username, data.password)
  }

  const refreshUser = async () => {
    try {
      const response = await authAPI.getCurrentUser()
      setUser(response.data)
    } catch (error) {
      console.error('Failed to refresh user:', error)
    }
  }

  const hasPermission = (permission: string) => {
    return user?.permissions.includes(permission) || false
  }

  const hasRole = (role: string) => {
    return user?.roles.includes(role) || false
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        register,
        refreshUser,
        hasPermission,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
