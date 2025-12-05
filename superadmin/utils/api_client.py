"""
API Client for Streamlit Application
Handles all API communications with FastAPI backend
"""
import requests
import streamlit as st
from typing import Optional, Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backend configuration
BASE_URL = "http://localhost:8000/api/v1"


class APIClient:
    """Client for interacting with FastAPI backend"""

    def __init__(self):
        self.base_url = BASE_URL
        self.timeout = 30

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        headers = {"Content-Type": "application/json"}
        if hasattr(st.session_state, 'token') and st.session_state.token:
            headers["Authorization"] = f"Bearer {st.session_state.token}"
        return headers

    def _handle_response(self, response: requests.Response) -> Optional[Dict[str, Any]]:
        """Handle API response and errors"""
        if response.status_code == 401:
            # Clear session on unauthorized
            if hasattr(st.session_state, 'token'):
                st.session_state.token = None
                st.session_state.authenticated = False
            logger.warning("Session expired - 401 Unauthorized")
            st.error("Session expired. Please login again.")
            st.rerun()
            return None

        if response.status_code == 403:
            st.error("Access denied. You don't have permission for this action.")
            return None

        if response.status_code >= 400:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', response.text)
            except:
                error_detail = response.text

            logger.error(f"API Error {response.status_code}: {error_detail}")
            st.error(f"API Error: {error_detail}")
            return None

        try:
            return response.json()
        except:
            return {"success": True}

    def make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request to backend"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        # Remove Content-Type for file uploads
        if files:
            headers.pop("Content-Type", None)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if not files else None,
                params=params,
                files=files,
                timeout=self.timeout
            )
            return self._handle_response(response)
        except requests.exceptions.ConnectionError:
            st.error(f"Cannot connect to backend at {self.base_url}. Please ensure the backend is running.")
            logger.error(f"Connection error to {url}")
            return None
        except requests.exceptions.Timeout:
            st.error("Request timed out. Please try again.")
            logger.error(f"Timeout for {url}")
            return None
        except Exception as e:
            st.error(f"Request failed: {str(e)}")
            logger.error(f"Request error: {str(e)}")
            return None

    # Authentication endpoints
    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Login to get access token"""
        data = {"username": username, "password": password}
        return self.make_request("/auth/login", method="POST", data=data)

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user information"""
        return self.make_request("/auth/me")

    # Admin endpoints
    def get_all_users(self) -> Optional[List[Dict[str, Any]]]:
        """Get all users (admin only)"""
        return self.make_request("/admin/users")

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID (admin only)"""
        return self.make_request(f"/admin/users/{user_id}")

    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new user (admin only)"""
        return self.make_request("/admin/users", method="POST", data=user_data)

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user (admin only)"""
        return self.make_request(f"/admin/users/{user_id}", method="PUT", data=user_data)

    def delete_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Delete user (admin only)"""
        return self.make_request(f"/admin/users/{user_id}", method="DELETE")

    def get_roles(self) -> Optional[List[Dict[str, Any]]]:
        """Get all roles (admin only)"""
        return self.make_request("/admin/roles")

    def get_system_stats(self) -> Optional[Dict[str, Any]]:
        """Get system statistics (admin only)"""
        return self.make_request("/admin/stats")

    def get_llm_config(self) -> Optional[Dict[str, Any]]:
        """Get LLM configuration (admin only)"""
        return self.make_request("/admin/llm-config")

    # Metering endpoints
    def get_my_token_usage(self) -> Optional[Dict[str, Any]]:
        """Get current user's token usage"""
        return self.make_request("/metering/usage")

    def get_user_token_usage(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get specific user's token usage (admin only)"""
        return self.make_request(f"/metering/usage/{user_id}")

    def get_overall_usage(self) -> Optional[Dict[str, Any]]:
        """Get system-wide token usage (admin only)"""
        return self.make_request("/metering/overall")

    def get_cost_breakdown(self) -> Optional[Dict[str, Any]]:
        """Get cost breakdown by provider/model (admin only)"""
        return self.make_request("/metering/costs")

    def get_usage_history(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> Optional[List[Dict[str, Any]]]:
        """Get usage history"""
        params = {"limit": limit}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.make_request("/metering/history", params=params)

    # Document endpoints
    def get_documents(self, scope: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get documents"""
        params = {"scope": scope} if scope else None
        return self.make_request("/documents/", params=params)

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document details"""
        return self.make_request(f"/documents/{document_id}")

    def delete_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Delete document"""
        return self.make_request(f"/documents/{document_id}", method="DELETE")

    def upload_document_global(
        self,
        file,
        provider: str = "custom",
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Upload document to global knowledge base (admin only)"""
        files = {"file": file}
        data = {"provider": provider}
        if title:
            data["title"] = title
        if description:
            data["description"] = description
        if category:
            data["category"] = category

        # For multipart/form-data, we need to send data as params
        return self.make_request("/documents/upload/global", method="POST", files=files, params=data)

    # Agent endpoints
    def get_agent_status(self) -> Optional[Dict[str, Any]]:
        """Get agent system status"""
        return self.make_request("/agents/status")

    def get_agent_logs(self, limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """Get recent agent logs"""
        return self.make_request("/agents/logs", params={"limit": limit})

    # Conversation endpoints
    def get_conversations(self) -> Optional[List[Dict[str, Any]]]:
        """Get user's conversations"""
        return self.make_request("/chat/conversations")

    def get_conversation_messages(self, conversation_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get messages in conversation"""
        return self.make_request(f"/chat/conversations/{conversation_id}/messages")

    # Prompts endpoints
    def get_prompts(self, category: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get all prompts with optional category filter (admin only)"""
        params = {"category": category} if category else None
        return self.make_request("/prompts", params=params)

    def get_prompt(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific prompt details (admin only)"""
        return self.make_request(f"/prompts/{name}")

    def get_prompt_categories(self) -> Optional[Dict[str, Any]]:
        """Get all prompt categories (admin only)"""
        return self.make_request("/prompts/categories")

    def get_prompt_stats(self) -> Optional[Dict[str, Any]]:
        """Get prompt usage statistics (admin only)"""
        return self.make_request("/prompts/stats")

    def create_prompt(self, prompt_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create custom prompt (admin only)"""
        return self.make_request("/prompts", method="POST", data=prompt_data)

    def update_prompt(self, name: str, prompt_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update custom prompt (admin only)"""
        return self.make_request(f"/prompts/{name}", method="PUT", data=prompt_data)

    def delete_prompt(self, name: str) -> Optional[Dict[str, Any]]:
        """Delete custom prompt (admin only)"""
        return self.make_request(f"/prompts/{name}", method="DELETE")

    def test_prompt(self, name: str, variables: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Test prompt with variables (admin only)"""
        return self.make_request(f"/prompts/{name}/test", method="POST", data={"variables": variables})


# Singleton instance
api_client = APIClient()
