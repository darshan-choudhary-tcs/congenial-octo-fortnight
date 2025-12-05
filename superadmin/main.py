"""
Streamlit Admin Application
Main entry point for the admin dashboard
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import pages
from pages.login import show_login_page
from pages.dashboard import show_dashboard_page
from pages.llm_config import show_llm_config_page


# Page configuration
st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="🎛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Load custom CSS
try:
    with open("static/custom.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass  # CSS file optional

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    div[data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_roles' not in st.session_state:
    st.session_state.user_roles = []
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False


def logout():
    """Clear session and logout"""
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user_info = None
    st.session_state.username = None
    st.session_state.user_roles = []
    st.session_state.is_admin = False
    st.rerun()


def main():
    """Main application logic"""

    # Check authentication
    if not st.session_state.authenticated:
        show_login_page()
        return

    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🎛️ Admin Dashboard")
        st.markdown("---")

        # User info
        st.markdown(f"👤 **User:** {st.session_state.username}")
        if st.session_state.user_roles:
            roles_str = ", ".join(st.session_state.user_roles)
            st.markdown(f"🎭 **Roles:** {roles_str}")

        st.markdown("---")

        # Navigation menu
        st.markdown("### 📑 Navigation")

        page = st.radio(
            "Select Page",
            ["Dashboard", "LLM Configuration", "User Management", "Documents", "Token Analytics"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout()

        # Footer
        st.markdown("---")
        st.caption("🔗 Backend: http://localhost:8000")
        st.caption("📊 Admin Panel v1.0")

    # Main content area
    if page == "Dashboard":
        show_dashboard_page()

    elif page == "LLM Configuration":
        show_llm_config_page()

    elif page == "User Management":
        st.title("👥 User Management")
        st.info("🚧 User Management page coming soon!")
        st.markdown("""
        **Planned Features:**
        - View all users with roles and permissions
        - Create new users
        - Edit user details and roles
        - Deactivate/activate users
        - Reset user passwords
        - View user activity and token usage
        """)

    elif page == "Documents":
        st.title("📄 Document Management")
        st.info("🚧 Document Management page coming soon!")
        st.markdown("""
        **Planned Features:**
        - View all documents (user and global)
        - Upload documents to global knowledge base
        - View document metadata and processing status
        - Delete documents
        - Reprocess failed documents
        - View document analytics
        """)

    elif page == "Token Analytics":
        st.title("💰 Token Usage Analytics")
        st.info("🚧 Token Analytics page coming soon!")
        st.markdown("""
        **Planned Features:**
        - Detailed cost breakdown by provider/model
        - Usage trends over time (charts)
        - Per-user token usage comparison
        - Cost projections and budgets
        - Export usage reports
        - Set usage alerts and limits
        """)


if __name__ == "__main__":
    main()
