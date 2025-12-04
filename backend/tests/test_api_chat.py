"""
Tests for chat endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestChatEndpoints:
    """Test chat API endpoints"""

    def test_list_conversations(self, client: TestClient, auth_headers):
        """Test listing user conversations"""
        response = client.get("/api/v1/chat/conversations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_conversation(self, client: TestClient, auth_headers):
        """Test creating new conversation"""
        response = client.post(
            "/api/v1/chat/conversations",
            headers=auth_headers,
            json={"title": "Test Conversation"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Conversation"
        assert "id" in data

    def test_get_conversation_history(self, client: TestClient, auth_headers, db_session, test_user):
        """Test getting conversation history"""
        # Create a conversation first
        from app.database.models import Conversation, User
        user = db_session.query(User).filter(User.username == "testuser").first()
        conv = Conversation(title="Test Conv", user_id=user.id)
        db_session.add(conv)
        db_session.commit()
        db_session.refresh(conv)

        response = client.get(f"/api/v1/chat/conversations/{conv.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data

    @patch('app.agents.orchestrator.orchestrator.process_query')
    def test_send_message(self, mock_process, client: TestClient, auth_headers, db_session, test_user):
        """Test sending message in conversation"""
        # Create a conversation
        from app.database.models import Conversation, User
        user = db_session.query(User).filter(User.username == "testuser").first()
        conv = Conversation(title="Test", user_id=user.id)
        db_session.add(conv)
        db_session.commit()
        db_session.refresh(conv)

        # Mock orchestrator response
        mock_process.return_value = {
            "response": "Test response",
            "agent": "research",
            "sources": [],
            "confidence_score": 0.85,
            "token_usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }

        response = client.post(
            f"/api/v1/chat/conversations/{conv.id}/messages",
            headers=auth_headers,
            json={
                "content": "Test question",
                "provider": "custom",
                "selected_document_ids": []
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_message" in data
        assert "assistant_message" in data

    def test_send_message_nonexistent_conversation(self, client: TestClient, auth_headers):
        """Test sending message to nonexistent conversation"""
        response = client.post(
            "/api/v1/chat/conversations/99999/messages",
            headers=auth_headers,
            json={
                "content": "Test question",
                "provider": "custom"
            }
        )
        assert response.status_code == 404
    def test_delete_conversation(self, client: TestClient, auth_headers, db_session, test_user):
        """Test deleting conversation"""
        from app.database.models import Conversation, User
        user = db_session.query(User).filter(User.username == "testuser").first()
        conv = Conversation(title="To Delete", user_id=user.id)
        db_session.add(conv)
        db_session.commit()
        db_session.refresh(conv)
        db_session.refresh(conv)

        response = client.delete(
            f"/api/v1/chat/conversations/{conv.id}",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_chat_requires_authentication(self, client: TestClient):
        """Test that chat endpoints require authentication"""
        response = client.get("/api/v1/chat/conversations")
        assert response.status_code == 401
