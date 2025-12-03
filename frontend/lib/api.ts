import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/auth/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),

  register: (data: { username: string; email: string; password: string; full_name?: string }) =>
    api.post('/auth/register', data),

  getCurrentUser: () => api.get('/auth/me'),

  updateProfile: (data: any) => api.put('/auth/me', data),

  changePassword: (old_password: string, new_password: string) =>
    api.post('/auth/change-password', { old_password, new_password }),
}

// Chat API
export const chatAPI = {
  sendMessage: (data: {
    message: string
    conversation_id?: string
    provider?: string
    include_grounding?: boolean
  }) => api.post('/chat/message', data),

  getConversations: () => api.get('/chat/conversations'),

  getMessages: (conversationId: string) =>
    api.get(`/chat/conversations/${conversationId}/messages`),

  deleteConversation: (conversationId: string) =>
    api.delete(`/chat/conversations/${conversationId}`),
}

// Documents API
export const documentsAPI = {
  upload: (formData: FormData, provider: string = 'custom') => {
    formData.append('provider', provider)
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  uploadGlobal: (formData: FormData, provider: string = 'custom') => {
    formData.append('provider', provider)
    return api.post('/documents/global/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  list: () => api.get('/documents/'),

  get: (documentId: string) => api.get(`/documents/${documentId}`),

  delete: (documentId: string, provider: string = 'custom') =>
    api.delete(`/documents/${documentId}?provider=${provider}`),
}

// Agents API
export const agentsAPI = {
  getStatus: () => api.get('/agents/status'),

  getLogs: (limit: number = 50) => api.get(`/agents/logs?limit=${limit}`),

  getMessageLogs: (messageId: string) => api.get(`/agents/logs/message/${messageId}`),
}

// Explainability API
export const explainabilityAPI = {
  getMessageExplainability: (messageId: string) =>
    api.get(`/explain/message/${messageId}`),

  getConversationConfidence: (conversationId: string) =>
    api.get(`/explain/conversation/${conversationId}/confidence`),

  getExplanations: (conversationId: string) =>
    api.get(`/explain/conversation/${conversationId}`),

  getAgentLogs: (limit: number = 100) => api.get(`/agents/logs?limit=${limit}`),
}

// Admin API
export const adminAPI = {
  listUsers: () => api.get('/admin/users'),
  getUsers: () => api.get('/admin/users'),

  getUser: (userId: string | number) => api.get(`/admin/users/${userId}`),

  createUser: (data: any) => api.post('/admin/users', data),

  updateUser: (userId: string | number, data: any) => api.put(`/admin/users/${userId}`, data),

  deleteUser: (userId: string | number) => api.delete(`/admin/users/${userId}`),

  listRoles: () => api.get('/admin/roles'),
  getRoles: () => api.get('/admin/roles'),

  getStats: () => api.get('/admin/stats'),
  getSystemStats: () => api.get('/admin/stats'),

  getLLMConfig: () => api.get('/admin/llm-config'),
}

export default api
