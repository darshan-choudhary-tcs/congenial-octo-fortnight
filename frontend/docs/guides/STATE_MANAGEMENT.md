# State Management Guide

> **Complete guide to state management patterns, context providers, and data flow**

## 📋 Table of Contents

- [Overview](#overview)
- [State Architecture](#state-architecture)
- [Context Providers](#context-providers)
- [Local Component State](#local-component-state)
- [Data Flow Patterns](#data-flow-patterns)
- [Best Practices](#best-practices)

---

## Overview

The application uses a **minimal state management** approach with React Context for global state and local useState/useEffect for component-specific state. This avoids the complexity of additional libraries while maintaining clean data flow.

### State Layers

```mermaid
graph TD
    A[Application State] --> B[Global State]
    A --> C[Component State]
    A --> D[Server State]

    B --> E[Auth Context]
    B --> F[Theme Context]
    B --> G[Snackbar Store]

    C --> H[Form Inputs]
    C --> I[UI State]
    C --> J[Loading Flags]

    D --> K[API Data]
    D --> L[Cached Responses]

    style B fill:#ff9800
    style C fill:#2196f3
    style D fill:#4caf50
```

---

## State Architecture

### Provider Hierarchy

```mermaid
graph TD
    A[Root Layout] --> B[EmotionCacheProvider]
    B --> C[ThemeProvider]
    C --> D[AuthProvider]
    D --> E[SnackbarProvider]
    E --> F[Page Content]

    F --> G[Dashboard Layout]
    G --> H[Protected Pages]

    style A fill:#1976d2
    style C fill:#9c27b0
    style D fill:#ff9800
    style E fill:#4caf50
```

**Implementation in `app/layout.tsx`:**

```typescript
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <EmotionCacheProvider>
          <ThemeProvider>
            <AuthProvider>
              <SnackbarProvider>
                {children}
              </SnackbarProvider>
            </AuthProvider>
          </ThemeProvider>
        </EmotionCacheProvider>
      </body>
    </html>
  )
}
```

### State Ownership

```mermaid
graph LR
    A[Global State] --> B[Multiple Components]
    C[Component State] --> D[Single Component Tree]
    E[Lifted State] --> F[Parent Component]
    F --> G[Child Props]

    style A fill:#ff9800
    style C fill:#2196f3
    style E fill:#9c27b0
```

---

## Context Providers

### 1. Auth Context

**Purpose:** Manage user authentication state globally

```mermaid
stateDiagram-v2
    [*] --> Loading
    Loading --> Unauthenticated: No token
    Loading --> Authenticated: Valid token

    Unauthenticated --> Authenticating: login()
    Authenticating --> Authenticated: Success
    Authenticating --> Unauthenticated: Failed

    Authenticated --> Unauthenticated: logout()
    Authenticated --> Authenticated: refreshUser()

    Authenticated --> [*]
    Unauthenticated --> [*]
```

**State Structure:**

```typescript
interface AuthContextType {
  // State
  user: User | null
  loading: boolean

  // Actions
  login: (username: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>

  // Utilities
  hasPermission: (permission: string) => boolean
  hasRole: (role: string) => boolean
}
```

**Data Flow:**

```mermaid
sequenceDiagram
    participant C as Component
    participant AC as Auth Context
    participant LS as localStorage
    participant API as Backend

    C->>AC: useAuth()
    AC->>LS: Check token

    alt Token exists
        AC->>API: GET /auth/me
        API-->>AC: User data
        AC->>AC: setUser(data)
    else No token
        AC->>AC: setUser(null)
    end

    AC-->>C: { user, login, logout }
```

**File:** `frontend/lib/auth-context.tsx`

### 2. Theme Context

**Purpose:** Manage light/dark theme preference

```mermaid
stateDiagram-v2
    [*] --> System
    System --> Light: User selects light
    System --> Dark: User selects dark

    Light --> Dark: Toggle
    Light --> System: Set to system

    Dark --> Light: Toggle
    Dark --> System: Set to system

    System --> Light: System preference
    System --> Dark: System preference
```

**State Structure:**

```typescript
interface ThemeContextType {
  mode: 'light' | 'dark' | 'system'
  setMode: (mode: 'light' | 'dark' | 'system') => void
  resolvedTheme: 'light' | 'dark'  // Actual applied theme
}
```

**Theme Resolution:**

```mermaid
flowchart TD
    A[Theme Mode] --> B{Mode Value}
    B -->|light| C[Use Light Theme]
    B -->|dark| D[Use Dark Theme]
    B -->|system| E[Check System Preference]

    E --> F{prefers-color-scheme}
    F -->|dark| D
    F -->|light| C

    C --> G[Apply Theme]
    D --> G

    style C fill:#fff9c4
    style D fill:#37474f
```

**File:** `frontend/lib/theme-context.tsx`

### 3. Snackbar Store (Zustand)

**Purpose:** Global notification system

```mermaid
graph TD
    A[Component Action] --> B[showSnackbar]
    B --> C[Zustand Store]
    C --> D[Update State]
    D --> E[SnackbarProvider]
    E --> F[Render Snackbar]

    F --> G[Auto-dismiss after 6s]
    G --> H[Close Snackbar]
    H --> C

    style C fill:#4caf50
    style F fill:#2196f3
```

**Store Structure:**

```typescript
interface SnackbarState {
  open: boolean
  message: string
  severity: 'success' | 'error' | 'warning' | 'info'

  showSnackbar: (message: string, severity: string) => void
  hideSnackbar: () => void
}
```

**Usage Pattern:**

```typescript
import { useSnackbar } from '@/components/SnackbarProvider'

function MyComponent() {
  const { showSnackbar } = useSnackbar()

  const handleAction = async () => {
    try {
      await api.call()
      showSnackbar('Success!', 'success')
    } catch (error) {
      showSnackbar('Error occurred', 'error')
    }
  }
}
```

**File:** `frontend/components/SnackbarProvider.tsx`

---

## Local Component State

### State Patterns by Use Case

```mermaid
graph TD
    A[Component State] --> B[Form Data]
    A --> C[UI State]
    A --> D[Fetched Data]
    A --> E[Derived State]

    B --> B1[Controlled Inputs]
    C --> C1[Modals Open/Close]
    C --> C2[Tab Selection]
    C --> C3[Accordion Expanded]

    D --> D1[API Response]
    D --> D2[Loading Flag]
    D --> D3[Error State]

    E --> E1[Filtered Lists]
    E --> E2[Computed Values]

    style B fill:#2196f3
    style C fill:#9c27b0
    style D fill:#4caf50
```

### 1. Form State

```typescript
function LoginForm() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await login(username, password)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <TextField
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      {/* ... */}
    </form>
  )
}
```

### 2. Async Data Fetching

```mermaid
sequenceDiagram
    participant C as Component
    participant S as useState
    participant API as API Call

    C->>S: setLoading(true)
    C->>API: fetchData()

    alt Success
        API-->>C: Data
        C->>S: setData(data)
        C->>S: setLoading(false)
    else Error
        API-->>C: Error
        C->>S: setError(error)
        C->>S: setLoading(false)
    end
```

**Pattern:**

```typescript
function DataComponent() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.getData()
        setData(response.data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])  // Empty deps = run once on mount

  if (loading) return <CircularProgress />
  if (error) return <Alert severity="error">{error}</Alert>

  return <DataList data={data} />
}
```

### 3. Modal State

```typescript
function ComponentWithModal() {
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState(null)

  const handleOpenModal = (item) => {
    setSelectedItem(item)
    setModalOpen(true)
  }

  const handleCloseModal = () => {
    setModalOpen(false)
    setSelectedItem(null)
  }

  return (
    <>
      <Button onClick={() => handleOpenModal(item)}>
        Edit
      </Button>

      <Modal open={modalOpen} onClose={handleCloseModal}>
        <EditForm item={selectedItem} />
      </Modal>
    </>
  )
}
```

### 4. Derived State

```typescript
function FilteredList() {
  const [items, setItems] = useState([])
  const [searchQuery, setSearchQuery] = useState('')

  // Derived state - computed from other state
  const filteredItems = useMemo(() => {
    return items.filter(item =>
      item.name.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }, [items, searchQuery])

  return (
    <>
      <TextField
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search..."
      />

      <List>
        {filteredItems.map(item => (
          <ListItem key={item.id}>{item.name}</ListItem>
        ))}
      </List>
    </>
  )
}
```

---

## Data Flow Patterns

### Pattern 1: Top-Down Data Flow

```mermaid
graph TD
    A[Parent Component] --> B[Fetch Data]
    B --> C[Store in State]
    C --> D[Pass as Props]
    D --> E[Child Component 1]
    D --> F[Child Component 2]

    E --> G[Display Data]
    F --> H[Display Data]

    style A fill:#2196f3
    style C fill:#4caf50
```

**Example:**

```typescript
// Parent
function DashboardPage() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetchStats().then(setStats)
  }, [])

  return (
    <>
      <StatsCard data={stats} />
      <ChartComponent data={stats} />
    </>
  )
}

// Children
function StatsCard({ data }) {
  return <Card>{data?.total}</Card>
}
```

### Pattern 2: Callback Props for Updates

```mermaid
sequenceDiagram
    participant P as Parent
    participant C as Child

    P->>C: Pass callback as prop
    C->>C: User interaction
    C->>P: Call callback(data)
    P->>P: Update state
    P->>C: Re-render with new props
```

**Example:**

```typescript
// Parent
function ParentComponent() {
  const [items, setItems] = useState([])

  const handleAddItem = (newItem) => {
    setItems([...items, newItem])
  }

  return (
    <ChildForm onAdd={handleAddItem} />
  )
}

// Child
function ChildForm({ onAdd }) {
  const [input, setInput] = useState('')

  const handleSubmit = () => {
    onAdd(input)
    setInput('')
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={input} onChange={e => setInput(e.target.value)} />
      <button type="submit">Add</button>
    </form>
  )
}
```

### Pattern 3: Optimistic Updates

```mermaid
sequenceDiagram
    participant U as User
    participant C as Component
    participant S as State
    participant API as API

    U->>C: Performs action
    C->>S: Update immediately (optimistic)
    C->>U: Show updated UI

    C->>API: Send request

    alt Success
        API-->>C: Confirmation
        C->>C: Keep optimistic update
    else Failure
        API-->>C: Error
        C->>S: Revert update
        C->>U: Show error + old state
    end
```

**Example:**

```typescript
function ChatInterface() {
  const [messages, setMessages] = useState([])

  const sendMessage = async (text) => {
    // Optimistic update
    const tempMessage = {
      id: 'temp-' + Date.now(),
      text,
      timestamp: new Date(),
      status: 'sending'
    }

    setMessages([...messages, tempMessage])

    try {
      const response = await api.sendMessage(text)

      // Replace temp with real message
      setMessages(prev =>
        prev.map(msg =>
          msg.id === tempMessage.id ? response.data : msg
        )
      )
    } catch (error) {
      // Remove failed message
      setMessages(prev =>
        prev.filter(msg => msg.id !== tempMessage.id)
      )
      showSnackbar('Failed to send', 'error')
    }
  }
}
```

### Pattern 4: Lifting State Up

```mermaid
graph TD
    A[Sibling 1 needs data] --> C[Lift to Parent]
    B[Sibling 2 needs data] --> C

    C --> D[Parent owns state]
    D --> E[Pass to Sibling 1]
    D --> F[Pass to Sibling 2]

    style C fill:#ff9800
    style D fill:#2196f3
```

**Example:**

```typescript
// Before: State in one sibling
function Sibling1() {
  const [count, setCount] = useState(0)
  return <div>{count}</div>
}

function Sibling2() {
  // Can't access count from Sibling1!
}

// After: Lift state to parent
function Parent() {
  const [count, setCount] = useState(0)

  return (
    <>
      <Sibling1 count={count} setCount={setCount} />
      <Sibling2 count={count} />
    </>
  )
}
```

---

## Best Practices

### ✅ Do's

1. **Keep state as local as possible**
```typescript
// ✅ Good: State only where needed
function SearchBar() {
  const [query, setQuery] = useState('')
  // ...
}

// ❌ Bad: Lifting unnecessarily
function App() {
  const [searchQuery, setSearchQuery] = useState('')  // Not used by other components!
}
```

2. **Use context for truly global state**
```typescript
// ✅ Good: Auth needed everywhere
<AuthProvider>
  <App />
</AuthProvider>

// ❌ Bad: Context for component-specific state
<FormDataProvider>  // Only one form uses this
  <SingleForm />
</FormDataProvider>
```

3. **Colocate state with usage**
```typescript
// ✅ Good
function DocumentPage() {
  const [documents, setDocuments] = useState([])
  const [filter, setFilter] = useState('')
  // Both used only in this component
}
```

4. **Use derived state instead of duplicating**
```typescript
// ✅ Good: Compute on render
const filteredItems = items.filter(i => i.active)

// ❌ Bad: Duplicate state
const [items, setItems] = useState([])
const [filteredItems, setFilteredItems] = useState([])
// Now must keep in sync!
```

5. **Cleanup effects**
```typescript
// ✅ Good
useEffect(() => {
  const controller = new AbortController()
  fetchData(controller.signal)

  return () => controller.abort()  // Cleanup!
}, [])
```

### ❌ Don'ts

1. **Don't mutate state directly**
```typescript
// ❌ Bad
state.items.push(newItem)
setState(state)

// ✅ Good
setState({ ...state, items: [...state.items, newItem] })
```

2. **Don't depend on previous state incorrectly**
```typescript
// ❌ Bad
setCount(count + 1)
setCount(count + 1)  // Both use same 'count' value!

// ✅ Good
setCount(prev => prev + 1)
setCount(prev => prev + 1)  // Uses updated value
```

3. **Don't forget dependency arrays**
```typescript
// ❌ Bad
useEffect(() => {
  fetchData(id)  // 'id' is a dependency!
})  // Missing deps array

// ✅ Good
useEffect(() => {
  fetchData(id)
}, [id])
```

4. **Don't over-contextualize**
```typescript
// ❌ Bad: Everything in context
<UserContext>
  <ThemeContext>
    <NotificationContext>
      <ModalContext>
        <FormContext>
          {/* Context hell */}
        </FormContext>
      </ModalContext>
    </NotificationContext>
  </ThemeContext>
</UserContext>

// ✅ Good: Only essential global state
<AuthProvider>
  <ThemeProvider>
    {/* Everything else is local */}
  </ThemeProvider>
</AuthProvider>
```

---

## State Management Decision Tree

```mermaid
flowchart TD
    A[Need to manage state] --> B{Used by multiple<br/>unrelated components?}

    B -->|Yes| C{Related to auth<br/>or theme?}
    B -->|No| D{Parent-child<br/>relationship?}

    C -->|Yes| E[Use Context Provider]
    C -->|No| F{Simple notification?}

    F -->|Yes| G[Use Zustand Snackbar]
    F -->|No| H[Consider Context]

    D -->|Yes| I[Lift to common parent]
    D -->|No| J[Local useState]

    E --> K[Global State]
    G --> K
    H --> K
    I --> L[Props Drilling]
    J --> M[Component State]

    style E fill:#ff9800
    style J fill:#2196f3
    style G fill:#4caf50
```

---

## Next Steps

- **[Components Guide](./COMPONENTS.md)** - Learn about reusable components
- **[API Integration](./API_INTEGRATION.md)** - Understand server state management
- **[Development Guide](./DEVELOPMENT_GUIDE.md)** - Apply these patterns in practice

---

**Last Updated:** December 4, 2025
