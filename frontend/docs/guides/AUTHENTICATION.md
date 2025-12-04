# Authentication System Guide

> **Complete guide to authentication, authorization, and security in the frontend application**

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication Flow](#authentication-flow)
- [Token Management](#token-management)
- [Authorization System](#authorization-system)
- [Route Protection](#route-protection)
- [Implementation Details](#implementation-details)
- [Security Considerations](#security-considerations)

---

## Overview

The application uses **JWT (JSON Web Token)** based authentication with role-based access control (RBAC) and permission-based authorization. Authentication state is managed globally through React Context and persisted in browser localStorage.

### Key Components

```mermaid
graph TD
    A[Auth Context Provider] --> B[useAuth Hook]
    B --> C[Login]
    B --> D[Logout]
    B --> E[Register]
    B --> F[Permission Check]

    C --> G[JWT Token]
    G --> H[localStorage]
    G --> I[Axios Interceptor]

    I --> J[API Requests]

    style A fill:#ff9800
    style G fill:#4caf50
    style I fill:#2196f3
```

---

## Authentication Flow

### Complete Login Flow

```mermaid
sequenceDiagram
    participant U as User
    participant L as Login Page
    participant AC as Auth Context
    participant API as Backend API
    participant LS as localStorage
    participant D as Dashboard

    U->>L: Enter credentials
    L->>AC: login(username, password)
    AC->>API: POST /api/v1/auth/login

    alt Success
        API-->>AC: {access_token, token_type}
        AC->>LS: Store JWT token
        AC->>API: GET /api/v1/auth/me
        API-->>AC: User profile with roles/permissions
        AC->>AC: Set user state
        AC-->>L: Login successful
        L->>D: Redirect to /dashboard
    else Failure
        API-->>AC: 401 Unauthorized
        AC-->>L: Show error message
        L->>U: Display "Invalid credentials"
    end
```

### Registration Flow

```mermaid
sequenceDiagram
    participant U as User
    participant R as Register Page
    participant AC as Auth Context
    participant API as Backend API
    participant L as Login Page

    U->>R: Fill registration form
    R->>AC: register(userData)
    AC->>API: POST /api/v1/auth/register

    alt Success
        API-->>AC: User created
        AC-->>R: Registration successful
        R->>L: Redirect to /auth/login
        L->>U: Show "Please login with credentials"
    else Failure (Username exists)
        API-->>AC: 400 Bad Request
        AC-->>R: Error message
        R->>U: Display error
    end
```

### Logout Flow

```mermaid
sequenceDiagram
    participant U as User
    participant D as Dashboard
    participant AC as Auth Context
    participant LS as localStorage
    participant L as Login Page

    U->>D: Click logout
    D->>AC: logout()
    AC->>LS: Remove JWT token
    AC->>AC: Clear user state
    AC->>L: Redirect to /auth/login
    L->>U: Show login form
```

---

## Token Management

### Token Storage

**Location:** Browser `localStorage`
**Key:** `token`
**Format:** JWT (JSON Web Token)

```typescript
// Token structure (decoded)
{
  "sub": "username",           // Subject (username)
  "exp": 1733356800,          // Expiration timestamp
  "iat": 1733270400,          // Issued at timestamp
  "user_id": 123,             // User ID
  "roles": ["admin"],         // User roles
  "permissions": [            // User permissions
    "chat:use",
    "documents:create"
  ]
}
```

### Token Lifecycle

```mermaid
stateDiagram-v2
    [*] --> NotAuthenticated
    NotAuthenticated --> Authenticating: Login attempt
    Authenticating --> Authenticated: Token received
    Authenticating --> NotAuthenticated: Login failed

    Authenticated --> TokenValid: Check on each request
    TokenValid --> Authenticated: Valid
    TokenValid --> Expired: Token expired (401)

    Expired --> NotAuthenticated: Auto logout
    Authenticated --> NotAuthenticated: Manual logout

    NotAuthenticated --> [*]
```

### Automatic Token Injection

Axios interceptor automatically adds JWT token to all API requests:

```typescript
// In lib/api.ts
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)
```

### Token Expiration Handling

```mermaid
flowchart TD
    A[API Request] --> B[Backend validates token]
    B --> C{Valid?}

    C -->|Yes| D[Process request]
    C -->|No - Expired| E[Return 401 Unauthorized]

    E --> F[Axios Interceptor catches 401]
    F --> G[Remove token from localStorage]
    G --> H[Clear user state]
    H --> I[Redirect to /auth/login]
    I --> J[Show 'Session expired' message]

    style E fill:#f44336
    style I fill:#ff9800
```

**Implementation:**

```typescript
// Response interceptor for 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/auth/login'
    }
    return Promise.reject(error)
  }
)
```

---

## Authorization System

### Role-Based Access Control (RBAC)

The application implements a three-tier role system:

```mermaid
graph TD
    A[User Roles] --> B[Admin]
    A --> C[Analyst]
    A --> D[Viewer]

    B --> E[All Permissions]
    C --> F[Documents: Read/Write]
    C --> G[Chat: Use]
    C --> H[Explainability: View]

    D --> I[Documents: Read Only]
    D --> J[Conversations: Read Only]

    style B fill:#f44336
    style C fill:#ff9800
    style D fill:#4caf50
```

### Permission Matrix

| Permission | Admin | Analyst | Viewer | Description |
|------------|:-----:|:-------:|:------:|-------------|
| `chat:use` | ✅ | ✅ | ❌ | Access chat interface |
| `documents:read` | ✅ | ✅ | ✅ | View documents |
| `documents:create` | ✅ | ✅ | ❌ | Upload documents |
| `documents:delete` | ✅ | ✅ | ❌ | Delete documents |
| `documents:upload_global` | ✅ | ❌ | ❌ | Upload to global scope |
| `explain:view` | ✅ | ✅ | ❌ | View explainability |
| `admin:access` | ✅ | ❌ | ❌ | Access admin panel |
| `users:manage` | ✅ | ❌ | ❌ | CRUD user operations |
| `system:configure` | ✅ | ❌ | ❌ | System settings |

### Permission Check Flow

```mermaid
flowchart TD
    A[User attempts action] --> B{Authenticated?}
    B -->|No| C[Redirect to login]
    B -->|Yes| D{Has permission?}

    D -->|Yes| E[Allow action]
    D -->|No| F{Has role?}

    F -->|Yes| G[Check role-based access]
    F -->|No| H[Deny access]

    G -->|Authorized| E
    G -->|Not authorized| H

    H --> I[Show 403 Forbidden or hide UI]

    style C fill:#ff9800
    style E fill:#4caf50
    style H fill:#f44336
```

### User Profile Structure

```typescript
interface User {
  id: number
  username: string
  email: string
  full_name: string
  is_active: boolean

  // Authorization
  roles: string[]                    // ['admin', 'analyst']
  permissions: string[]              // ['chat:use', 'documents:create']

  // Preferences
  preferred_llm: 'custom' | 'ollama'
  explainability_level: 'basic' | 'detailed' | 'debug'

  // Metadata
  created_at: string
  last_login: string
}
```

---

## Route Protection

### Protected Route Pattern

All routes under `/dashboard` are protected and require authentication:

```mermaid
flowchart TD
    A[User navigates to /dashboard/*] --> B[Dashboard Layout]
    B --> C{useAuth hook}
    C --> D{loading?}

    D -->|Yes| E[Show loading spinner]
    D -->|No| F{user exists?}

    F -->|Yes| G[Render dashboard content]
    F -->|No| H[Redirect to /auth/login]

    G --> I{Route requires specific role?}
    I -->|Yes| J{Has required role?}
    I -->|No| K[Show page]

    J -->|Yes| K
    J -->|No| L[Show 403 or redirect]

    style E fill:#2196f3
    style G fill:#4caf50
    style H fill:#ff9800
    style L fill:#f44336
```

### Implementation in Dashboard Layout

**File:** `frontend/app/dashboard/layout.tsx`

```typescript
'use client'

import { useAuth } from '@/lib/auth-context'
import { redirect } from 'next/navigation'

export default function DashboardLayout({ children }) {
  const { user, loading } = useAuth()

  // Show loading state
  if (loading) {
    return <CircularProgress />
  }

  // Redirect if not authenticated
  if (!user) {
    redirect('/auth/login')
  }

  return (
    <Box>
      {/* Sidebar navigation */}
      <Drawer>
        <NavigationMenu user={user} />
      </Drawer>

      {/* Main content */}
      <Box component="main">
        {children}
      </Box>
    </Box>
  )
}
```

### Admin Route Protection

Admin-only routes implement an additional check:

```mermaid
flowchart TD
    A[User navigates to /dashboard/admin] --> B[Dashboard Layout Check]
    B --> C{Authenticated?}
    C -->|No| D[Redirect to login]
    C -->|Yes| E[Admin Page Component]

    E --> F{useAuth - hasRole}
    F --> G{Is admin?}
    G -->|Yes| H[Render admin panel]
    G -->|No| I[Show 403 Forbidden]

    style D fill:#ff9800
    style H fill:#4caf50
    style I fill:#f44336
```

**Implementation:**

```typescript
// In /dashboard/admin/page.tsx
export default function AdminPage() {
  const { user, hasRole } = useAuth()

  if (!hasRole('admin')) {
    return (
      <Box>
        <Alert severity="error">
          Access Denied: Admin privileges required
        </Alert>
      </Box>
    )
  }

  return <AdminPanelContent />
}
```

### Feature-Level Protection

Individual features can be conditionally rendered based on permissions:

```typescript
// Example: Upload button only for users with create permission
const { hasPermission } = useAuth()

{hasPermission('documents:create') && (
  <Button
    variant="contained"
    onClick={handleUpload}
  >
    Upload Document
  </Button>
)}
```

---

## Implementation Details

### Auth Context Provider

**File:** `frontend/lib/auth-context.tsx`

```mermaid
classDiagram
    class AuthContext {
        +User user
        +boolean loading
        +login(username, password)
        +logout()
        +register(userData)
        +refreshUser()
        +hasPermission(permission)
        +hasRole(role)
    }

    class AuthProvider {
        -useState user
        -useState loading
        -useEffect checkAuth()
        +provides AuthContext
    }

    class useAuth {
        +returns AuthContext
        +throws if outside provider
    }

    AuthProvider --> AuthContext : provides
    useAuth --> AuthContext : consumes
```

### Key Methods

#### 1. Login Method

```typescript
const login = async (username: string, password: string) => {
  try {
    // 1. Get access token
    const response = await authAPI.login(username, password)
    const { access_token } = response.data

    // 2. Store token
    localStorage.setItem('token', access_token)

    // 3. Fetch user profile
    const userResponse = await authAPI.getCurrentUser()
    setUser(userResponse.data)

    // 4. Success!
    return true
  } catch (error) {
    console.error('Login failed:', error)
    throw error
  }
}
```

#### 2. Auto-Check on Mount

```typescript
useEffect(() => {
  const checkAuth = async () => {
    const token = localStorage.getItem('token')

    if (!token) {
      setLoading(false)
      return
    }

    try {
      // Validate token by fetching user
      const response = await authAPI.getCurrentUser()
      setUser(response.data)
    } catch (error) {
      // Token invalid - clean up
      localStorage.removeItem('token')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  checkAuth()
}, [])
```

#### 3. Permission Helpers

```typescript
const hasPermission = (permission: string): boolean => {
  return user?.permissions.includes(permission) ?? false
}

const hasRole = (role: string): boolean => {
  return user?.roles.includes(role) ?? false
}
```

### Usage in Components

```typescript
import { useAuth } from '@/lib/auth-context'

function MyComponent() {
  const { user, login, logout, hasPermission, hasRole } = useAuth()

  // Check authentication
  if (!user) {
    return <LoginPrompt />
  }

  // Check permission
  const canUpload = hasPermission('documents:create')

  // Check role
  const isAdmin = hasRole('admin')

  return (
    <Box>
      <Typography>Welcome, {user.full_name}</Typography>

      {canUpload && <UploadButton />}
      {isAdmin && <AdminControls />}

      <Button onClick={logout}>Logout</Button>
    </Box>
  )
}
```

---

## Security Considerations

### Current Implementation

#### ✅ Implemented Security Measures

1. **JWT Token Authentication**
   - Industry-standard token format
   - Expiration timestamps
   - Backend signature verification

2. **Automatic Token Refresh**
   - Token included in all API requests
   - 401 errors trigger auto-logout

3. **Protected Routes**
   - Authentication check before rendering
   - Automatic redirect to login

4. **Role-Based Access Control**
   - Granular permissions system
   - UI conditionally rendered based on permissions

5. **HTTPS in Production**
   - Encrypted data transmission
   - Prevents token interception

### ⚠️ Security Considerations

#### 1. Token Storage in localStorage

**Current Risk:**
- Vulnerable to XSS (Cross-Site Scripting) attacks
- JavaScript can access localStorage

**Recommended Improvement:**
```mermaid
graph LR
    A[Current: localStorage] --> B[Vulnerable to XSS]
    C[Better: httpOnly Cookies] --> D[Not accessible via JavaScript]
    C --> E[Automatic inclusion in requests]
    C --> F[CSRF protection needed]

    style A fill:#ff9800
    style C fill:#4caf50
```

**Migration Path:**
1. Move token to httpOnly cookie (backend sets it)
2. Implement CSRF token protection
3. Remove `localStorage.getItem('token')` calls
4. Backend automatically reads cookie

#### 2. Token Expiration

**Current:** Tokens expire, but no refresh token mechanism

**Recommendation:** Implement refresh tokens

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API

    C->>A: Request with access token
    A-->>C: 401 Token expired

    C->>A: POST /refresh with refresh token
    A-->>C: New access token

    C->>A: Retry original request
    A-->>C: Success
```

#### 3. Password Security

**Current:** Passwords sent as plain text in HTTPS

**Backend Responsibility:** (Already implemented)
- Passwords hashed with bcrypt
- Salt added for each password
- Never stored in plain text

#### 4. CSRF Protection

**Current:** Not explicitly implemented for state-changing requests

**Recommended:**
```typescript
// Add CSRF token to API client
apiClient.defaults.headers.common['X-CSRF-Token'] = getCsrfToken()
```

#### 5. Content Security Policy (CSP)

**Recommendation:** Add CSP headers in `next.config.js`

```javascript
module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-eval'"
          }
        ]
      }
    ]
  }
}
```

### Security Checklist for Production

- [ ] Move tokens to httpOnly cookies
- [ ] Implement CSRF protection
- [ ] Add rate limiting for auth endpoints
- [ ] Implement account lockout after failed attempts
- [ ] Add 2FA/MFA support
- [ ] Enable Content Security Policy
- [ ] Regular security audits
- [ ] Implement session timeout warnings
- [ ] Add audit logging for security events
- [ ] Scan dependencies for vulnerabilities

---

## Common Scenarios

### Scenario 1: User First Login

```mermaid
sequenceDiagram
    participant U as New User
    participant R as Register Page
    participant L as Login Page
    participant D as Dashboard

    U->>R: Create account
    R->>U: Success - Please login
    U->>L: Enter credentials
    L->>U: Token received
    L->>D: Redirect
    D->>U: Show onboarding
```

### Scenario 2: Session Expiration During Use

```mermaid
sequenceDiagram
    participant U as User
    participant D as Dashboard
    participant A as API
    participant L as Login

    U->>D: Click button
    D->>A: API request
    A-->>D: 401 Expired
    D->>D: Auto logout
    D->>L: Redirect
    L->>U: Session expired message
```

### Scenario 3: Permission Denied

```mermaid
sequenceDiagram
    participant U as Viewer Role
    participant C as Chat Page

    U->>C: Navigate to /dashboard/chat
    C->>C: Check permission 'chat:use'
    C->>C: Viewer has no permission
    C->>U: Show "Access Denied" message
```

---

## Troubleshooting

### Issue: "Session expired" on every page refresh

**Cause:** Token not being retrieved from localStorage

**Solution:**
```typescript
// Check browser console
console.log(localStorage.getItem('token'))

// If null, re-login required
// If exists but fails, token may be corrupted - clear it:
localStorage.removeItem('token')
```

### Issue: User logged in but redirects to login

**Cause:** Auth context loading state or async timing

**Solution:**
```typescript
// Ensure loading is properly handled
if (loading) return <CircularProgress />
if (!user) redirect('/auth/login')
```

### Issue: Permission denied despite having role

**Cause:** Backend permissions not synced with frontend expectations

**Solution:**
```typescript
// Debug user permissions
const { user } = useAuth()
console.log('User permissions:', user?.permissions)
console.log('User roles:', user?.roles)

// Refresh user profile
const { refreshUser } = useAuth()
await refreshUser()
```

---

## Next Steps

- **[API Integration Guide](./API_INTEGRATION.md)** - Learn how auth integrates with API calls
- **[Development Guide](./DEVELOPMENT_GUIDE.md)** - Implement auth in new features
- **[State Management](./STATE_MANAGEMENT.md)** - Understand auth context in the state system

---

**Last Updated:** December 4, 2025
