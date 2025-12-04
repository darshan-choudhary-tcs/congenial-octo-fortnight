# Streamlit Admin Application

A comprehensive admin dashboard for managing the RAG & Multi-Agent backend system. Built with Streamlit for easy deployment and intuitive UI.

## 🚀 Features

### ✅ Implemented
- **🔐 Login System**: Secure authentication with hardcoded credentials
- **📊 Dashboard**: Real-time system statistics and metrics
  - User statistics and role distribution
  - Document processing status
  - Conversation analytics
  - Token usage overview (last 30 days)
  - Agent execution performance
  - Recent activity tracking
  - System health monitoring
- **⚙️ LLM Configuration**: Comprehensive configuration management
  - Custom API Provider settings (GenAI Lab)
  - Ollama Provider settings (local)
  - RAG parameters (chunking, retrieval, embeddings)
  - Agent system configuration
  - Explainability settings

### 🚧 Planned Features
- **👥 User Management**: Full CRUD for users, roles, and permissions
- **📄 Document Management**: Upload, view, delete documents; manage global knowledge base
- **💰 Token Analytics**: Detailed usage analytics with charts and cost projections

## 📋 Prerequisites

1. **Backend Running**: Ensure the FastAPI backend is running at `http://localhost:8000`
2. **Database Access**: SQLite database should exist at `../backend/data/data_store.db`
3. **Python 3.8+**: Required for Streamlit

## 🛠️ Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Usage

### Start the Application

```bash
streamlit run streamlit_app.py
```

The application will open in your default browser at `http://localhost:8501`

### Login Credentials

**Admin User (Full Access):**
- Username: `admin`
- Password: `admin123`

**Analyst User (Limited Access):**
- Username: `analyst1`
- Password: `analyst123`

**Viewer User (Read-Only):**
- Username: `viewer1`
- Password: `viewer123`

## 📁 Project Structure

```
.
├── streamlit_app.py              # Main application entry point
├── requirements.txt     # Python dependencies
├── README_STREAMLIT.md           # This file
│
├── pages/
│   ├── login.py                  # Login page
│   ├── dashboard.py              # Dashboard with statistics
│   └── llm_config.py             # LLM configuration management
│
└── utils/
    ├── api_client.py             # Backend API client
    └── db_utils.py               # Direct database access utilities
```

## 🔧 Configuration

### Backend URL
The application connects to the backend at `http://localhost:8000` by default. To change this, edit `utils/api_client.py`:

```python
BASE_URL = "http://your-backend-url:port/api/v1"
```

### Database Path
The application accesses the SQLite database at `backend/data/data_store.db`. To change this, edit `utils/db_utils.py`:

```python
DATABASE_PATH = "path/to/your/database.db"
```

## 📊 Dashboard Features

### System Overview
- **Users**: Total, active, and inactive user counts
- **Documents**: Total documents with global/user scope breakdown
- **Conversations**: Total conversations and message counts
- **Agent Executions**: Total runs with success rate

### Token Usage (Last 30 Days)
- Total tokens consumed
- Estimated costs
- Number of operations
- Active users

### Analytics Tabs
1. **Documents**: Recent uploads, processing status, file types
2. **Agent Logs**: Recent agent executions with performance metrics
3. **Token Usage**: Top users by usage with cost breakdown

### System Health
- Database size monitoring
- Agent success rate
- Average execution time
- Total document chunks

## ⚙️ LLM Configuration

### Custom API Provider
- Base URL and model selection
- API key management (masked display)
- Embedding and vision model configuration
- Pricing settings

### Ollama Provider
- Local Ollama server configuration
- Model selection for chat, embeddings, and vision
- Connection testing

### RAG Settings
- Chunk size and overlap
- Max retrieval documents
- Similarity threshold
- File upload limits
- ChromaDB collection management

### Agent Configuration
- Temperature and creativity settings
- Max iterations
- Memory management
- Explainability levels
- Confidence scoring
- Source attribution

## 🔐 Security Notes

- API keys are masked in the UI
- JWT tokens stored in session state (memory only)
- Session expires on browser close
- Admin-only endpoints protected with role checks
- Direct database access uses read-only queries

## 🐛 Troubleshooting

### Cannot Connect to Backend
- Ensure FastAPI backend is running: `cd backend && python main.py`
- Check backend URL in `utils/api_client.py`
- Verify CORS settings allow Streamlit origin

### Database Connection Failed
- Verify database exists at `backend/data/data_store.db`
- Check database path in `utils/db_utils.py`
- Ensure SQLite file has read permissions

### Session Expired Error
- Re-login with credentials
- Check backend JWT token expiration settings
- Verify backend is running and accessible

### Missing Statistics
- Ensure you're logged in as `admin` for full access
- Check that backend has data (users, documents, conversations)
- Verify database has been initialized with sample data

## 🔄 Integration with Backend

### API Endpoints Used
- `POST /api/v1/auth/login` - Authentication
- `GET /api/v1/auth/me` - Current user info
- `GET /api/v1/admin/stats` - System statistics
- `GET /api/v1/admin/llm-config` - LLM configuration
- `GET /api/v1/metering/overall` - Token usage
- `GET /api/v1/documents/` - Document list
- `GET /api/v1/agents/logs` - Agent execution logs

### Direct Database Queries
The application performs read-only queries for:
- User statistics by role
- Document analytics by type/scope
- Token usage trends and breakdowns
- Agent performance metrics
- Recent activity logs

## 📝 Development Notes

### Adding New Pages
1. Create page file in `pages/` directory
2. Import in `streamlit_app.py`
3. Add to navigation menu
4. Implement page logic with `show_*_page()` function

### API Client Usage
```python
from utils.api_client import api_client

# Get data
result = api_client.get_system_stats()

# Handle response
if result:
    st.write(result)
else:
    st.error("Failed to fetch data")
```

### Database Queries
```python
from utils.db_utils import db_client

# Execute custom query
results = db_client.execute_query(
    "SELECT * FROM users WHERE is_active = :active",
    {"active": 1}
)

# Use helper methods
stats = db_client.get_user_statistics()
```

## 🎨 UI Customization

The application uses Streamlit's theming system. To customize:

1. Create `.streamlit/config.toml` in project root:
```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

## 📦 Dependencies

- **streamlit**: Web application framework
- **requests**: HTTP client for API calls
- **sqlalchemy**: Database ORM and query builder
- **pandas**: Data manipulation and analysis
- **plotly/altair**: Visualization (for future charts)

## 🤝 Contributing

To extend the application:
1. Follow the existing page structure pattern
2. Use `api_client` for backend communication
3. Use `db_client` for database queries
4. Maintain session state for authentication
5. Add appropriate error handling
6. Update this README with new features

## 📄 License

Same as the main project.

## 💡 Tips

- Use `st.rerun()` sparingly to avoid infinite loops
- Cache expensive operations with `@st.cache_data`
- Keep API calls in try-except blocks
- Always check authentication before rendering pages
- Use `with st.spinner()` for loading states
- Leverage `st.columns()` for responsive layouts

---

**Last Updated**: December 5, 2025
**Version**: 1.0.0
