# RAG & Multi-Agent Frontend

## 📚 Complete Documentation Available!

**For comprehensive documentation with visual diagrams, architecture guides, and development tutorials, see:**

👉 **[DOCUMENTATION.md](./DOCUMENTATION.md)** - Start here for complete frontend documentation

### Quick Links

| Documentation | Description |
|---------------|-------------|
| **[Main Documentation](./DOCUMENTATION.md)** | Complete overview, tech stack, quick start |
| **[Authentication Guide](./docs/guides/AUTHENTICATION.md)** | Login flow, permissions, security |
| **[API Integration](./docs/guides/API_INTEGRATION.md)** | HTTP client, error handling, streaming |
| **[Theming & Styling](./docs/guides/THEMING_STYLING.md)** | MUI theme, dark mode, responsive design |
| **[State Management](./docs/guides/STATE_MANAGEMENT.md)** | Context, hooks, data flow patterns |
| **[Components & Utilities](./docs/guides/COMPONENTS_UTILITIES.md)** | Reusable components, helper functions |
| **[Development Guide](./docs/guides/DEVELOPMENT_GUIDE.md)** | Add features, forms, API endpoints |
| **[Architecture Patterns](./docs/ARCHITECTURE_PATTERNS.md)** | Design patterns, best practices |
| **[Chat Feature](./docs/features/CHAT.md)** | Streaming, agents, document context |
| **[Features Overview](./docs/features/FEATURES_OVERVIEW.md)** | All features documentation |

---

## Overview
This is the Next.js 14 frontend for the RAG & Multi-Agent AI system. It provides a modern, responsive UI for interacting with the AI system, managing documents, viewing explainability insights, and administering users.

## Features

### 🤖 Chat Interface
- Real-time conversational AI with RAG support
- Multi-agent orchestration (Research, Analyzer, Explainability, Grounding agents)
- Source citations with similarity scores
- Confidence indicators for each response
- LLM provider selection (Custom API / Ollama)
- Document upload during chat
- Conversation history management

### 📄 Document Management
- Upload documents (PDF, TXT, CSV, DOCX)
- Automatic processing and vectorization
- Document status tracking
- Provider-specific vector storage
- Document deletion with cleanup

### 📊 Explainability Dashboard
- **AI Insights**: Query history with confidence scores
- **Confidence Analysis**: Trend visualization across queries
- **Agent Performance**: Execution metrics and success rates
- **Reasoning Chains**: Step-by-step AI decision visualization
- Source attribution and grounding evidence
- Interactive charts and graphs

### 👥 Admin Panel (Admin Role Only)
- User management (create, edit, delete)
- Role and permission assignment
- System statistics and metrics
- Performance monitoring
- Active user tracking

## Technology Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI (shadcn/ui)
- **Charts**: Recharts
- **HTTP Client**: Axios
- **Markdown**: react-markdown

## Project Structure

```
frontend/
├── app/
│   ├── auth/
│   │   ├── login/page.tsx          # Login page
│   │   └── register/page.tsx       # Registration page
│   ├── dashboard/
│   │   ├── page.tsx                # Dashboard home
│   │   ├── layout.tsx              # Protected layout
│   │   ├── chat/page.tsx           # Chat interface
│   │   ├── documents/page.tsx      # Document management
│   │   ├── explainability/page.tsx # Explainability dashboard
│   │   └── admin/page.tsx          # Admin panel
│   ├── layout.tsx                  # Root layout
│   ├── page.tsx                    # Home (redirects to login)
│   └── globals.css                 # Global styles
├── components/
│   └── ui/                         # Reusable UI components
│       ├── button.tsx
│       ├── card.tsx
│       ├── input.tsx
│       ├── label.tsx
│       ├── badge.tsx
│       ├── select.tsx
│       ├── tabs.tsx
│       ├── accordion.tsx
│       ├── scroll-area.tsx
│       ├── separator.tsx
│       └── toast.tsx
├── lib/
│   ├── api.ts                      # API client with all endpoints
│   ├── auth-context.tsx            # Authentication context
│   └── utils.ts                    # Utility functions
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## Setup

### Prerequisites
- Node.js 18+
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

3. Run development server:
```bash
npm run dev
```

4. Open http://localhost:3000

## Default Users

Login with these pre-configured accounts:

### Admin (Full Access)
- Username: `admin`
- Password: `admin123`
- Permissions: All features including user management

### Analyst (Read/Write)
- Username: `analyst1`
- Password: `password123`
- Permissions: Chat, documents, agents, explainability

### Viewer (Read Only)
- Username: `viewer1`
- Password: `password123`
- Permissions: View chat, documents, explainability

## Key Components

### API Client (`lib/api.ts`)
Centralized API client with:
- Automatic JWT token injection
- Request/response interceptors
- Error handling with 401 redirect
- Typed API methods for all endpoints

### Auth Context (`lib/auth-context.tsx`)
Global authentication state with:
- User information
- Token management
- Permission checking
- Role verification
- Auto-redirect on logout

### Utility Functions (`lib/utils.ts`)
- `cn()` - Class name merging
- `formatDate()` - Date formatting
- `formatFileSize()` - File size formatting
- `getConfidenceColor()` - Confidence score color coding
- `getConfidenceLabel()` - Confidence score labels

## Features by Route

### `/dashboard/chat`
- Message history with role indicators
- Real-time AI responses
- Source citations in collapsible sections
- Confidence badges
- LLM provider selection
- Document upload button
- Grounding verification toggle
- Conversation sidebar

### `/dashboard/documents`
- Document list with status
- Upload with drag-and-drop
- Processing status indicators
- File size and type display
- Delete functionality
- Stats cards (total, processed, chunks, size)

### `/dashboard/explainability`
- 4 tabs: Insights, Confidence, Agents, Reasoning
- Interactive confidence trend charts
- Agent performance bar charts
- Reasoning chain visualization
- Source and grounding evidence display
- Agent decision logs

### `/dashboard/admin`
- User CRUD operations
- Role assignment
- Permission management
- System statistics
- Performance metrics
- Active user tracking

## Styling

### Theme
- Primary: Blue (#3b82f6)
- Success: Green (#10b981)
- Destructive: Red (#ef4444)
- Gradient background: Blue to Indigo

### Components
All UI components use Radix UI primitives with custom Tailwind styling following the shadcn/ui pattern.

## API Integration

### Authentication Flow
1. Login → Receive JWT token
2. Store token in localStorage
3. Axios interceptor adds token to headers
4. 401 response → Auto redirect to login

### Endpoints Used
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user
- `POST /chat` - Send message
- `GET /chat/conversations` - List conversations
- `POST /documents/upload` - Upload document
- `GET /documents` - List documents
- `GET /explainability/explanations/:id` - Get explanations
- `GET /admin/users` - List users (admin only)
- `POST /admin/users` - Create user (admin only)

## Development

### Adding New Pages
1. Create page in `app/dashboard/[name]/page.tsx`
2. Add route to dashboard navigation
3. Update permissions in `features` array
4. Add API methods if needed

### Adding UI Components
```bash
# Using shadcn CLI
npx shadcn-ui@latest add [component-name]
```

### TypeScript Types
Types are defined inline or imported from API responses. Consider creating a `types/` directory for shared types.

## Build & Deploy

### Production Build
```bash
npm run build
npm start
```

### Environment Variables
- `NEXT_PUBLIC_API_URL` - Backend API URL (required)

## Troubleshooting

### 401 Unauthorized
- Check if backend is running
- Verify token in localStorage
- Check token expiration (default 7 days)

### Connection Refused
- Ensure backend is running on correct port
- Check NEXT_PUBLIC_API_URL in .env.local
- Verify CORS settings in backend

### Components Not Found
- Run `npm install` to ensure all dependencies installed
- Check import paths match file structure

### Styling Issues
- Run `npm run dev` to rebuild Tailwind classes
- Check tailwind.config.ts for correct paths
- Verify globals.css is imported in layout.tsx

## Performance Tips

1. **Code Splitting**: Next.js automatically code-splits pages
2. **Image Optimization**: Use `next/image` for images
3. **API Caching**: Consider React Query or SWR for API caching
4. **Lazy Loading**: Use dynamic imports for heavy components

## Security

- JWT tokens stored in localStorage (consider httpOnly cookies for production)
- CSRF protection via SameSite cookies
- XSS protection via React's built-in escaping
- Input validation on all forms
- Role-based access control enforced on backend

## Future Enhancements

- [ ] Real-time chat with WebSockets
- [ ] Advanced search and filtering
- [ ] Export chat history
- [ ] Dark mode support
- [ ] Mobile responsive improvements
- [ ] Internationalization (i18n)
- [ ] Progressive Web App (PWA)
- [ ] Offline support
