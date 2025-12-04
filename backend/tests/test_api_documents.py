"""
Tests for document endpoints
"""
import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from unittest.mock import patch, MagicMock


class TestDocumentEndpoints:
    """Test document API endpoints"""

    def test_list_user_documents(self, client: TestClient, auth_headers):
        """Test listing user documents"""
        response = client.get("/api/v1/documents/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_global_documents(self, client: TestClient, admin_headers):
        """Test listing global documents as admin"""
        response = client.get("/api/v1/documents/global", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch('app.rag.document_processor.DocumentProcessor.process_document')
    @patch('app.services.vector_store.vector_store_service.add_document')
    def test_upload_document(self, mock_vector, mock_process, client: TestClient, auth_headers):
        """Test uploading a document"""
        # Mock document processing
        mock_process.return_value = {
            "chunks": [
                {"text": "Test chunk 1", "metadata": {"page": 1}},
                {"text": "Test chunk 2", "metadata": {"page": 2}}
            ]
        }
        mock_vector.return_value = None

        # Create test file
        file_content = b"Test document content"
        file = ("test.txt", BytesIO(file_content), "text/plain")

        response = client.post(
            "/api/v1/documents/upload",
            headers=auth_headers,
            files={"file": file},
            data={"provider": "custom"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["filename"] == "test.txt"

    @patch('app.rag.document_processor.DocumentProcessor.process_document')
    @patch('app.services.vector_store.vector_store_service.add_document')
    def test_upload_global_document(self, mock_vector, mock_process, client: TestClient, admin_headers):
        """Test uploading a global document as admin"""
        mock_process.return_value = {
            "chunks": [{"text": "Global chunk", "metadata": {"page": 1}}]
        }
        mock_vector.return_value = None

        file_content = b"Global test content"
        file = ("global.txt", BytesIO(file_content), "text/plain")

        response = client.post(
            "/api/v1/documents/upload/global",
            headers=admin_headers,
            files={"file": file},
            data={"provider": "custom"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["scope"] == "global"

    def test_upload_global_document_as_user(self, client: TestClient, auth_headers):
        """Test uploading global document as regular user (should fail)"""
        file = ("test.txt", BytesIO(b"content"), "text/plain")

        response = client.post(
            "/api/v1/documents/upload/global",
            headers=auth_headers,
            files={"file": file},
            data={"provider": "custom"}
        )
        assert response.status_code == 403

    def test_get_document_by_id(self, client: TestClient, auth_headers, db_session, test_user):
        """Test getting document by ID"""
        from app.database.models import Document, User
        import uuid

        user = db_session.query(User).filter(User.username == "testuser").first()
        doc = Document(
            uuid=str(uuid.uuid4()),
            filename="test.txt",
            content_type="text/plain",
            file_size=100,
            user_id=user.id,
            scope="user"
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        response = client.get(f"/api/v1/documents/{doc.uuid}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.txt"

    @patch('app.services.vector_store.vector_store_service.delete_document')
    def test_delete_document(self, mock_delete, client: TestClient, auth_headers, db_session, test_user):
        """Test deleting a document"""
        from app.database.models import Document, User
        import uuid

        user = db_session.query(User).filter(User.username == "testuser").first()
        doc = Document(
            uuid=str(uuid.uuid4()),
            filename="to_delete.txt",
            content_type="text/plain",
            file_size=100,
            user_id=user.id,
            scope="user"
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        mock_delete.return_value = None

        response = client.delete(
            f"/api/v1/documents/{doc.uuid}",
            headers=auth_headers,
            params={"provider": "custom"}
        )
        assert response.status_code == 200

    def test_document_requires_authentication(self, client: TestClient):
        """Test that document endpoints require authentication"""
        response = client.get("/api/v1/documents/")
        assert response.status_code == 401
